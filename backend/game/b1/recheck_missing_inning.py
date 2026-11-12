"""Read-only targeted refetch for 20260415WOHT02026 inning 1. Never installs a patch."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

GAME = '20260415WOHT02026'
URL = 'https://api-gw.sports.naver.com/schedule/games/' + GAME + '/relay?inning=1'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def read_json(raw):
    return json.loads(raw.decode('utf-8-sig'), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))

def get_rows(data):
    if not isinstance(data, dict) or data.get('success') is not True or data.get('code') != 200:
        raise ValueError('API success/code is not 200/true')
    relay = data['result']['textRelayData']
    if relay.get('gameId') != GAME:
        raise ValueError('response game ID differs')
    blocks = relay['textRelays']
    if not isinstance(blocks, list):
        raise ValueError('textRelays is not a list')
    rows = []
    for bi, block in enumerate(blocks):
        if str(block.get('inn')) != '1':
            continue
        half = str(block.get('homeOrAway'))
        if half not in ('0', '1'):
            raise ValueError('unknown half code')
        items = block.get('textOptions', [])
        if not isinstance(items, list):
            raise ValueError('textOptions is not a list')
        for ti, raw in enumerate(items):
            text = raw.get('text')
            if not isinstance(text, str):
                raise ValueError('text is missing or not string')
            rows.append({'block_index': bi, 'item_index': ti, 'half_raw': half,
                         'seqno': raw.get('seqno'), 'text': text, 'raw': raw})
    if not rows:
        raise ValueError('no inning 1 text rows')
    return rows

def projection(row):
    return json.dumps([row['half_raw'], row['seqno'], row['text']], ensure_ascii=False, sort_keys=True)

def compare(old, new):
    a, b = get_rows(old), get_rows(new)
    ca, cb = Counter(map(projection, a)), Counter(map(projection, b))
    added = cb - ca
    added_rows = []
    for row in b:
        key = projection(row)
        if added[key]:
            added_rows.append(row); added[key] -= 1
    first = [r for r in b if r['half_raw'] == '0' and
             re.match(r'^\s*1번타자\s+이주형\s*$', r['text'])]
    outcomes = [r for r in b if r['half_raw'] == '0' and re.match(r'^\s*이주형\s*:', r['text'])]
    candidate = bool(first and outcomes)
    same = ca == cb
    return {'status': 'RECOVERY_CANDIDATE_REVIEW_REQUIRED' if candidate else
             'STILL_MISSING_IN_FRESH_RESPONSE' if same else 'RESPONSE_CHANGED_REVIEW_REQUIRED',
            'game_id': GAME, 'inning': 1, 'old_text_rows': len(a), 'new_text_rows': len(b),
            'text_projection_unchanged': same,
            'old_rows_absent_in_new': sum((ca-cb).values()),
            'new_rows_not_in_old': sum((cb-ca).values()),
            'first_batter_announcement_found': bool(first),
            'first_batter_result_text_found': bool(outcomes),
            'first_batter_evidence': first + outcomes,
            'added_rows': added_rows,
            'restored_or_installed': False,
            'note': 'Candidate detection only. No original, IDs, normalization, PA groups or B2 files were updated.'}

def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def run(old_path, out_base, getter=None):
    old_path = Path(old_path).resolve()
    # Confirm source structure before making a request.
    old_bytes = old_path.read_bytes()
    old = read_json(old_bytes)
    get_rows(old)
    if getter is None:
        from curl_cffi import requests
        getter = requests.get
    out_base = Path(out_base).resolve()
    if out_base == old_path.parent or old_path.parent in out_base.parents:
        raise ValueError('output must be outside original game folder')
    out_base.mkdir(parents=True, exist_ok=True)
    folder = out_base / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder.mkdir(exist_ok=False)
    (folder / 'inning_01_original_snapshot.json').write_bytes(old_bytes)
    report = {'status': 'REQUEST_FAILED', 'game_id': GAME, 'url': URL,
              'original_sha256': sha(old_bytes), 'created_at_utc': datetime.now(timezone.utc).isoformat(),
              'restored_or_installed': False}
    try:
        print('1회만 새로 요청합니다. 기존 저장본은 변경하지 않습니다.', flush=True)
        response = getter(URL, impersonate='chrome', timeout=30, allow_redirects=False)
        report['http_status'] = response.status_code
        if response.status_code != 200:
            report['status'] = 'ACCESS_OR_RATE_LIMIT_STOP' if response.status_code in (401,403,429) else 'HTTP_ERROR'
            raise ValueError('HTTP ' + str(response.status_code) + '; 자동 재시도하지 않습니다.')
        body = bytes(response.content)
        (folder / 'inning_01_refetched.json').write_bytes(body)
        fresh = read_json(body)
        if fresh.get('code') in (401,403,429):
            report['status'] = 'ACCESS_OR_RATE_LIMIT_STOP'
            raise ValueError('API access/rate limit; 자동 재시도하지 않습니다.')
        report.update(compare(old, fresh))
        report['refetched_sha256'] = sha(body)
    except Exception as e:
        report['error'] = str(e)
    finally:
        report['original_file_unchanged'] = sha(old_path.read_bytes()) == sha(old_bytes)
        if not report['original_file_unchanged']:
            report['status'] = 'ORIGINAL_CHANGED_EXTERNALLY'
        save(folder / 'recheck_report.json', report)
        archive = folder.with_suffix('.zip')
        with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
            for p in sorted(folder.iterdir()):
                if p.is_file(): z.write(p, p.name)
        print('상태:', report['status'])
        print('기존 원본 보존:', report['original_file_unchanged'])
        print('공유할 ZIP:', archive)
        print('점검 결과:', folder / 'recheck_report.json')
    return 1 if 'error' in report or not report['original_file_unchanged'] else 0

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--old', type=Path, default=Path(__file__).resolve().parent/'data'/'games'/GAME/'inning_01.json')
    p.add_argument('--out', type=Path, default=Path(__file__).resolve().parent/'data'/'recheck_20260415WOHT02026')
    a = p.parse_args()
    try:
        return run(a.old, a.out)
    except ModuleNotFoundError:
        print('curl_cffi 설치 필요: py -m pip install curl_cffi', file=sys.stderr); return 1
    except (OSError, ValueError, KeyError, TypeError) as e:
        print('STOP:', str(e), file=sys.stderr); return 1

if __name__ == '__main__':
    raise SystemExit(main())
