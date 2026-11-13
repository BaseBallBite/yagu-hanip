"""Checked access to selected records. Returned rows are B1 records, not verified facts F."""
from pathlib import Path
from finalize_b1 import read,file_hash

def load_selected(normalized_root,selection_root,game_id):
    if not game_id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in game_id):raise ValueError('invalid game_id')
    root=Path(selection_root)
    run=read(root/'finish_report.json')
    if run['status']!='SELECTION_PASS_WITH_LIMITATIONS':raise ValueError('selection batch not passed')
    selected=read(root/'games'/(game_id+'.json'))
    if selected['status']!='SELECTION_CHECKS_PASS':raise ValueError('game selection blocked')
    path=Path(normalized_root)/'games'/game_id/'normalized_game.json'
    if file_hash(path)!=selected['normalized_file_sha256']:raise ValueError('source changed after selection')
    data=read(path);index={p['play_id']:p for p in data['plays']}
    return {'game_id':game_id,'records':[index[p] for p in selected['ordered_play_ids']],
            'event_candidate_ids':selected['event_candidate_ids'],'context_ids':selected['context_ids'],
            'notice_ids':selected['notice_ids'],'pending_semantics':selected['pending_semantics'],
            'field_limitations':selected['field_limitations'],'global_limitations':selected['global_limitations']}
