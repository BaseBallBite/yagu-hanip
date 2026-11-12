"""Offline B1 delivery contract. Source records are not independently verified facts."""
import argparse
from collections import Counter
from pathlib import Path
import re
import sys
from b1_selection_core import read, write, file_hash, select_game, digest

VERSION = 'b1-handoff-v1.0'
CONTEXT = {'inning_start', 'batter_announcement', 'substitution'}
NOTICES = {'video_review', 'correction_notice', 'play_notice', 'check_swing_notice',
           'break_notice', 'abs_notice', 'ejection_notice', 'game_status_notice',
           'mound_visit', 'dugout_visit', 'pitcher_disengagement'}
EVENTS = {'pitch', 'runner_advance', 'strikeout', 'flyout', 'single', 'groundout',
          'run_scored', 'walk', 'runner_out', 'double', 'steal', 'lineout', 'double_play',
          'home_run', 'dropped_third_strike', 'reached_on_error', 'hit_by_pitch',
          'sacrifice_bunt', 'caught_stealing', 'sacrifice_fly', 'intentional_walk',
          'triple', 'pickoff_out', 'bunt_out', 'triple_play', 'fielders_choice',
          'batting_interference', 'batted_ball_out', 'reach_unspecified'}

def policy(event, flags):
    if event not in CONTEXT | NOTICES | EVENTS:
        raise ValueError('No policy for event_type: ' + str(event))
    category = 'context' if event in CONTEXT else 'notice' if event in NOTICES else 'event'
    if event == 'reach_unspecified':
        disposition = 'unresolved_reach_reason'
    elif event in {'video_review', 'correction_notice', 'play_notice'}:
        disposition = 'context_review_required'
    elif flags:
        disposition = 'flagged_source_record'
    elif category != 'event':
        disposition = 'context_only'
    else:
        disposition = 'source_text_only'
    return {'category': category, 'disposition': disposition,
            'can_display_source_text': True, 'can_use_as_verified_fact': False,
            'can_accumulate_outs_or_runs': False}

def build_game(data, selection):
    index = {p['play_id']: p for p in data['plays']}
    pending = {p['play_id']: p['flags'] for p in selection['pending_semantics']}
    records = []
    for order, pid in enumerate(selection['ordered_play_ids'], 1):
        p = index[pid]
        flags = pending.get(pid, [])
        use = policy(p['event_type'], flags)
        # Explicit excerpts are source claims, never certified reconstructed state.
        records.append({'play_id': pid, 'display_order': order,
            'record_unit': 'source_text_row', 'plate_appearance_id': None,
            'inning': p['inning'], 'inning_half': p['inning_half'],
            'description': p['description'], 'event_type': p['event_type'],
            'source_tags': p.get('event_tags', []), 'usage': use,
            'review_flags': flags, 'source_ref': p['source_record']['source_ref'],
            'actor_player_id': None, 'state_before': None, 'state_after': None,
            'pitch_id': (p.get('pitch') or {}).get('pitch_id'),
            'tracking_status': (p.get('pitch') or {}).get('tracking_status')})
    ids = [r['play_id'] for r in records]
    if len(set(ids)) != len(ids) or ids != selection['ordered_play_ids']:
        raise ValueError('selected record identity/order mismatch')
    return {'schema_version': VERSION, 'game_id': data['game_id'],
            'record_unit': 'source_text_row', 'plate_appearance_grouping_complete': False,
            'state_reconstruction_complete': False, 'semantic_review_complete': False,
            'records': records, 'field_limitations': selection['field_limitations'],
            'global_limitations': selection['global_limitations'],
            'excluded_records': selection['excluded_from_sequence']}

