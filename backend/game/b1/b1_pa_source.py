"""Offline B1 selection overlay; never rewrites normalized source files."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

VERSION='b1-selection-v1.0'
ADMIN={'separator','game_result_notice'}
NOTICES={'video_review','correction_notice','play_notice','check_swing_notice','break_notice','abs_notice','ejection_notice','game_status_notice','mound_visit','dugout_visit','pitcher_disengagement'}
CONTEXT={'inning_start','batter_announcement','substitution'}
RESOLVABLE={'seqno_collision_review','source_order_decrease','repeated_pitch_id_review'}

def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def file_hash(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp')
    tmp.write_text(canonical(value),encoding='utf-8');tmp.replace(path)
def sid(game,kind,ref):return game+':'+kind+':'+digest(ref)
def valid_pitch_id(x):return x is not None and str(x) not in ('','-1','0','None')

def select_game(data, plan=None):
    gid=data['game_id']
    if data.get('schema_version')!='b1-row-v1.1':raise ValueError('requires b1-row-v1.1')
    plays=data['plays'];tracks=data['tracking_records']
    if not plays:raise ValueError('empty plays')
    for rows,kind,key in [(plays,'play','play_id'),(tracks,'tracking','tracking_id')]:
        ids=[r[key] for r in rows]
        if len(ids)!=len(set(ids)):raise ValueError('duplicate '+key)
        for r in rows:
            source=r['source_record']
            if source['game_id']!=gid or r[key]!=sid(gid,kind,source['source_ref']):raise ValueError('source identity mismatch')
    for p in plays:
        if p['description']!=p['source_record']['text']:raise ValueError('description mismatch')
        if p.get('pitch') and p['pitch']['pitch_id']!=sid(gid,'pitch',p['source_record']['source_ref']):raise ValueError('pitch identity mismatch')
    refs={p['source_record']['source_ref']:p for p in plays}
    if len(refs)!=len(plays):raise ValueError('duplicate source ref')
    if plan:
        if gid!=plan['game_id']:raise ValueError('plan game mismatch')
        if digest([p['source_record'] for p in plays])!=plan['source_text_sha256']:raise ValueError('reviewed text changed')
        if digest([p['source_record'] for p in tracks])!=plan['source_pitch_sha256']:raise ValueError('reviewed pitches changed')
    actions={}
    for d in (plan or {}).get('decisions',[]):
        ref=d['source_ref']
        if ref not in refs or ref in actions:raise ValueError('invalid decision source')
        target=d['replacement_source_ref']
        if target is not None and (target not in refs or target==ref):raise ValueError('invalid replacement')
        if d['action'] not in {'post_finish_notice','equivalent_event_copy','superseded_in_event_sequence'}:raise ValueError('invalid action')
        actions[ref]=d
    if any(d['replacement_source_ref'] in actions for d in actions.values() if d['replacement_source_ref']):raise ValueError('replacement also excluded')
    excluded=[];ordered=[];events=[];context=[];notices=[];pending=[];blocks=[]
    for p in plays:
        ref=p['source_record']['source_ref'];pid=p['play_id'];event=p['event_type']
        if ref in actions:
            d=actions[ref];target=d['replacement_source_ref']
            excluded.append({'play_id':pid,'action':d['action'],'replacement_play_id':refs[target]['play_id'] if target else None,'reason':d['reason']})
            continue
        if event in ADMIN:
            excluded.append({'play_id':pid,'action':'administrative_only','replacement_play_id':None,'reason':'Display/audit only, never a pitch/out/run accumulation event'})
            continue
        ordered.append(pid)
        if event in CONTEXT:context.append(pid)
        elif event in NOTICES:notices.append(pid)
        else:events.append(pid)
        flags=set(p.get('review_flags',[]))
        if plan:flags-=RESOLVABLE
        if event in {'reach_unspecified','video_review','play_notice','correction_notice'}:flags.add('contextual_semantics_pending')
        if event=='unknown':blocks.append({'play_id':pid,'reason':'unknown_event'})
        if flags:pending.append({'play_id':pid,'event_type':event,'flags':sorted(flags)})
        if flags & RESOLVABLE:blocks.append({'play_id':pid,'reason':'unreviewed_order_or_collision'})
    if data.get('timeline_review_required') and plan is None:blocks.append({'reason':'unreviewed_game_timeline_flag'})
    # Check selected pitch identities and actual source linking; do not accept repeated IDs silently.
    track_index={t['tracking_id']:t for t in tracks};pitch_ids=[];missing=0
    index={p['play_id']:p for p in plays};prev=None
    for pid in ordered:
        p=index[pid];s=p['source_record'];half=p['inning_half'];inn=p['inning']
        if half not in ('top','bottom') or not isinstance(inn,int) or isinstance(inn,bool) or inn<1:raise ValueError('invalid inning/half')
        seq=s.get('seqno')
        try:seq=int(seq)
        except (TypeError,ValueError):raise ValueError('invalid seqno')
        order=(inn,0 if half=='top' else 1,seq)
        if prev is not None and order<prev:blocks.append({'play_id':pid,'reason':'selected_sequence_decreases'})
        prev=order
        pitch=p.get('pitch')
        if pitch:
            source_id=pitch.get('source_pitch_id')
            if valid_pitch_id(source_id):pitch_ids.append(str(source_id))
            status=pitch['tracking_status']
            if status=='source_id_missing':
                if valid_pitch_id(source_id):raise ValueError('false missing pitch id')
                missing+=1
            elif status=='matched':
                tr=track_index.get(pitch['tracking_id'])
                if not tr:raise ValueError('missing tracking reference')
                ts=tr['source_record']
                if not valid_pitch_id(source_id) or str(ts['raw'].get('pitchId'))!=str(source_id):raise ValueError('pitch ID mismatch')
                for k in ['source_file','block_index','inning','half_raw','relay_no']:
                    if s.get(k) is None or str(s[k])!=str(ts.get(k)):raise ValueError('tracking context mismatch: '+k)
            else:blocks.append({'play_id':pid,'reason':'unresolved_tracking_'+status})
    repeats={k:v for k,v in Counter(pitch_ids).items() if v>1}
    if repeats:blocks.append({'reason':'selected_pitch_id_repeats','counts':repeats})
    all_ids={p['play_id'] for p in plays};excluded_ids={p['play_id'] for p in excluded}
    assert not set(ordered)&excluded_ids
    assert set(ordered)|excluded_ids==all_ids
    assert len(ordered)+len(excluded)==len(plays)
    assert set(events)|set(context)|set(notices)==set(ordered)
    assert len(events)+len(context)+len(notices)==len(ordered)
    result={'selection_version':VERSION,'game_id':gid,'source_schema_version':data['schema_version'],'dataset_revision':data.get('dataset_revision'),
       'status':'BLOCKED' if blocks else 'SELECTION_CHECKS_PASS',
       'semantic_review_complete':False,'state_reconstruction_complete':False,
       'ordered_play_ids':ordered,'event_candidate_ids':events,'context_ids':context,'notice_ids':notices,'excluded_from_sequence':excluded,
       'pending_semantics':pending,'blocking_issues':blocks,'rule_applied':plan is not None,
       'field_limitations':(plan or {}).get('warnings',[]),
       'global_limitations':['All before/after states await B2.','No currentPlayersInfo/batterRecord/playerChange metadata is automatically certified for AI facts.','Event candidates are not verified F facts; do not increment outs/runs once per row.'],
       'text_rows_accounted_for':len(plays),'pitch_rows_preserved_in_source':len(tracks),'selected_pitch_rows_with_id':len(pitch_ids),'selected_pitch_id_missing_rows':missing}
    if gid=='20260526LGLT02026' and plan:result['reviewed_played_last_inning']=7
    return result

def run(root,out,rules,expected=720):
    root=root.resolve();out=out.resolve()
    if out.exists() or out==root or root in out.parents or out in root.parents:raise ValueError('Choose NEW output folder outside input tree')
    controls={name:file_hash(root/name) for name in ['run_report.json','game_reports.json']}
    source=read(root/'run_report.json');reports=read(root/'game_reports.json')
    if source.get('scope')!='full' or source.get('status')!='STRUCTURAL_PASS' or source.get('schema_version')!='b1-row-v1.1':raise ValueError('input full normalization not passed')
    for key in ['selected_games','processed_games','normalized_games']:
        if source.get(key)!=expected:raise ValueError('expected count mismatch')
    if source.get('failed_games')!=0:raise ValueError('source contains failures')
    ids=[r['game_id'] for r in reports]
    if len(ids)!=expected or len(set(ids))!=expected or any(not re.fullmatch('[A-Za-z0-9_-]+',g) for g in ids):raise ValueError('invalid game list')
    plan_list=rules['games'];plans={p['game_id']:p for p in plan_list}
    if len(plans)!=len(plan_list):raise ValueError('duplicate rule game')
    if expected==720 and not set(plans).issubset(ids):raise ValueError('reviewed game missing')
    out.mkdir();summary=[];errors=[];totals=Counter();teams=Counter();interrupted=False
    write(out/'finish_report.json',{'status':'RUNNING','selection_version':VERSION})
    try:
        for number,report in enumerate(reports,1):
            gid=report['game_id']
            try:
                path=root/'games'/gid/'normalized_game.json';before=file_hash(path)
                if before!=report.get('output_sha256'):raise ValueError('normalized file differs from recorded hash')
                data=read(path)
                if data.get('game_id')!=gid:raise ValueError('game mismatch')
                if len(data['plays'])!=report['text_rows_output'] or len(data['tracking_records'])!=report['pitch_rows_output']:raise ValueError('source report row mismatch')
                if expected==720:
                    m=data.get('metadata_raw') or {};a=m.get('awayTeamCode');h=m.get('homeTeamCode')
                    if a==h or a not in {'HT','SK','KT','LG','LT','SS','OB','NC','WO','HH'} or h not in {'HT','SK','KT','LG','LT','SS','OB','NC','WO','HH'}:raise ValueError('invalid teams')
                    teams.update([a,h])
                selection=select_game(data,plans.get(gid));selection['normalized_file_sha256']=before
                if file_hash(path)!=before:raise ValueError('input changed during read')
                write(out/'games'/(gid+'.json'),selection)
                disk=read(out/'games'/(gid+'.json'))
                if disk!=selection:raise ValueError('output round-trip mismatch')
                summary.append({'game_id':gid,'status':selection['status'],'retained_rows':len(selection['ordered_play_ids']),'excluded_rows':len(selection['excluded_from_sequence']),'pending_semantics':len(selection['pending_semantics']),'blocking_issues':selection['blocking_issues']})
                totals['text_rows']+=len(data['plays']);totals['pitch_rows']+=len(data['tracking_records'])
                totals['retained_rows']+=len(selection['ordered_play_ids']);totals['excluded_rows']+=len(selection['excluded_from_sequence'])
                totals['selected_pitch_rows_with_id']+=selection['selected_pitch_rows_with_id'];totals['selected_pitch_id_missing_rows']+=selection['selected_pitch_id_missing_rows']
                totals['pending_semantic_rows']+=len(selection['pending_semantics'])
                print(f'[{number}/{expected}] {gid}: {selection["status"]}',flush=True)
            except (ValueError,KeyError,TypeError,OSError,AssertionError) as e:
                errors.append({'game_id':gid,'error':str(e)});print(gid+': ERROR '+str(e),flush=True)
                if isinstance(e,OSError) and e.errno==28:break
    except KeyboardInterrupt:interrupted=True
    changed=[name for name,h in controls.items() if not (root/name).exists() or file_hash(root/name)!=h]
    if totals['text_rows']!=source['text_rows_preserved'] or totals['pitch_rows']!=source['pitch_rows_preserved']:errors.append({'error':'total source coverage mismatch'})
    if expected==720 and (len(teams)!=10 or any(v!=144 for v in teams.values())):errors.append({'error':'team coverage mismatch'})
    blocked=sum(r['status']=='BLOCKED' for r in summary)
    passed=len(summary)==expected and not errors and not blocked and not changed and not interrupted
    final={'selection_version':VERSION,'scope':'full','status':'SELECTION_PASS_WITH_LIMITATIONS' if passed else 'INCOMPLETE',
        'expected_games':expected,'processed_games':len(summary),'failed_games':sum('game_id'in e for e in errors),'blocked_games':blocked,
        'totals':dict(totals),'rules_sha256':digest(rules),'changed_control_files':changed,'errors':errors,'interrupted':interrupted,
        'semantic_review_complete':False,'state_reconstruction_complete':False,
        'note':'Pass covers source integrity and reviewed sequence selection only. B2 and contextual semantic validation remain required.'}
    write(out/'game_status.json',summary);write(out/'applied_rules.json',rules);write(out/'finish_report.json',final)
    print(json.dumps(final,ensure_ascii=False,indent=2));return 0 if passed else 1

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    try:return run(a.input,a.out,read(Path(__file__).with_name('selection_rules.json')))
    except (OSError,ValueError,KeyError,TypeError) as e:print('STOP: '+str(e),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
