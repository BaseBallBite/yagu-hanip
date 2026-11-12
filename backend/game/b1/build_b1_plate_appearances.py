"""Add traceable plate-appearance groups without replacing B1 row IDs or B2 states."""
import argparse
from collections import Counter
from pathlib import Path
import re
import sys
from b1_pa_source import read, write, file_hash, digest, select_game

VERSION = 'b1-pa-v1.0'
RESULTS = {'single','double','triple','home_run','walk','intentional_walk','hit_by_pitch',
 'strikeout','groundout','flyout','lineout','bunt_out','batted_ball_out','double_play',
 'triple_play','sacrifice_bunt','sacrifice_fly','dropped_third_strike','reached_on_error',
 'fielders_choice','batting_interference','reach_unspecified'}
RUNNERS = {'runner_advance','runner_out','run_scored','steal','caught_stealing','pickoff_out'}
REVIEWS = {'video_review','correction_notice','play_notice'}
HEADER = re.compile(r'^\s*(\d+)번타자\s+(.+?)\s*$')

def group_game(data, selection):
    gid = data['game_id']
    index = {r['play_id']:r for r in data['plays']}
    rows = [index[x] for x in selection['ordered_play_ids']]
    groups, links, loose = [], [], []
    current = None
    half = None

    def start(row, basis, header=None):
        nonlocal current
        current = {'plate_appearance_id':gid+':pa:'+digest({'version':VERSION,'anchor':row['play_id']}),
            'anchor_play_id':row['play_id'], 'inning':row['inning'], 'inning_half':row['inning_half'],
            'start_basis':basis, 'announced_batting_order':header[0] if header else None,
            'announced_batter_names':[header[1]] if header else [],
            'member_play_ids':[], 'pitch_play_ids':[], 'batter_result_play_ids':[],
            'related_runner_play_ids':[], 'review_flags':[], 'last_pitch_number':None,
            'state_before':None,'state_after':None,'official_pa_count_eligible':False,
            'verified_fact_eligible':False}
        if basis != 'batter_announcement':current['review_flags'].append('start_inferred_without_announcement')

    def flag(reason):
        if reason not in current['review_flags']:current['review_flags'].append(reason)

    def close(reason):
        nonlocal current
        if current is None:return
        count = len(current['batter_result_play_ids'])
        if count == 0:flag('no_batter_result_observed')
        if count > 1:flag('multiple_batter_result_rows')
        current['end_boundary'] = reason
        current['group_status'] = 'review_required' if current['review_flags'] else 'source_boundaries_observed'
        current['completion_status'] = 'batter_result_observed' if count else 'completion_unknown'
        current.pop('last_pitch_number')
        groups.append(current)
        current = None

    for row in rows:
        event = row['event_type'];pid=row['play_id']
        new_half = (row['inning'], row['inning_half'])
        if half != new_half:
            close('half_inning_changed');half=new_half
        if event == 'inning_start':
            # Repeated same-half headings are context, not a new PA boundary.
            loose.append(pid);links.append({'play_id':pid,'plate_appearance_id':None,'role':'inning_context'})
            continue
        match = HEADER.match(row['description']) if event == 'batter_announcement' else None
        header = (int(match[1]),match[2]) if match else None
        pinch = re.match(r'^\s*대타\s+(.+?)\s*$',row['description']) if event == 'batter_announcement' else None
        if event == 'batter_announcement':
            if pinch:
                if current is not None and current['batter_result_play_ids']:
                    close('next_pinch_hitter_announcement')
                if current is None:start(row,'pinch_hitter_announcement')
                if pinch[1] not in current['announced_batter_names']:current['announced_batter_names'].append(pinch[1])
                flag('pinch_hitter_context')
            elif current is None:
                start(row,'batter_announcement',header)
            elif current['batter_result_play_ids']:
                close('next_batter_announcement');start(row,'batter_announcement',header)
            elif header and current['announced_batting_order'] == header[0]:
                # Same batting slot may repeat or name a pinch hitter; preserve both names.
                if header[1] not in current['announced_batter_names']:
                    current['announced_batter_names'].append(header[1]);flag('batter_changed_within_group')
            elif header and current['announced_batting_order'] is None:
                # Late announcement does not prove the inferred earlier start belongs to it.
                flag('late_batter_announcement');current['announced_batting_order']=header[0]
                current['announced_batter_names'].append(header[1])
            else:
                flag('announcement_boundary_without_result')
                close('unresolved_next_announcement');start(row,'batter_announcement',header)
                flag('previous_group_boundary_unresolved')
            if header is None and pinch is None:flag('unparsed_batter_announcement')
        elif event == 'pitch':
            number=(row.get('pitch') or {}).get('pitch_number')
            if current is None:start(row,'pitch_without_announcement')
            elif current['batter_result_play_ids']:
                flag('pitch_after_result_boundary_unresolved')
                close('pitch_after_result');start(row,'pitch_after_result')
                flag('previous_group_boundary_unresolved')
            elif number == 1 and current['pitch_play_ids']:
                # Could be a correction/reset; do not invent another PA solely from pitch count.
                flag('pitch_number_reset_without_result')
            last=current['last_pitch_number']
            if isinstance(number,int) and isinstance(last,int) and number <= last:
                flag('pitch_number_not_increasing')
            current['last_pitch_number']=number
        elif event in RESULTS and current is None:
            start(row,'result_without_announcement')

        if current is None:
            loose.append(pid);links.append({'play_id':pid,'plate_appearance_id':None,'role':'unassigned_context_or_runner'})
            continue
        current['member_play_ids'].append(pid)
        role = 'context'
        if event == 'pitch':
            current['pitch_play_ids'].append(pid);role='pitch'
        elif event in RESULTS:
            current['batter_result_play_ids'].append(pid);role='batter_result_candidate'
            subject=row['description'].split(':',1)[0].strip()
            if current['announced_batter_names'] and subject not in current['announced_batter_names']:
                flag('result_subject_differs_from_announced_batter')
            if event in {'reach_unspecified','dropped_third_strike'}:flag('result_semantics_pending')
        elif event in RUNNERS:
            current['related_runner_play_ids'].append(pid);role='related_runner_event'
            # Relation is temporal, not proof that batter caused this event.
            if event in {'runner_out','caught_stealing','pickoff_out'}:flag('runner_out_requires_B2_boundary_check')
        elif event in REVIEWS:
            flag('review_or_correction_in_group');role='notice'
        elif event == 'substitution':
            role='substitution_context'
            if '대타' in row['description']:flag('pinch_hitter_context')
        links.append({'play_id':pid,'plate_appearance_id':current['plate_appearance_id'],'role':role})
    close('selected_game_records_ended')
    membership=[x for g in groups for x in g['member_play_ids']]+loose
    if len(membership)!=len(rows) or len(set(membership))!=len(rows) or set(membership)!={r['play_id'] for r in rows}:
        raise ValueError('row coverage is not one-to-one')
    if [l['play_id'] for l in links]!=selection['ordered_play_ids']:
        raise ValueError('row link order mismatch')
    if len({g['plate_appearance_id'] for g in groups})!=len(groups):raise ValueError('duplicate PA ID')
    for g in groups:
        if any((index[p]['inning'],index[p]['inning_half'])!=(g['inning'],g['inning_half']) for p in g['member_play_ids']):
            raise ValueError('group crosses half innings')
    return {'schema_version':VERSION,'game_id':gid,'groups':groups,'row_links':links,
       'unassigned_play_ids':loose,'grouping_complete':True,'semantic_validation_complete':False,
       'state_reconstruction_complete':False,
       'note':'Source sequence grouping, not official plate-appearance statistics. Runner links are temporal only.'}