def run(normalized, selected, out, expected=720):
    normalized, selected, out = [Path(x).resolve() for x in (normalized, selected, out)]
    if out.exists() or any(out == x or x in out.parents or out in x.parents for x in (normalized, selected)):
        raise ValueError('Use a NEW output folder outside both input folders')
    control_paths = [normalized/'run_report.json', normalized/'game_reports.json',
                     selected/'finish_report.json', selected/'applied_rules.json']
    controls = {str(p): file_hash(p) for p in control_paths}
    nr, reports, sr, rules = [read(p) for p in control_paths]
    if nr.get('status') != 'STRUCTURAL_PASS' or nr.get('scope') != 'full':
        raise ValueError('normalization not passed')
    if sr.get('status') != 'SELECTION_PASS_WITH_LIMITATIONS' or sr.get('scope') != 'full':
        raise ValueError('selection not passed')
    if sr.get('processed_games') != expected or sr.get('expected_games') != expected or sr.get('errors') or sr.get('blocked_games') or sr.get('failed_games') or sr.get('interrupted'):
        raise ValueError('selection coverage/errors mismatch')
    if digest(rules) != sr['rules_sha256']:
        raise ValueError('selection rules changed')
    ids = [r['game_id'] for r in reports]
    if len(ids) != expected or len(set(ids)) != expected or any(not re.fullmatch('[A-Za-z0-9_-]+', g) for g in ids):
        raise ValueError('invalid game inventory')
    plans = {g['game_id']: g for g in rules['games']}
    out.mkdir()
    write(out/'handoff_report.json', {'status': 'RUNNING'})
    errors, games = [], []
    totals, dispositions, events = Counter(), Counter(), Counter()
    interrupted = False
    try:
        for n, report in enumerate(reports, 1):
            gid = report['game_id']
            try:
                src = normalized/'games'/gid/'normalized_game.json'
                sel = selected/'games'/(gid+'.json')
                sh, th = file_hash(src), file_hash(sel)
                data, choice = read(src), read(sel)
                if sh != report['output_sha256'] or sh != choice['normalized_file_sha256'] or data['game_id'] != gid:
                    raise ValueError('source identity/hash mismatch')
                recalculated = select_game(data, plans.get(gid))
                recalculated['normalized_file_sha256'] = sh
                if choice != recalculated or choice['status'] != 'SELECTION_CHECKS_PASS':
                    raise ValueError('selection content changed or not reproducible')
                view = build_game(data, choice)
                view['normalized_file_sha256'], view['selection_file_sha256'] = sh, th
                if file_hash(src) != sh or file_hash(sel) != th:
                    raise ValueError('input changed during read')
                dest = out/'games'/(gid+'.json')
                write(dest, view)
                if read(dest) != view:
                    raise ValueError('output read-back mismatch')
                rows = view['records']
                totals.update({'selected_rows': len(rows), 'excluded_rows': len(view['excluded_records']),
                    'pending_rows': len(choice['pending_semantics']), 'source_text_rows': len(data['plays']),
                    'source_pitch_rows': len(data['tracking_records'])})
                dispositions.update(r['usage']['disposition'] for r in rows)
                events.update(r['event_type'] for r in rows)
                games.append({'game_id': gid, 'records': len(rows), 'output_sha256': file_hash(dest)})
                print(f'[{n}/{expected}] {gid}: CONTRACT_CHECKED', flush=True)
            except (ValueError, KeyError, TypeError, OSError, AssertionError) as e:
                errors.append({'game_id': gid, 'error': str(e)})
                print(gid + ': ERROR ' + str(e), flush=True)
                if isinstance(e, OSError) and e.errno == 28:
                    break
    except KeyboardInterrupt:
        interrupted = True
    for ours, theirs in [('selected_rows','retained_rows'), ('excluded_rows','excluded_rows'),
                        ('pending_rows','pending_semantic_rows'), ('source_text_rows','text_rows'),
                        ('source_pitch_rows','pitch_rows')]:
        if totals[ours] != sr['totals'][theirs]:
            errors.append({'error': 'coverage mismatch: ' + ours})
    changed = [p for p,h in controls.items() if not Path(p).exists() or file_hash(Path(p)) != h]
    passed = len(games) == expected and not errors and not changed and not interrupted
    final = {'schema_version': VERSION, 'status': 'HANDOFF_CONTRACT_PASS' if passed else 'INCOMPLETE',
        'processed_games': len(games), 'expected_games': expected, 'errors': errors,
        'changed_control_files': changed, 'interrupted': interrupted, 'totals': dict(totals),
        'disposition_counts': dict(dispositions), 'event_counts': dict(events),
        'semantic_review_complete': False, 'state_reconstruction_complete': False,
        'plate_appearance_grouping_complete': False,
        'note': 'Policy coverage and source traceability passed; not factual or plate-appearance verification.'}
    write(out/'game_reports.json', games)
    write(out/'handoff_report.json', final)
    print(__import__('json').dumps(final, ensure_ascii=False, indent=2))
    return 0 if passed else 1

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--normalized', type=Path, required=True)
    p.add_argument('--selection', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    try:
        return run(a.normalized, a.selection, a.out)
    except (ValueError, KeyError, TypeError, OSError) as e:
        print('STOP: ' + str(e), file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
