"""Read-only verification of B1 review decisions against existing normalized files."""
import argparse
import hashlib
import json
from pathlib import Path

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def check_game(data, decision, version):
    if data.get('schema_version') != version or data.get('game_id') != decision['game_id']:
        raise ValueError('schema/game mismatch')
    plays=data['plays']; tracks=data['tracking_records']
    if len(plays)!=decision['expected_text_rows'] or len(tracks)!=decision['expected_pitch_rows']:
        raise ValueError('row count mismatch')
    for rows,key in [(plays,'source_text_sha256'),(tracks,'source_pitch_sha256')]:
        if digest([r['source_record'] for r in rows])!=decision[key]:
            raise ValueError('source contents or order changed: '+key)
    ids=[p['play_id'] for p in plays]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate play_id')
    index={p['play_id']:p for p in plays}
    for row in decision['administrative_rows_not_for_play_accumulation']:
        p=index.get(row['play_id'])
        if not p or p['description']!=row['description'] or p['source_record']['source_ref']!=row['source_ref']:
            raise ValueError('review play mapping mismatch')
        if p['event_type'] not in ('separator','game_result_notice'):
            raise ValueError('administrative type mismatch')
    for c in decision['reviewed_collision_groups']:
        if not set(c['play_ids']).issubset(index):raise ValueError('collision play mapping mismatch')
    for c in decision['repeat_candidate_groups']:
        if not set(c['play_ids']).issubset(index):raise ValueError('repeat play mapping mismatch')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--decisions',type=Path,default=Path(__file__).with_name('b1_review_decisions.json'))
    a=p.parse_args(); decisions=json.loads(a.decisions.read_text(encoding='utf-8-sig'))
    errors=0
    for d in decisions['games']:
        try:
            path=a.input/'games'/d['game_id']/'normalized_game.json'
            data=json.loads(path.read_text(encoding='utf-8-sig'))
            check_game(data,d,decisions['required_schema_version'])
            print(d['game_id']+': MATCH / '+d['timeline_decision'])
        except (OSError,ValueError,KeyError,TypeError) as e:
            errors+=1; print(d['game_id']+': MISMATCH / '+str(e))
    print('REVIEW_FILE_MATCH' if not errors else 'REVIEW_FILE_MISMATCH')
    print('Read-only check. Matching does not mean semantic or state reconstruction completion.')
    return 1 if errors else 0
if __name__=='__main__':raise SystemExit(main())