def run(normalized, selected, out, expected=720):
    normalized,selected,out=[Path(p).resolve() for p in (normalized,selected,out)]
    if out.exists() or any(out==p or p in out.parents or out in p.parents for p in (normalized,selected)):
        raise ValueError('Choose NEW output folder outside inputs')
    paths=[normalized/'run_report.json',normalized/'game_reports.json',selected/'finish_report.json',selected/'applied_rules.json']
    hashes={str(p):file_hash(p) for p in paths}
    nr,reports,sr,rules=[read(p) for p in paths]
    if nr.get('status')!='STRUCTURAL_PASS' or nr.get('scope')!='full':raise ValueError('normalization not passed')
    if sr.get('status')!='SELECTION_PASS_WITH_LIMITATIONS' or sr.get('processed_games')!=expected or sr.get('expected_games')!=expected or sr.get('errors') or sr.get('interrupted') or sr.get('blocked_games') or sr.get('failed_games'):
        raise ValueError('selection not passed/complete')
    if digest(rules)!=sr['rules_sha256']:raise ValueError('rules changed')
    ids=[r['game_id'] for r in reports]
    if len(ids)!=expected or len(set(ids))!=expected or any(not re.fullmatch('[A-Za-z0-9_-]+',g) for g in ids):raise ValueError('invalid inventory')
    plans={p['game_id']:p for p in rules['games']}
    out.mkdir();write(out/'pa_report.json',{'status':'RUNNING'})
    errors=[];games=[];totals=Counter();flags=Counter();interrupted=False
    try:
        for n,report in enumerate(reports,1):
            gid=report['game_id']
            try:
                src=normalized/'games'/gid/'normalized_game.json';sel=selected/'games'/(gid+'.json')
                sh,th=file_hash(src),file_hash(sel);data,choice=read(src),read(sel)
                if sh!=report['output_sha256'] or sh!=choice['normalized_file_sha256'] or data['game_id']!=gid:raise ValueError('source hash/ID mismatch')
                check=select_game(data,plans.get(gid));check['normalized_file_sha256']=sh
                if check!=choice or check['status']!='SELECTION_CHECKS_PASS':raise ValueError('selection changed')
                result=group_game(data,choice);result.update(normalized_file_sha256=sh,selection_file_sha256=th)
                if file_hash(src)!=sh or file_hash(sel)!=th:raise ValueError('input changed while reading')
                dest=out/'games'/(gid+'.json');write(dest,result)
                if read(dest)!=result:raise ValueError('output read-back mismatch')
                counts=Counter(g['group_status'] for g in result['groups'])
                games.append({'game_id':gid,'groups':len(result['groups']),'review_groups':counts['review_required'],'output_sha256':file_hash(dest)})
                totals.update({'groups':len(result['groups']),'source_boundaries_observed':counts['source_boundaries_observed'],
                    'review_groups':counts['review_required'],'selected_rows':len(result['row_links']),
                    'unassigned_rows':len(result['unassigned_play_ids'])})
                for g in result['groups']:flags.update(g['review_flags'])
                print(f'[{n}/{expected}] {gid}: GROUPED, review={counts["review_required"]}',flush=True)
            except (ValueError,KeyError,TypeError,OSError,AssertionError) as e:
                errors.append({'game_id':gid,'error':str(e)});print(gid+': ERROR '+str(e),flush=True)
                if isinstance(e,OSError) and e.errno==28:break
    except KeyboardInterrupt:interrupted=True
    if totals['selected_rows']!=sr['totals']['retained_rows']:errors.append({'error':'selected row coverage mismatch'})
    changed=[p for p,h in hashes.items() if not Path(p).exists() or file_hash(Path(p))!=h]
    passed=len(games)==expected and not errors and not changed and not interrupted
    final={'schema_version':VERSION,'status':'PA_GROUPING_PASS_WITH_REVIEW' if passed else 'INCOMPLETE',
      'expected_games':expected,'processed_games':len(games),'errors':errors,'changed_control_files':changed,
      'interrupted':interrupted,'totals':dict(totals),'review_flag_counts':dict(flags),
      'semantic_validation_complete':False,'state_reconstruction_complete':False,
      'note':'Grouping coverage passed; flagged boundaries require review/B2. Counts are not official PA totals.'}
    write(out/'game_reports.json',games);write(out/'pa_report.json',final)
    print(__import__('json').dumps(final,ensure_ascii=False,indent=2));return 0 if passed else 1

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--normalized',type=Path,required=True);p.add_argument('--selection',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    try:return run(a.normalized,a.selection,a.out)
    except (ValueError,KeyError,TypeError,OSError) as e:print('STOP: '+str(e),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
