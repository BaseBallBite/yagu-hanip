#!/usr/bin/env python3
r"""Rebuild B3 v2 strictly from B1 corrected v2 + B2 state v2 ZIPs.

Python 3.10+; standard library only; no pre-existing B3 output is read.

Windows example (run from naver_relay_starter):
  py .\b3_v2_work\scripts\build_b3_v2.py --b1 .\B1_corrected_v2.zip --b2 .\b2_state_v2_all.zip --out .\b3_v2_work\output\B3_final_data_v2.zip --report .\b3_v2_work\reports\B3_v2_build_report.json
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import zipfile

B1_PREFIX = 'B1_corrected_v2/data'
B2_PREFIX = 'b2_state_v2_all/games'
SCHEMA_VERSION = 'b3-pitches-on-b1-v2-b2-v2'
MANUAL_GAME = '20260415WOHT02026'
TRACKING_FIELDS = ('x0', 'y0', 'z0', 'vx0', 'vy0', 'vz0', 'ax', 'ay', 'az',
                   'crossPlateX', 'crossPlateY', 'topSz', 'bottomSz', 'stance', 'ballcount')
MOTION = ('x0', 'y0', 'z0', 'vx0', 'vy0', 'vz0', 'ax', 'ay', 'az')
NONPHYSICAL_TEXT = {
    '피치클락 투수위반 볼': 'pitch_clock_violation',
    '피치클락 타자위반 스트라이크': 'pitch_clock_violation',
    '포수 파울 플라이 포구 실책': 'foul_fly_error_notice',
    '3루수 파울 플라이 포구 실책': 'foul_fly_error_notice',
    '1루수 파울 플라이 포구 실책': 'foul_fly_error_notice',
    '투수 파울 플라이 포구 실책': 'foul_fly_error_notice',
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def dumps(obj, pretty=False):
    return json.dumps(obj, ensure_ascii=False, allow_nan=False,
                      indent=2 if pretty else None,
                      separators=None if pretty else (',', ':')).encode('utf-8')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def number(v):
    if v is None or isinstance(v, bool):
        return None
    try:
        n = float(v)
    except (ValueError, TypeError, OverflowError):
        return None
    return n if math.isfinite(n) else None


def geometry(raw):
    """Conservative display-only model; source tracking raw is never changed.

    Uses the same conservative equation and stop criteria as the earlier
    standalone B3 exporter. Numerical consistency != independently validated
    sensor coordinate convention or actual flight trajectory.
    """
    parsed = {k: number(raw.get(k)) for k in TRACKING_FIELDS if k != 'stance'}
    if any(parsed[k] is None for k in MOTION + ('crossPlateX', 'crossPlateY')):
        return None, None, 'missing_motion_fields'
    x, y, z, vx, vy, vz, ax, ay, az = (parsed[k] for k in MOTION)
    cross_x, cross_y = parsed['crossPlateX'], parsed['crossPlateY']
    distance_y = y - cross_y
    if distance_y <= 0 or vy >= 0 or z <= 0:
        return None, None, 'invalid_release_or_direction'
    discriminant = vy * vy - 2 * ay * distance_y
    if discriminant < 0:
        return None, None, 'no_plate_intersection'
    denominator = -vy + math.sqrt(discriminant)
    if denominator <= 0:
        return None, None, 'no_plate_intersection'
    duration = 2 * distance_y / denominator
    end_z = z + vz * duration + 0.5 * az * duration * duration
    end_x = x + vx * duration + 0.5 * ax * duration * duration
    if not all(map(math.isfinite, (duration, end_z, end_x))) or not 0 < duration <= 1:
        return None, None, 'invalid_flight_time'
    if abs(end_x - cross_x) > 0.05:
        return None, None, 'horizontal_endpoint_mismatch'
    lowest = min(z, end_z)
    if az > 0 and 0 < -vz / az < duration:
        t_min = -vz / az
        lowest = min(lowest, z + vz * t_min + 0.5 * az * t_min * t_min)
    if lowest < 0:
        return None, None, 'model_below_ground'
    top, bottom = parsed['topSz'], parsed['bottomSz']
    zone = None
    if top is not None and bottom is not None and 0 <= bottom < top:
        zone = {'x_ft': cross_x, 'height_ft': round(end_z, 6),
                'top_ft': top, 'bottom_ft': bottom}
    flight = {'duration_s': round(duration, 9),
              'release_ft': [x, y, z],
              'velocity_ft_s': [vx, vy, vz],
              'acceleration_ft_s2': [ax, ay, az]}
    return zone, flight, 'ok' if zone is not None else 'invalid_zone_bounds'


def get_games(zf, prefix):
    names = zf.namelist()
    require(len(names) == len(set(names)), 'ZIP has duplicate member paths')
    if prefix == B1_PREFIX:
        pre = f'{B1_PREFIX}/b1_normalized_v11/games/'
        suf = '/normalized_game.json'
        ids = {name[len(pre):-len(suf)] for name in names
               if name.startswith(pre) and name.endswith(suf)
               and '/' not in name[len(pre):-len(suf)]}
    else:
        pre = f'{B2_PREFIX}/'
        ids = {name[len(pre):-5] for name in names
               if name.startswith(pre) and name.endswith('.json')
               and '/' not in name[len(pre):]}
    return ids


def check_old_source(play, track, pitch):
    require(pitch.get('tracking_id') == track['tracking_id'], 'tracking key mismatch')
    psource = play['source_record']
    tsource = track['source_record']
    require(all(psource.get(k) == tsource.get(k) for k in
                ('source_file', 'block_index', 'inning', 'half_raw', 'relay_no')),
            f'{play["play_id"]}: tracking source block mismatch')
    raw = tsource['raw']
    require(str(raw.get('pitchId')) == str(pitch.get('source_pitch_id')),
            f'{play["play_id"]}: original pitch ID mismatch')
    return raw


def build_one(gid, b1, b2, stats):
    nf = f'{B1_PREFIX}/b1_normalized_v11/games/{gid}/normalized_game.json'
    sf = f'{B1_PREFIX}/b1_selection_v1/games/{gid}.json'
    pf = f'{B1_PREFIX}/b1_plate_appearances_v2/games/{gid}.json'
    bf = f'{B2_PREFIX}/{gid}.json'
    norm_raw, sel_raw, pa_raw, b2_raw = (b1.read(nf), b1.read(sf), b1.read(pf), b2.read(bf))
    norm, sel, pa, b2_game = (json.loads(norm_raw), json.loads(sel_raw),
                              json.loads(pa_raw), json.loads(b2_raw))
    require(all(d['game_id'] == gid for d in (norm, sel, pa)), f'{gid}: input game ID mismatch')
    require(sha(norm_raw) == sel['normalized_file_sha256'], f'{gid}: B1 norm-selection hash mismatch')
    require(sel['status'] in ('SELECTION_CHECKS_PASS', 'MANUAL_OVERLAY_READY_FOR_B2_TEST'),
            f'{gid}: unexpected selection status {sel["status"]}')
    require(not sel.get('blocking_issues'), f'{gid}: unresolved B1 blocking issues')
    require(pa['grouping_complete'], f'{gid}: B1 PA grouping incomplete')

    order = sel['ordered_play_ids']
    plays = {p['play_id']: p for p in norm['plays']}
    links = pa['row_links']
    track = {t['tracking_id']: t for t in norm['tracking_records']}
    groups = {g['plate_appearance_id']: g for g in pa['groups']}
    state_rows = b2_game['rows']

    require(len(plays) == len(norm['plays']), f'{gid}: duplicate B1 play IDs')
    require(len(track) == len(norm['tracking_records']), f'{gid}: duplicate tracking IDs')
    require(len(groups) == len(pa['groups']), f'{gid}: duplicate PA IDs')
    require(len(order) == len(set(order)), f'{gid}: duplicate selected IDs')
    require(set(order) <= set(plays), f'{gid}: unknown selected play ID')
    require([a['play_id'] for a in links] == order, f'{gid}: PA link order mismatch')
    require([a['play_id'] for a in state_rows] == order, f'{gid}: B2 row order mismatch')
    require(b2_game['summary']['final_score_match'], f'{gid}: B2 final score mismatch')
    require(not b2_game['summary']['half_innings_not_3_outs'], f'{gid}: B2 half-inning outs mismatch')

    unique_ids = set()
    pitches = []
    for play_id, link, state in zip(order, links, state_rows):
        play = plays[play_id]
        pitch = play.get('pitch')
        if pitch is None:
            continue
        require(play['event_type'] == 'pitch', f'{gid}: unexpected event with pitch object')
        pid = pitch['pitch_id']
        require(pid and pid not in unique_ids, f'{gid}: duplicate/missing pitch_id {pid}')
        unique_ids.add(pid)
        pa_id = link['plate_appearance_id']
        group = groups.get(pa_id) if pa_id is not None else None
        require(pa_id is None or group is not None, f'{gid}: PA group missing')
        if group is not None:
            require(play_id in group['pitch_play_ids'], f'{gid}: PA pitch membership mismatch')

        reconstructed = play.get('record_unit') == 'manual_verified_reconstruction'
        raw = None
        zone = None
        trajectory = None
        tracking_status = pitch.get('tracking_status')
        geometry_status = 'tracking_unavailable'
        if not reconstructed and tracking_status == 'matched':
            tracking_id = pitch.get('tracking_id')
            require(tracking_id in track, f'{gid}: tracking ID not found {tracking_id}')
            raw = check_old_source(play, track[tracking_id], pitch)
            zone, trajectory, geometry_status = geometry(raw)
        elif reconstructed:
            require(play['source_seqno'] is None and pitch.get('source_pitch_id') is None
                    and pitch.get('tracking_id') is None,
                    f'{gid}: manual pitch contains invented source ID')
            require(pitch.get('speed_value') is None and pitch.get('pitch_type') is None,
                    f'{gid}: manual pitch has unverified pitch facts')

        result_text = pitch.get('result_text')
        speed = number(pitch.get('speed_value'))
        if reconstructed:
            kind = 'manual_reconstructed_pitch'
            physical = True
            vis = 'manual_no_tracking'
        else:
            kind = NONPHYSICAL_TEXT.get(result_text, 'physical_pitch')
            physical = kind == 'physical_pitch'
            if not physical:
                require(pitch.get('pitch_number') is None and speed is None
                        and pitch.get('source_pitch_id') is None and zone is None
                        and trajectory is None,
                        f'{gid}: nonphysical pitch unexpectedly has physical details')
                vis = 'not_a_physical_pitch'
            else:
                require(pitch.get('pitch_number') is not None and speed is not None,
                        f'{gid}: physical source pitch lacks number/speed')
                if geometry_status == 'ok' and zone is not None and trajectory is not None:
                    vis = 'available'
                elif geometry_status == 'model_below_ground' and zone is None and trajectory is None:
                    vis = 'model_below_ground'
                elif (geometry_status == 'tracking_unavailable'
                      and tracking_status == 'source_id_missing'
                      and str(pitch.get('source_pitch_id')) == '-1'):
                    vis = 'tracking_id_missing'
                else:
                    raise ValueError(f'{gid}: unexpected geometry status for {pid}: '
                                     f'{geometry_status} / {tracking_status}')

        stats['pitch_related_rows'] += 1
        stats['kind_' + kind] += 1
        stats['visualization_' + vis] += 1
        stats['tracking_' + str(tracking_status)] += 1
        stats['physical_pitch_rows'] += bool(physical)
        stats['source_pitch_rows'] += not reconstructed
        stats['manual_pitch_rows'] += reconstructed
        stats['b2_joined_rows'] += 1
        stats['zone_available'] += zone is not None
        stats['trajectory_available'] += trajectory is not None

        pitches.append({
            'play_id': play_id, 'pitch_id': pid, 'plate_appearance_id': pa_id,
            'pa_review_flags': group.get('review_flags', []) if group else [],
            'inning': play['inning'], 'half_raw': play['source_record']['half_raw'],
            'pitch_number': pitch.get('pitch_number'),
            'pitch_type': pitch.get('pitch_type'), 'pitch_type_raw': pitch.get('pitch_type_raw'),
            'speed_reported': speed, 'speed_unit': pitch.get('speed_unit'),
            'result_text': result_text, 'result_code_raw': pitch.get('result_code_raw'),
            'source_pitch_id': pitch.get('source_pitch_id'),
            'tracking_id': pitch.get('tracking_id'), 'tracking_status': tracking_status,
            'source_ref': play['source_record']['source_ref'],
            'geometry_status': geometry_status, 'zone': zone, 'trajectory': trajectory,
            'tracking_raw': {k: raw.get(k) for k in TRACKING_FIELDS} if raw else None,
            'state_before': state['state_before'], 'state_after': state['state_after'],
            'state_join_status': 'joined',
            'source_origin': 'manual_verified_reconstruction' if reconstructed else 'naver_source',
            'pitch_record_kind': kind, 'is_physical_pitch': physical,
            'visualization_status': vis,
            'review_flags': ['manual_source_reconstruction'] if reconstructed else [],
        })

    return {
        'schema_version': SCHEMA_VERSION,
        'game_id': gid,
        'b1_normalized_sha256': sha(norm_raw),
        'b1_selection_sha256': sha(sel_raw),
        'b2_state_file_sha256': sha(b2_raw),
        'b2_state_version': b2_game.get('version'),
        'b2_state_status': 'joined',
        'b2_validation': b2_game['summary'],
        'pitches': pitches,
    }, b2_raw


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--b1', type=Path, required=True)
    ap.add_argument('--b2', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    ap.add_argument('--sample-game', action='append', default=[],
                    help='Optional specific game ID; omit for full 720-game run')
    a = ap.parse_args()
    for file in (a.b1, a.b2):
        require(file.is_file(), f'Input file does not exist: {file}')
    require(a.out.resolve() not in (a.b1.resolve(), a.b2.resolve()), 'Output cannot overwrite input')
    require(a.out.resolve() != a.report.resolve(), 'Report and ZIP paths must differ')
    require(not a.out.exists() and not a.report.exists(),
            'Refusing to overwrite an existing output/report file')

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    temp = a.out.with_name(a.out.name + '.partial')
    require(not temp.exists(), f'Old partial output exists: {temp}')
    stats = Counter()
    input_meta = {'B1_corrected_v2.zip_sha256': file_sha(a.b1),
                  'b2_state_v2_all.zip_sha256': file_sha(a.b2)}
    processed_ids = []
    try:
        with zipfile.ZipFile(a.b1) as b1, zipfile.ZipFile(a.b2) as b2:
            b1_ids, b2_ids = get_games(b1, B1_PREFIX), get_games(b2, B2_PREFIX)
            require(len(b1_ids) == len(b2_ids) == 720 and b1_ids == b2_ids,
                    'B1/B2 720-game ID coverage mismatch')
            game_ids = sorted(set(a.sample_game)) if a.sample_game else sorted(b1_ids)
            require(set(game_ids) <= b1_ids, 'Unknown sample game ID')
            with zipfile.ZipFile(temp, 'w', compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=1, allowZip64=True) as out:
                for i, gid in enumerate(game_ids, 1):
                    doc, b2_raw = build_one(gid, b1, b2, stats)
                    out.writestr(f'games/{gid}.json', dumps(doc))
                    # Include the identical B2 result for downstream review.
                    out.writestr(f'b2_state/games/{gid}.json', b2_raw)
                    processed_ids.append(gid)
                    if i % 50 == 0 or i == len(game_ids):
                        print(f'[{i}/{len(game_ids)}] B3 rebuilt', flush=True)
                full = not a.sample_game
                if full:
                    for key, expected in (
                        ('pitch_related_rows', 221661),
                        ('source_pitch_rows', 221658),
                        ('manual_pitch_rows', 3),
                        ('physical_pitch_rows', 221530),
                        ('kind_physical_pitch', 221527),
                        ('kind_manual_reconstructed_pitch', 3),
                        ('kind_pitch_clock_violation', 116),
                        ('kind_foul_fly_error_notice', 15),
                        ('b2_joined_rows', 221661),
                    ):
                        require(stats[key] == expected,
                                f'{key} differs from expected {expected}: {stats[key]}')
                report = {
                    'status': 'B3_V2_REBUILD_STRUCTURAL_PASS',
                    'version': SCHEMA_VERSION,
                    'built_at_utc': datetime.now(timezone.utc).isoformat(),
                    'input_file_hashes': input_meta,
                    'input_b1': a.b1.name, 'input_b2': a.b2.name,
                    'game_count': len(processed_ids),
                    'full_720_run': full,
                    'counts': dict(stats),
                    'notes': [
                        'Original source pitch data is preserved; 3 manual pitches have no source tracking or speed.',
                        'B2 states joined strictly via selected play_id and ordered_play_ids.',
                        'Naver currentGameState errors are not automatically overwritten.',
                        'Zone/trajectory are model-derived display values, not independently verified coordinates.',
                        'Use is_physical_pitch and visualization_status for frontend display.'
                    ],
                }
                out.writestr('B3_v2_build_report.json', dumps(report, pretty=True))
        with zipfile.ZipFile(temp) as z:
            require(len(z.namelist()) == len(processed_ids) * 2 + 1,
                    'Output member count mismatch')
            require(z.testzip() is None, 'Output ZIP CRC check failed')
        # Do not modify user-controlled input or previously created artifacts.
        os.replace(temp, a.out)
        a.report.write_bytes(dumps(report, pretty=True))
        print('\nB3 V2 REBUILD PASS')
        print('Games:', len(processed_ids))
        print('Pitch-related rows:', stats['pitch_related_rows'])
        print('Manual reconstructed pitches:', stats['manual_pitch_rows'])
        print('B2 state joins:', stats['b2_joined_rows'])
        print('Output:', a.out)
        print('Report:', a.report)
        print('Still requires visual coordinate direction/physical accuracy check and downstream API tests.')
    except Exception:
        if temp.exists():
            temp.unlink()
        raise


if __name__ == '__main__':
    main()
