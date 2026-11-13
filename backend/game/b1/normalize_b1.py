"""B1 lossless normalization. Python 3.10+, standard library, offline only."""
import argparse
import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

VERSION = 'b1-row-v1.1'
TEAMS = {'HT': 'KIA', 'SK': 'SSG', 'KT': 'KT', 'LG': 'LG', 'LT': 'LOTTE',
         'SS': 'SAMSUNG', 'OB': 'DOOSAN', 'NC': 'NC', 'WO': 'KIWOOM', 'HH': 'HANWHA'}
PITCH_TYPES = {'직구': 'fastball', '투심': 'two_seam', '슬라이더': 'slider', '커터': 'cutter',
               '스위퍼': 'sweeper', '커브': 'curve', '체인지업': 'changeup', '포크': 'forkball',
               '싱커': 'sinker', '스플리터': 'splitter', '너클볼': 'knuckleball'}


def canonical(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def hash_value(x):
    return hashlib.sha256(canonical(x).encode('utf-8')).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load_json(path):
    def bad(value):
        raise ValueError('Non-finite JSON number: ' + value)
    return json.loads(path.read_text(encoding='utf-8-sig'), parse_constant=bad)


def load_jsonl(path):
    rows = []
    with path.open(encoding='utf-8-sig') as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
            except ValueError as e:
                raise ValueError(f'{path.name}:{line_no}: invalid JSON: {e}') from e
            if not isinstance(value, dict):
                raise ValueError(f'{path.name}:{line_no}: expected object')
            rows.append(value)
    return rows


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    temp.replace(path)


def save_csv(path, rows, fields):
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        for r in rows:
            clean = {}
            for k in fields:
                v = r.get(k, '')
                if isinstance(v, (list, dict)):
                    v = canonical(v)
                # Prevent spreadsheet formulas from untrusted source text.
                if isinstance(v, str) and v[:1] in ('=', '+', '-', '@'):
                    v = "'" + v
                clean[k] = v
            w.writerow(clean)
    temp.replace(path)


def integer(x):
    if isinstance(x, bool):
        return None
    if isinstance(x, int):
        return x
    if isinstance(x, str) and re.fullmatch(r'-?\d+', x):
        return int(x)
    return None


def number(x):
    if isinstance(x, bool) or x is None or x == '':
        return None
    try:
        n = float(x)
        return n if math.isfinite(n) else None
    except (ValueError, TypeError):
        return None


def valid_id(x):
    return None if x is None or str(x).strip() in ('', '-1', '0', 'None') else str(x)


def stable_id(game, kind, source_ref):
    # Frozen source position identity; source hash separately guards updates.
    return f'{game}:{kind}:' + hash_value(source_ref)


def block_key(row):
    """Only explicit source coordinates prove membership in the same block."""
    source = row.get('source_file')
    block = integer(row.get('block_index'))
    if not isinstance(source, str) or not source or block is None or block < 0:
        return None
    return source, block


def classify(text, raw):
    """Return event_type, tags, rule_id. Does not infer causation or state."""
    t = text.strip()
    if '비디오 판독' in t or '비디오판독' in t:
        return 'video_review', ['review'], 'review_text'
    if re.search(r'정정|기록 수정|기록변경|번복|홈런 취소|판정.*변경', t):
        return 'correction_notice', ['correction'], 'correction_text'
    # Narrative notices must not become batter results just because they contain a colon.
    if re.match(r'^\d+회[초말]\s', t) and not re.fullmatch(r'\d+회[초말] .+ 공격', t):
        if '체크스윙' in t:
            return 'check_swing_notice', ['administrative', 'ruling'], 'check_swing_notice'
        if re.search(r'쿨링\s*브레이크|클리닝\s*타임', t):
            return 'break_notice', ['administrative'], 'break_notice'
        if 'ABS' in t:
            return 'abs_notice', ['administrative'], 'abs_notice'
        if re.search(r'콜드게임|경기.*지연', t):
            return 'game_status_notice', ['administrative'], 'game_status_notice'
        if '퇴장' in t:
            return 'ejection_notice', ['administrative', 'ruling'], 'ejection_notice'
        return 'play_notice', ['review'], 'narrative_notice_pending_review'
    if '교체' in t or '수비위치 변경' in t:
        return 'substitution', ['substitution'], 'substitution_text'
    if re.fullmatch(r'\d+회[초말] .+ 공격', t):
        return 'inning_start', ['administrative'], 'inning_header'
    if re.match(r'^\d+구\s', t):
        return 'pitch', ['pitch'], 'pitch_text'
    if re.match(r'^(\d+번타자\s|대타\s)', t):
        return 'batter_announcement', ['administrative'], 'batter_header'
    if '마운드 방문' in t:
        return 'mound_visit', ['administrative'], 'visit_text'
    if t == '포수 덕아웃 방문':
        return 'dugout_visit', ['administrative'], 'dugout_visit'
    if '투수판 이탈' in t:
        return 'pitcher_disengagement', ['administrative'], 'disengagement_text'
    if t and set(t) <= {'=', '-'}:
        return 'separator', ['administrative'], 'separator_text'
    if re.match(r'^(승리투수|패전투수|세이브투수|홀드투수|무승부투수|무승부팀 홀드투수)\s*:', t):
        return 'game_result_notice', ['administrative'], 'result_notice'
    if re.search(r'경기\s*(종료|중단|재개|취소)', t):
        return 'game_status_notice', ['administrative'], 'game_status_text'
    parts = re.split(r'\s*:\s*', t, maxsplit=1)
    if len(parts) != 2:
        return 'unknown', [], 'unrecognized'
    subject, result = parts
    tags = []
    for token, label in [('폭투', 'wild_pitch'), ('포일', 'passed_ball'), ('보크', 'balk'),
                         ('실책', 'error'), ('홈인', 'run_scored')]:
        if token in result:
            tags.append(label)
    if re.match(r'^[123]루주자\s', subject):
        if '도루실패' in result or '도루 실패' in result:
            event = 'caught_stealing'
        elif '견제사' in result:
            event = 'pickoff_out'
        elif '아웃' in result:
            event = 'runner_out'
        elif '홈인' in result:
            event = 'run_scored'
        elif '도루' in result:
            event = 'steal'
        elif '진루' in result:
            event = 'runner_advance'
        else:
            event = 'unknown'
        return event, sorted(set(tags + ['runner'])), 'runner_text' if event != 'unknown' else 'unrecognized'
    # Each outcome is explicitly present in the text. No reconstruction from raw type codes.
    for pattern, event in [
        (r'고의\s*(4구|사구)|고의\s*볼넷', 'intentional_walk'),
        (r'볼넷', 'walk'), (r'몸에\s*맞는\s*(볼|공)', 'hit_by_pitch'),
        (r'삼중살', 'triple_play'), (r'병살', 'double_play'),
        (r'희생\s*번트', 'sacrifice_bunt'), (r'희생\s*플라이', 'sacrifice_fly'),
        (r'낫\s*아웃', 'dropped_third_strike'), (r'쓰리\s*번트\s*아웃|삼진', 'strikeout'),
        (r'홈런(?=\s|\(|$)', 'home_run'), (r'3루타(?=\s|\(|$)', 'triple'), (r'2루타(?=\s|\(|$)', 'double'),
        (r'1루타|내야안타|번트\s*안타', 'single'), (r'실책.*출루', 'reached_on_error'),
        (r'야수\s*선택', 'fielders_choice'), (r'타격\s*방해', 'batting_interference'),
        (r'라인드라이브\s*아웃', 'lineout'), (r'플라이\s*아웃|뜬공\s*아웃', 'flyout'),
        (r'번트\s*아웃', 'bunt_out'), (r'타구맞음\s*아웃', 'batted_ball_out'),
        (r'땅볼\s*아웃', 'groundout')]:
        if re.search(pattern, result):
            return event, sorted(set(tags + ['batter_result'])), 'batter_result_text'
    if '출루' in result:
        # A ground-ball reach does not prove fielders_choice vs error.
        return 'reach_unspecified', sorted(set(tags + ['batter_result'])), 'reach_text_only'
    return 'unknown', tags, 'unrecognized'


def normalize_game(texts, pitches, metadata=None):
    if not texts:
        raise ValueError('Empty text_rows.jsonl')
    game_ids = {r.get('game_id') for r in texts + pitches}
    if len(game_ids) != 1 or not all(isinstance(x, str) and x for x in game_ids):
        raise ValueError('Input must contain exactly one nonempty game_id')
    game = next(iter(game_ids))
    if metadata and metadata.get('gameId') != game:
        raise ValueError('manifest game_id mismatch')
    for rows, kind in [(texts, 'text'), (pitches, 'pitch')]:
        refs = [r.get('source_ref') for r in rows]
        if any(not isinstance(v, str) or not v for v in refs) or len(set(refs)) != len(refs):
            raise ValueError(f'{kind}: missing or duplicate source_ref')
        if any(not isinstance(r.get('raw'), dict) for r in rows):
            raise ValueError(f'{kind}: missing raw object')
    if any(not isinstance(r.get('text'), str) for r in texts):
        raise ValueError('Text missing/not string')
    issues = []
    def issue(code, level='review', play_id=None, detail=''):
        issues.append({'game_id': game, 'level': level, 'code': code,
                       'play_id': play_id, 'detail': detail})
    # Names are accepted only from explicitly keyed records; conflicts remain null.
    names = defaultdict(set)
    for row in texts:
        raw = row['raw']
        b = raw.get('batterRecord')
        if isinstance(b, dict) and valid_id(b.get('pcode')) and b.get('name'):
            names[str(b['pcode'])].add(b['name'])
        change = raw.get('playerChange')
        if isinstance(change, dict):
            for key in ('inPlayer', 'outPlayer'):
                p = change.get(key)
                if isinstance(p, dict) and valid_id(p.get('playerId')) and p.get('playerName'):
                    names[str(p['playerId'])].add(p['playerName'])
    for pid, variants in names.items():
        if len(variants) > 1:
            issue('player_name_conflict', detail=f'{pid}: {sorted(variants)}')
    def player(pid):
        pid = valid_id(pid)
        options = names.get(pid, set())
        return {'player_id': pid, 'name': next(iter(options)) if len(options) == 1 else None,
                'team_id': None, 'identity_basis': 'source_state_id_not_event_actor'}
    away = TEAMS.get((metadata or {}).get('awayTeamCode'))
    home = TEAMS.get((metadata or {}).get('homeTeamCode'))
    pitch_map = defaultdict(list)
    tracks = []
    for row in pitches:
        sid = stable_id(game, 'tracking', row['source_ref'])
        source_id = valid_id(row['raw'].get('pitchId'))
        if source_id:
            pitch_map[source_id].append(sid)
        tracks.append({'tracking_id': sid, 'source_pitch_id': row['raw'].get('pitchId'),
                       'coordinate_units': 'unverified', 'source_record': row})
    track_index = {p['tracking_id']: p for p in tracks}
    plays, used = [], set()
    seq_groups = defaultdict(list)
    text_pitch_blocks = Counter((valid_id(r['raw'].get('ptsPitchId')), block_key(r)) for r in texts)
    repeated_pitch_plays = defaultdict(list)
    last_order = None
    for n, row in enumerate(texts, 1):
        raw = row['raw']
        pid = stable_id(game, 'play', row['source_ref'])
        inn, seq = integer(row.get('inning')), integer(row.get('seqno'))
        half = {'0': 'top', '1': 'bottom'}.get(str(row.get('half_raw')))
        for valid, code in [(inn is not None and inn > 0, 'invalid_inning'),
                            (seq is not None, 'invalid_seqno'), (half is not None, 'unknown_half')]:
            if not valid:
                issue(code, play_id=pid)
        if inn is not None and half is not None and seq is not None:
            order = (inn, 0 if half == 'top' else 1, seq)
            if last_order is not None and order < last_order:
                issue('source_order_decrease', play_id=pid, detail=f'{last_order} -> {order}')
            last_order = order
        if raw.get('text') != row['text'] or str(raw.get('seqno')) != str(row.get('seqno')):
            issue('raw_wrapper_mismatch', play_id=pid)
        event, tags, rule = classify(row['text'], raw)
        if event in ('unknown', 'reach_unspecified', 'correction_notice', 'video_review', 'play_notice'):
            issue('event_needs_review', play_id=pid, detail=f'{event}: {row["text"]}')
        state = raw.get('currentGameState')
        if not isinstance(state, dict):
            state = {}
            issue('missing_source_state', play_id=pid)
        source_pitch_id = valid_id(raw.get('ptsPitchId'))
        all_candidates = pitch_map.get(source_pitch_id, [])
        key = block_key(row)
        candidates = [sid for sid in all_candidates if key is not None
                      and block_key(track_index[sid]['source_record']) == key]
        if event != 'pitch' and not raw.get('ptsPitchId'):
            link = 'not_applicable'
        elif valid_id(raw.get('ptsPitchId')) is None:
            link = 'source_id_missing'
        elif key is None:
            link = 'source_context_missing'
        elif len(candidates) > 1 or text_pitch_blocks[(source_pitch_id, key)] > 1:
            link = 'ambiguous'
        elif len(candidates) == 0:
            link = 'context_conflict' if all_candidates else 'unmatched'
        else:
            track = track_index[candidates[0]]['source_record']
            if (inn is None or half is None or integer(row.get('relay_no')) is None
                    or integer(track.get('inning')) != inn
                    or str(track.get('half_raw')) != str(row.get('half_raw'))
                    or str(track.get('relay_no')) != str(row.get('relay_no'))
                    or (integer(raw.get('pitchNum')) is not None
                        and integer(track['raw'].get('ballcount')) is not None
                        and integer(raw['pitchNum']) != integer(track['raw']['ballcount']))):
                link = 'context_conflict'
            else:
                link = 'matched'
                used.add(candidates[0])
        if event == 'pitch' and link != 'matched':
            issue('pitch_' + link, level='info' if link == 'source_id_missing' else 'review',
                  play_id=pid, detail=str(raw.get('ptsPitchId')))
        pitch = None
        if event == 'pitch' or 'ptsPitchId' in raw:
            result_text = re.sub(r'^\d+구\s*', '', row['text']) if event == 'pitch' else None
            speed = number(raw.get('speed'))
            if raw.get('speed') not in (None, '') and (speed is None or speed <= 0):
                issue('invalid_speed', play_id=pid, detail=str(raw.get('speed')))
                speed = None
            pitch = {'pitch_id': stable_id(game, 'pitch', row['source_ref']),
                     'pitch_number': integer(raw.get('pitchNum')), 'pitch_type': PITCH_TYPES.get(raw.get('stuff')),
                     'pitch_type_raw': raw.get('stuff'), 'speed_value': speed,
                     'speed_unit': 'source_display_unverified', 'result_text': result_text,
                     'result_code_raw': raw.get('pitchResult'), 'source_pitch_id': raw.get('ptsPitchId'),
                     'tracking_id': candidates[0] if link == 'matched' else None,
                     'tracking_candidate_ids': candidates, 'tracking_status': link,
                     'same_id_candidate_ids': all_candidates,
                     'link_basis': 'same_source_file_block_and_id' if link == 'matched' else None}
        play = {'play_id': pid, 'play_number': n, 'game_id': game, 'record_unit': 'source_text_row',
                'plate_appearance_id': None, 'inning': inn, 'inning_half': half,
                'batter': player(state.get('batter')), 'pitcher': player(state.get('pitcher')),
                'batting_team_id': away if half == 'top' else home if half == 'bottom' else None,
                'fielding_team_id': home if half == 'top' else away if half == 'bottom' else None,
                'event_type': event, 'event_tags': tags, 'classification_rule': rule,
                'classification_status': 'unclassified' if event == 'unknown' else 'text_rule',
                'description': row['text'], 'source_seqno': row.get('seqno'),
                'outs_before': None, 'outs_after': None, 'score_before': None, 'score_after': None,
                'runners_before': None, 'runners_after': None, 'state_status': 'pending_B2',
                'pitch': pitch, 'source_record': row}
        plays.append(play)
        if source_pitch_id:
            repeated_pitch_plays[source_pitch_id].append(play)
        if row.get('seqno') is not None:
            seq_groups[str(row['seqno'])].append(play)
    collisions = []
    for seq, group in seq_groups.items():
        if len(group) < 2:
            continue
        raw_hashes = {hash_value(p['source_record']['raw']) for p in group}
        text_set = {p['description'] for p in group}
        types = {p['event_type'] for p in group}
        if len(raw_hashes) == 1:
            classification = 'exact_payload_repeat_candidate'
        elif len(text_set) == 1:
            classification = 'same_text_different_payload'
        elif 'video_review' in types or 'correction_notice' in types:
            classification = 'correction_candidate'
        elif types == {'substitution', 'batter_announcement'}:
            classification = 'distinct_records_same_seqno'
        else:
            classification = 'different_text_unresolved'
        requires_review = classification != 'distinct_records_same_seqno'
        collisions.append({'game_id': game, 'source_seqno': seq, 'classification': classification,
                           'review_required': requires_review, 'action': 'keep_all',
                           'play_ids': [p['play_id'] for p in group],
                           'texts': [p['description'] for p in group]})
        if requires_review:
            issue('seqno_collision_review', detail=f'{seq}: {classification}')
    repeat_groups = []
    for source_id, group in repeated_pitch_plays.items():
        if len(group) < 2:
            continue
        raws = [p['source_record']['raw'] for p in group]
        keys = sorted(set().union(*(r.keys() for r in raws)))
        differing = [k for k in keys if len({canonical([k in r, r.get(k)]) for r in raws}) > 1]
        state_keys = sorted(set().union(*(r.get('currentGameState', {}).keys()
                                         for r in raws if isinstance(r.get('currentGameState'), dict))))
        states = [r.get('currentGameState') if isinstance(r.get('currentGameState'), dict) else {} for r in raws]
        state_diff = [k for k in state_keys if len({canonical([k in s, s.get(k)]) for s in states}) > 1]
        group_id = stable_id(game, 'repeat_candidate', source_id)
        repeat_groups.append({'group_id': group_id, 'source_pitch_id': source_id,
            'classification': 'repeated_pitch_id_candidate', 'action': 'keep_all_pending_review',
            'canonical_play_id': None, 'play_ids': [p['play_id'] for p in group],
            'source_refs': [p['source_record']['source_ref'] for p in group],
            'differing_raw_fields': differing, 'differing_state_fields': state_diff})
        for p in group:
            p['repeat_candidate_group_id'] = group_id
        issue('repeated_pitch_id_review', detail=group_id)
    for track in tracks:
        if track['tracking_id'] not in used:
            issue('unlinked_tracking', detail=track['tracking_id'])
    ids = [p['play_id'] for p in plays] + [p['tracking_id'] for p in tracks]
    ids += [p['pitch']['pitch_id'] for p in plays if p['pitch']]
    if len(ids) != len(set(ids)):
        raise ValueError('Generated ID collision')
    preserved = ([p['source_record'] for p in plays] == texts and
                 [p['source_record'] for p in tracks] == pitches)
    if not preserved:
        raise ValueError('Source preservation failure')
    # A linked source row is not a deduplicated, approved baseball event.
    by_play = defaultdict(set)
    for item in issues:
        if item['level'] == 'review' and item.get('play_id'):
            by_play[item['play_id']].add(item['code'])
    for c in collisions:
        if c['review_required']:
            for pid in c['play_ids']:
                by_play[pid].add('seqno_collision_review')
    for p in plays:
        if p.get('repeat_candidate_group_id'):
            by_play[p['play_id']].add('repeated_pitch_id_review')
        p['review_flags'] = sorted(by_play[p['play_id']])
    timeline_flags = {'source_order_decrease', 'seqno_collision_review', 'repeated_pitch_id_review'}
    timeline_review = any(i['code'] in timeline_flags for i in issues)
    report = {'game_id': game, 'processing_status': 'NORMALIZED',
              'review_status': 'NEEDS_REVIEW' if any(i['level'] == 'review' for i in issues) else 'NO_FLAGS',
              'text_rows_input': len(texts), 'text_rows_output': len(plays),
              'pitch_rows_input': len(pitches), 'pitch_rows_output': len(tracks),
              'source_records_preserved': True, 'id_duplicates': 0,
              'seqno_collision_groups': len(collisions),
              'repeated_pitch_id_groups': len(repeat_groups),
              'timeline_review_required': timeline_review,
              'unknown_event_rows': sum(p['event_type'] == 'unknown' for p in plays),
              'event_types': dict(Counter(p['event_type'] for p in plays)),
              'pitch_links': dict(Counter(p['pitch']['tracking_status'] for p in plays if p['pitch'])),
              'review_items': sum(i['level'] == 'review' for i in issues),
              'info_items': sum(i['level'] == 'info' for i in issues)}
    output = {'schema_version': VERSION, 'game_id': game, 'record_unit': 'source_text_row',
              'metadata_raw': metadata, 'team_code_map': TEAMS, 'state_reconstruction': 'pending_B2',
              'timeline_review_required': timeline_review, 'canonical_timeline_complete': False,
              'repeat_candidate_groups': repeat_groups,
              'plays': plays, 'tracking_records': tracks}
    return output, report, collisions, issues


def process_game(game_dir, out, metadata=None, collector_summary=None):
    paths = [game_dir / 'text_rows.jsonl', game_dir / 'pitch_rows.jsonl']
    before = {p.name: sha(p) for p in paths}
    texts, pitches = [load_jsonl(p) for p in paths]
    output, report, collisions, issues = normalize_game(texts, pitches, metadata)
    if game_dir.name != output['game_id']:
        raise ValueError('Game folder name must equal game_id')
    if collector_summary:
        for field, count in [('text_rows', len(texts)), ('pitch_rows', len(pitches))]:
            if integer(collector_summary.get(field)) != count:
                raise ValueError(f'Collector {field} mismatch')
        if collector_summary.get('status') != 'FETCHED':
            raise ValueError('Collector game status is not FETCHED')
    collision_file = game_dir / 'seqno_collisions.json'
    if collision_file.exists():
        before[collision_file.name] = sha(collision_file)
        supplied = load_json(collision_file)
        if not isinstance(supplied, list):
            raise ValueError('Invalid collector collisions file')
        actual = {str(c['source_seqno']): len(c['play_ids']) for c in collisions}
        expected = {str(c['seqno']): c['count'] for c in supplied}
        if actual != expected:
            raise ValueError('Collector collision count/keys mismatch')
    for name, checksum in before.items():
        if sha(game_dir / name) != checksum:
            raise ValueError('Input changed while reading: ' + name)
    report['input_sha256'] = before
    report['dataset_revision'] = hash_value(before)
    output['dataset_revision'] = report['dataset_revision']
    out.mkdir(parents=True, exist_ok=False)
    save_json(out / 'normalized_game.json', output)
    # Validate serialized artifact, not just the in-memory source references.
    disk = load_json(out / 'normalized_game.json')
    if ([p['source_record'] for p in disk['plays']] != texts or
            [p['source_record'] for p in disk['tracking_records']] != pitches):
        raise ValueError('Serialized source preservation failed')
    report['serialized_preservation_verified'] = True
    report['output_sha256'] = sha(out / 'normalized_game.json')
    save_json(out / 'report.json', report)
    save_json(out / 'collisions.json', collisions)
    save_json(out / 'review_items.json', issues)
    save_json(out / 'repeat_candidates.json', output['repeat_candidate_groups'])
    return report, collisions, issues


def load_season(root, expected):
    manifest = load_json(root / 'manifest.json')
    inventory = load_json(root / 'inventory_check.json')
    with (root / 'summary.csv').open(encoding='utf-8-sig', newline='') as f:
        summary = list(csv.DictReader(f))
    if not isinstance(manifest, list) or len(manifest) != expected:
        raise ValueError(f'manifest must contain {expected} games')
    games = {}
    counts = Counter()
    for item in manifest:
        gid = item.get('gameId')
        if not isinstance(gid, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', gid) or gid in games:
            raise ValueError('Invalid/duplicate manifest gameId')
        teams = [item.get('awayTeamCode'), item.get('homeTeamCode')]
        if any(t not in TEAMS for t in teams) or teams[0] == teams[1]:
            raise ValueError('Unknown or identical teams in manifest')
        counts.update(teams)
        games[gid] = item
    if expected == 720 and (set(counts) != set(TEAMS) or any(n != 144 for n in counts.values())):
        raise ValueError('Team game counts are not 144 each')
    reports = {r.get('game_id'): r for r in summary}
    if len(reports) != len(summary) or set(reports) != set(games):
        raise ValueError('summary/manifest game IDs differ or duplicate')
    if any(r.get('status') != 'FETCHED' for r in summary):
        raise ValueError('Some collector games are not FETCHED')
    if (inventory.get('inventory_passed') is not True or inventory.get('selected_games') != expected
            or inventory.get('schedule_errors') or inventory.get('review_items') or inventory.get('stop_message')):
        raise ValueError('Collector inventory is not passed')
    if inventory.get('checked_days') != inventory.get('expected_days'):
        raise ValueError('Collector day coverage mismatch')
    return games, reports


def run(args):
    root = args.input.resolve()
    out = args.out.resolve()
    if out == root or root in out.parents or out in root.parents:
        raise ValueError('Output must be outside input tree (e.g. data/b1_normalized_v1)')
    if out.exists():
        raise ValueError('Output exists: choose a new --out folder. No overwrite is allowed.')
    input_control = {}
    if args.sample:
        gid = root.name
        selected = {gid: None}
        summaries = {}
        scope = 'sample'
    else:
        selected, summaries = load_season(root, args.expected_games)
        input_control = {name: sha(root / name) for name in ['manifest.json', 'inventory_check.json', 'summary.csv']}
        scope = 'full'
    out.mkdir(parents=True)
    reports, collisions, issues = [], [], []
    interrupted = False
    save_json(out / 'run_report.json', {'status': 'RUNNING', 'scope': scope, 'selected_games': len(selected)})
    try:
        for n, (gid, meta) in enumerate(selected.items(), 1):
            try:
                report, c, i = process_game(root if args.sample else root / 'games' / gid,
                                             out / 'games' / gid, meta, summaries.get(gid))
                reports.append(report)
                collisions.extend(c)
                issues.extend(i)
                print(f'[{n}/{len(selected)}] {gid}: NORMALIZED, review={report["review_items"]}', flush=True)
            except (ValueError, TypeError, KeyError, OSError) as e:
                reports.append({'game_id': gid, 'processing_status': 'ERROR', 'error': str(e)})
                issues.append({'game_id': gid, 'level': 'error', 'code': 'game_failed', 'detail': str(e)})
                print(f'[{n}/{len(selected)}] {gid}: ERROR {e}', flush=True)
            save_json(out / 'progress.json', {'processed_games': len(reports), 'last_game_id': gid})
    except KeyboardInterrupt:
        interrupted = True
    changed_controls = [name for name, checksum in input_control.items() if sha(root / name) != checksum]
    ok = [r for r in reports if r['processing_status'] == 'NORMALIZED']
    complete = len(ok) == len(selected) and not interrupted and not changed_controls
    final = {'schema_version': VERSION, 'scope': scope,
             'status': 'INTERRUPTED' if interrupted else 'STRUCTURAL_PASS' if complete else 'INCOMPLETE',
             'semantic_review_complete': False, 'state_reconstruction_complete': False,
             'selected_games': len(selected), 'processed_games': len(reports), 'normalized_games': len(ok),
             'failed_games': sum(r['processing_status'] == 'ERROR' for r in reports),
             'games_needing_review': sum(r.get('review_status') == 'NEEDS_REVIEW' for r in ok),
             'text_rows_preserved': sum(r['text_rows_output'] for r in ok),
             'pitch_rows_preserved': sum(r['pitch_rows_output'] for r in ok),
             'review_items': sum(i['level'] == 'review' for i in issues),
             'info_items': sum(i['level'] == 'info' for i in issues),
             'collision_groups': len(collisions),
             'repeated_pitch_id_groups': sum(r['repeated_pitch_id_groups'] for r in ok),
             'timeline_review_games': sum(r['timeline_review_required'] for r in ok),
             'unknown_event_rows': sum(r['unknown_event_rows'] for r in ok),
             'review_code_counts': dict(Counter(i['code'] for i in issues if i['level'] == 'review')),
             'pitch_link_counts': dict(sum((Counter(r['pitch_links']) for r in ok), Counter())),
             'collision_types': dict(Counter(c['classification'] for c in collisions)),
             'input_control_sha256': input_control, 'changed_control_files': changed_controls,
             'completed_at_utc': datetime.now(timezone.utc).isoformat(),
             'note': 'Structural pass is preservation/coverage only; read review_items. B2 states remain null.'}
    save_json(out / 'run_report.json', final)
    save_json(out / 'game_reports.json', reports)
    save_json(out / 'collisions.json', collisions)
    save_json(out / 'review_items.json', issues)
    save_csv(out / 'summary.csv', reports, ['game_id', 'processing_status', 'review_status', 'text_rows_input',
             'text_rows_output', 'pitch_rows_input', 'pitch_rows_output', 'id_duplicates', 'review_items', 'error'])
    save_csv(out / 'review_items.csv', issues, ['game_id', 'level', 'code', 'play_id', 'detail'])
    save_csv(out / 'collisions.csv', collisions, ['game_id', 'source_seqno', 'classification',
             'review_required', 'action', 'play_ids', 'texts'])
    print(json.dumps(final, ensure_ascii=False, indent=2))
    return 130 if interrupted else 0 if complete else 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True, help='season_2026 directory; sample: one game directory')
    p.add_argument('--out', type=Path, required=True, help='NEW output directory outside input tree')
    p.add_argument('--sample', action='store_true', help='Only one game; not full-season completion')
    p.add_argument('--expected-games', type=int, default=720)
    args = p.parse_args()
    if args.expected_games <= 0:
        p.error('expected-games must be positive')
    try:
        return run(args)
    except (ValueError, TypeError, KeyError, OSError) as e:
        print('STOP: ' + str(e), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
