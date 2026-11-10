#!/usr/bin/env python3
"""2026 KBO regular-season raw collector. Python 3.10+, curl_cffi.

Raw preservation and structural audit only; NOT PlayEvent normalization.
Based on the user's fetch_games.py endpoint implementation.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlencode, quote

BASE = 'https://api-gw.sports.naver.com'
START, END = date(2026, 3, 28), date(2026, 10, 12)
EXPECTED = 720
TEAMS = {'HT': 'KIA', 'SK': 'SSG', 'KT': 'KT', 'LG': 'LG', 'LT': '롯데',
         'SS': '삼성', 'OB': '두산', 'NC': 'NC', 'WO': '키움', 'HH': '한화'}
SUMMARY_FIELDS = ['game_id', 'date', 'away', 'home', 'away_score', 'home_score',
                  'status', 'last_inning', 'innings_with_text', 'text_rows',
                  'rows_with_state', 'pitch_rows', 'same_seq_groups',
                  'scoreboard_matches_schedule', 'warnings']
NOTE = ('수집·기초 구조 검사 결과이며 경기 내용 완전성, 상태 전/후 의미, '
        '주자 복원 또는 투구 좌표 단위 검증을 보장하지 않습니다.')


class StopCollection(Exception):
    pass


def integer(value):
    if isinstance(value, bool):
        return None
    try:
        return int(str(value))
    except (ValueError, TypeError):
        return None


def truthy(value):
    return str(value).lower() in ('true', '1', 'y', 'yes')


def stamp():
    return datetime.now(timezone.utc).isoformat()


def save_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(content, encoding='utf-8')
    tmp.replace(path)


def save_json(path, data):
    save_text(path, json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def write_jsonl(path, rows):
    save_text(path, ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))


def validate_envelope(payload):
    if not isinstance(payload, dict):
        raise ValueError('객체가 아닌 응답')
    code = integer(payload.get('code'))
    if code in (401, 403, 429):
        raise StopCollection(f'API code {code}: 제한 응답. 자동 재시도 중단')
    if payload.get('success') is False:
        raise ValueError('API 실패 응답')
    if code is not None and code != 200:
        raise ValueError(f'API code={code}')
    if not isinstance(payload.get('result'), dict):
        raise ValueError('result 객체 없음')


def validate_schedule(payload):
    validate_envelope(payload)
    result = payload['result']
    games = result.get('games')
    if not isinstance(games, list) or any(not isinstance(g, dict) for g in games):
        raise ValueError('games 배열 형식 오류')
    total = integer(result.get('gameTotalCount'))
    if total is None or total != len(games):
        raise ValueError(f'경기 목록 전체성 확인 불가: 반환 {len(games)} / total {total}')


def validate_relay(payload, gid, inning=None):
    validate_envelope(payload)
    data = payload['result'].get('textRelayData')
    if not isinstance(data, dict) or str(data.get('gameId')) != gid:
        raise ValueError('textRelayData 누락 또는 응답 gameId 불일치')
    blocks = data.get('textRelays')
    if not isinstance(blocks, list) or not blocks:
        raise ValueError('textRelays 없음/빈 배열')
    matches = []
    for b in blocks:
        if not isinstance(b, dict) or integer(b.get('inn')) is None:
            raise ValueError('중계 묶음 형식 오류/inn 누락')
        for key in ('textOptions', 'ptsOptions'):
            items = b.get(key)
            if items is not None and (not isinstance(items, list)
                                      or any(not isinstance(x, dict) for x in items)):
                raise ValueError(f'{key} 형식 오류')
        if inning is None or integer(b['inn']) == inning:
            matches.append(b)
    if not matches or not any(b.get('textOptions') for b in matches):
        raise ValueError(f'요청 이닝({inning}) 문자 데이터 없음')


class Client:
    def __init__(self, root, delay=2, timeout=30, attempts=3, offline=False,
                 getter=None, sleeper=time.sleep):
        self.root = root
        self.delay, self.timeout, self.attempts = delay, timeout, attempts
        self.offline, self.getter, self.sleep = offline, getter, sleeper
        self.stats = Counter()

    def fetch(self, url, path, validator, refresh=False):
        if path.exists() and not refresh:
            try:
                payload = json.loads(path.read_text(encoding='utf-8-sig'))
                validator(payload)
                self.stats['cache_hits'] += 1
                return payload
            except StopCollection:
                raise
            except (ValueError, OSError, TypeError) as exc:
                if self.offline:
                    raise ValueError(f'오프라인 캐시 검사 실패: {path.name}: {exc}') from exc
                # Preserve the invalid response instead of deleting it.
                archived = path.with_name(path.name + f'.invalid-{time.time_ns()}')
                path.replace(archived)
                self.stats['invalid_cache_archived'] += 1
                print(f'  유효하지 않은 저장본 보존 후 재요청: {path.name}', flush=True)
        if self.offline:
            raise OSError(f'오프라인 모드: 저장본 없음 {path.name}')
        if self.getter is None:
            import curl_cffi
            self.getter = curl_cffi.get
        for attempt in range(1, self.attempts + 1):
            self.sleep(self.delay if attempt == 1 else max(self.delay, 5 * 2 ** (attempt - 2)))
            self.stats['network_attempts'] += 1
            print(f'  요청 {attempt}/{self.attempts}: {path.parent.name}/{path.name}', flush=True)
            try:
                response = self.getter(url, impersonate='chrome', timeout=self.timeout)
            except Exception as exc:
                if attempt == self.attempts:
                    raise OSError(f'연결 실패: {exc}') from exc
                continue
            status = response.status_code
            if status in (401, 403, 429):
                raise StopCollection(f'HTTP {status}: 접근/요청 제한. 자동 재시도 중단')
            if status == 408 or 500 <= status <= 599:
                if attempt == self.attempts:
                    raise OSError(f'HTTP {status}: {self.attempts}회 시도 실패')
                continue
            if status != 200:
                raise OSError(f'HTTP {status}')
            try:
                payload = response.json()
                validator(payload)
            except StopCollection:
                raise
            except (ValueError, TypeError) as exc:
                # Keep evidence but never cache this as a successful response.
                evidence = path.with_name(path.name + f'.rejected-{time.time_ns()}.txt')
                save_text(evidence, response.text)
                raise ValueError(f'응답 구조 검사 실패: {exc}') from exc
            save_json(path, payload)
            self.stats['downloaded'] += 1
            return payload
        raise RuntimeError('unreachable')


def select_game(game):
    """Date+category+10 club codes; no undocumented gameId suffix assumption."""
    gid = str(game.get('gameId', ''))
    if not re.fullmatch(r'[A-Za-z0-9_-]+', gid):
        return 'REVIEW', 'gameId 누락/형식 오류'
    if game.get('categoryId') != 'kbo':
        return 'EXCLUDED', 'KBO 구단 경기 category가 아님'
    try:
        day = date.fromisoformat(str(game.get('gameDate')))
    except ValueError:
        return 'REVIEW', 'gameDate 형식 오류'
    if not START <= day <= END:
        return 'EXCLUDED', '정규시즌 날짜 범위 밖'
    a, h = game.get('awayTeamCode'), game.get('homeTeamCode')
    if a not in TEAMS or h not in TEAMS:
        return 'EXCLUDED', '10개 구단 간 경기가 아님 (올스타 등)'
    if a == h:
        return 'REVIEW', '같은 팀끼리의 대진'
    if truthy(game.get('cancel')):
        return 'EXCLUDED', '취소 경기'
    if game.get('statusCode') != 'RESULT':
        return 'REVIEW', '종료 RESULT 아님: 중단/재편성/캐시 상태 확인'
    # A RESULT can retain suspended=true after resumption. Do not silently drop it.
    if any(integer(game.get(k)) is None or integer(game[k]) < 0
           for k in ('awayTeamScore', 'homeTeamScore')):
        return 'REVIEW', '최종 점수 누락/형식 오류'
    return 'SELECTED', ''


def schedule_inventory(client, report_root, refresh=False):
    by_id, excluded, review, errors = {}, [], [], []
    checked_days = 0
    day = START
    stopped = ''
    try:
        while day <= END:
            ds = day.isoformat()
            print(f'경기 목록: {ds}', flush=True)
            params = urlencode({'fields': 'basic', 'upperCategoryId': 'kbaseball',
                                'categoryId': 'kbo', 'fromDate': ds, 'toDate': ds})
            try:
                payload = client.fetch(f'{BASE}/schedule/games?{params}',
                                       report_root / 'schedules' / f'{ds}.json',
                                       validate_schedule, refresh=refresh)
                checked_days += 1
                for game in payload['result']['games']:
                    verdict, reason = select_game(game)
                    entry = {'source_date': ds, 'game_id': game.get('gameId'),
                             'reason': reason, 'game': game}
                    if verdict == 'EXCLUDED':
                        excluded.append(entry)
                    elif verdict == 'REVIEW':
                        review.append(entry)
                    else:
                        gid = game['gameId']
                        prior = by_id.get(gid)
                        if prior and any(prior.get(k) != game.get(k) for k in (
                                'gameDate', 'awayTeamCode', 'homeTeamCode',
                                'awayTeamScore', 'homeTeamScore')):
                            review.append({**entry, 'reason': '동일 gameId의 날짜/팀/점수 상충'})
                        else:
                            by_id[gid] = game
            except (ValueError, OSError, TypeError) as exc:
                errors.append({'date': ds, 'error': str(exc)})
            day += timedelta(days=1)
    except (StopCollection, KeyboardInterrupt) as exc:
        stopped = str(exc) or '사용자 중단'
    games = sorted(by_id.values(), key=lambda g: (g['gameDate'], g['gameId']))
    counts = Counter()
    for g in games:
        counts.update([g['awayTeamCode'], g['homeTeamCode']])
    team_rows = [{'team_code': k, 'team': v, 'games': counts[k], 'expected': 144}
                 for k, v in TEAMS.items()]
    passed = (not stopped and not errors and not review and len(games) == EXPECTED
              and all(row['games'] == 144 for row in team_rows)
              and checked_days == (END - START).days + 1)
    result = {'checked_at_utc': stamp(), 'start': str(START), 'end': str(END),
              'expected_games': EXPECTED, 'selected_games': len(games),
              'checked_days': checked_days, 'expected_days': (END - START).days + 1,
              'team_counts': team_rows, 'schedule_errors': errors,
              'review_items': review, 'excluded_items': excluded,
              'stop_message': stopped, 'inventory_passed': passed,
              'scope_note': '날짜+categoryId+구단 코드로 선택. 별도 공식 경기별 ID 대조는 아님. '
                            '720경기/팀별144경기는 누락·혼입 탐지 보조 검사.'}
    save_json(report_root / 'manifest.json', games)
    write_csv(report_root / 'game_index.csv', games, ['gameId', 'gameDate',
              'awayTeamCode', 'awayTeamName', 'homeTeamCode', 'homeTeamName',
              'awayTeamScore', 'homeTeamScore', 'statusCode', 'suspended'])
    write_csv(report_root / 'team_counts.csv', team_rows, ['team_code', 'team', 'games', 'expected'])
    save_json(report_root / 'inventory_check.json', result)
    return games, result


def final_inning(data, game):
    values = [integer(data.get('inn'))]
    values += [integer(b.get('inn')) for b in data['textRelays']]
    score = data.get('inningScore') or {}
    if isinstance(score, dict):
        for side in ('away', 'home'):
            side_score = score.get(side)
            if not isinstance(side_score, dict):
                continue
            for key, val in side_score.items():
                if str(val).strip() not in ('', '-', 'None'):
                    values.append(integer(key))
    match = re.search(r'(\d+)회', str(game.get('statusInfo', '')))
    if match:
        values.append(int(match.group(1)))
    values = [v for v in values if v is not None and v > 0]
    if not values or max(values) > 30:
        raise ValueError('마지막 이닝 확인 불가')
    return max(values)


def scoreboard_check(data, game):
    """Compare inningScore sums, NOT reconstructed runner/state scores."""
    score = data.get('inningScore')
    if not isinstance(score, dict):
        return None, []
    expected_halves = []
    totals = {}
    for side, half in [('away', '0'), ('home', '1')]:
        values = score.get(side)
        if not isinstance(values, dict) or not values:
            return None, []
        nums = []
        for key, value in values.items():
            inn = integer(key)
            if inn is None or inn <= 0:
                continue
            if str(value).strip() == '-':
                continue
            n = integer(value)
            if n is None or n < 0:
                return None, []
            nums.append(n)
            expected_halves.append((inn, half))
        if not nums:
            return None, []
        totals[side] = sum(nums)
    return (totals['away'] == integer(game.get('awayTeamScore')) and
            totals['home'] == integer(game.get('homeTeamScore'))), expected_halves


def collect_game(game, root, report_root, client):
    gid = game['gameId']
    folder = root / 'games' / gid
    folder.mkdir(parents=True, exist_ok=True)
    if not (folder / 'game.json').exists():
        save_json(folder / 'game.json', game)
    # Current schedule metadata is always in manifest.json; older game.json is preserved.
    url = f'{BASE}/schedule/games/{quote(gid, safe="")}/relay'
    payload = client.fetch(url, folder / 'relay_latest.json', lambda p: validate_relay(p, gid))
    latest = payload['result']['textRelayData']
    last = final_inning(latest, game)
    text_rows, pitches, failures, warnings, source_files = [], [], [], [], []
    source_files.append(folder / 'relay_latest.json')
    for inn in range(1, last + 1):
        path = folder / f'inning_{inn:02d}.json'
        try:
            payload = client.fetch(f'{url}?inning={inn}', path,
                                   lambda p, n=inn: validate_relay(p, gid, n))
        except (ValueError, OSError, TypeError) as exc:
            failures.append({'inning': inn, 'error': str(exc)})
            continue
        source_files.append(path)
        for bi, block in enumerate(payload['result']['textRelayData']['textRelays']):
            if integer(block['inn']) != inn:
                warnings.append(f'{inn}회 응답에 다른 이닝 포함 (원본 보존, 파생 행에서 제외)')
                continue
            shared = {'game_id': gid, 'inning': inn, 'half_raw': block.get('homeOrAway'),
                      'relay_no': block.get('no'),
                      'source_file': path.relative_to(root).as_posix(), 'block_index': bi}
            for ti, item in enumerate(block.get('textOptions') or []):
                # Every original row kept, including same seqno/text with different state.
                text_rows.append({**shared, 'source_ref': f'{gid}/i{inn:02d}/b{bi}/t{ti}',
                                  'item_index': ti, 'seqno': item.get('seqno'),
                                  'text': item.get('text'), 'raw': item})
            for pi, item in enumerate(block.get('ptsOptions') or []):
                pitches.append({**shared, 'source_ref': f'{gid}/i{inn:02d}/b{bi}/p{pi}',
                                'item_index': pi, 'raw': item})
    # This ordering is a viewing aid, not a semantically validated PlayEvent order.
    text_rows.sort(key=lambda r: (r['inning'], integer(r['half_raw']) or 0,
                                 integer(r['relay_no']) or 0,
                                 integer(r['seqno']) if integer(r['seqno']) is not None else 10**9,
                                 r['block_index'], r['item_index']))
    groups = defaultdict(list)
    for row in text_rows:
        if row['seqno'] is not None:
            groups[str(row['seqno'])].append(row)
    collisions = [{'game_id': gid, 'seqno': seq, 'count': len(rows),
                   'different_texts': len({r['text'] for r in rows}),
                   'rows': [{'source_ref': r['source_ref'], 'text': r['text'],
                             'inning': r['inning'], 'half_raw': r['half_raw']} for r in rows]}
                  for seq, rows in groups.items() if len(rows) > 1]
    halves = {(r['inning'], str(r['half_raw'])) for r in text_rows}
    innings = {r['inning'] for r in text_rows}
    state_count = sum(isinstance(r['raw'].get('currentGameState'), dict)
                      and bool(r['raw']['currentGameState']) for r in text_rows)
    score_match, expected_halves = scoreboard_check(latest, game)
    if failures:
        warnings.append('이닝 요청/캐시 실패: ' + ', '.join(str(f['inning']) for f in failures))
    if innings != set(range(1, last + 1)):
        warnings.append(f'문자 없는 이닝: {sorted(set(range(1, last + 1)) - innings)}')
    missing_halves = sorted(set(expected_halves) - halves)
    if missing_halves:
        warnings.append(f'스코어보드에 있지만 문자가 없는 반이닝: {missing_halves}')
    if score_match is not True:
        warnings.append('이닝 점수 합계와 경기 목록 점수 불일치/확인 불가 (원본 수동 확인)')
    if state_count != len(text_rows):
        warnings.append(f'행별 상태 누락: {len(text_rows) - state_count}')
    if any(integer(r['seqno']) is None for r in text_rows):
        warnings.append('seqno 누락/형식 오류')
    if any(str(r['half_raw']) not in ('0', '1') for r in text_rows):
        warnings.append('초/말 코드가 0/1이 아님')
    if not pitches:
        warnings.append('ptsOptions 없음 (문자 수집 실패와는 별개)')
    if truthy(game.get('suspended')):
        warnings.append('RESULT이나 suspended 표시 있음: 재개 경기 원본 연결 수동 확인')
    result = {'game_id': gid, 'date': game['gameDate'], 'away': game.get('awayTeamName'),
              'home': game.get('homeTeamName'), 'away_score': game['awayTeamScore'],
              'home_score': game['homeTeamScore'], 'status': 'CHECK' if warnings else 'FETCHED',
              'last_inning': last, 'innings_with_text': len(innings), 'text_rows': len(text_rows),
              'rows_with_state': state_count, 'pitch_rows': len(pitches),
              'same_seq_groups': len(collisions), 'scoreboard_matches_schedule': score_match,
              'warnings': ' | '.join(dict.fromkeys(warnings)), 'failed_innings': failures,
              'checked_at_utc': stamp(), 'note': NOTE}
    derived = report_root / 'games' / gid
    write_jsonl(derived / 'text_rows.jsonl', text_rows)
    write_jsonl(derived / 'pitch_rows.jsonl', pitches)
    save_json(derived / 'seqno_collisions.json', collisions)
    save_text(derived / 'preview.txt', '\n'.join(
        f"{r['inning']}회{ {'0': '초', '1': '말'}.get(str(r['half_raw']), '?')} "
        f"[{r['seqno']}] {r['text']}" for r in text_rows) + '\n')
    # Hash identifies bytes checked, not baseball truth. Does not skip future audits.
    result['raw_files'] = [{'path': p.relative_to(root).as_posix(), 'bytes': p.stat().st_size,
                            'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in source_files]
    save_json(derived / 'check.json', result)
    return result


def summarize(root, inventory, reports, selected, scope, stopped, stats):
    counts = Counter(r['status'] for r in reports)
    full = (scope == 'full' and inventory['inventory_passed'] and not stopped
            and len(reports) == EXPECTED and counts['FETCHED'] == EXPECTED)
    run = {'updated_at_utc': stamp(), 'scope': scope, 'status': 'PASS' if full else 'INCOMPLETE',
           'inventory_passed': inventory['inventory_passed'], 'selected_games': selected,
           'reported_games': len(reports), 'status_counts': dict(counts),
           'stop_message': stopped, 'request_stats': dict(stats), 'note': NOTE}
    write_csv(root / 'summary.csv', reports, SUMMARY_FIELDS)
    write_csv(root / 'issues.csv', [r for r in reports if r['status'] != 'FETCHED'], SUMMARY_FIELDS)
    save_json(root / 'run_check.json', run)
    return run


def main(argv=None):
    parser = argparse.ArgumentParser(description='2026 정규시즌 전체 원본 수집/구조 점검')
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent / 'data',
                        help='기존 data 폴더. 원본 games 재사용, 결과는 season_2026 하위')
    parser.add_argument('--list-only', action='store_true', help='전체 시즌 경기 목록만 검사')
    parser.add_argument('--sample', type=int, help='목록 검사 후 앞 N경기만 시험 (전체 완료 아님)')
    parser.add_argument('--game-id', help='manifest에 있는 경기 하나만 점검 (전체 완료 아님)')
    parser.add_argument('--offline', action='store_true', help='네트워크 요청 없이 저장본만 검사')
    parser.add_argument('--refresh-schedules', action='store_true', help='전체 시즌 목록 캐시 갱신')
    parser.add_argument('--delay', type=float, default=2, help='새 요청 전 대기 초, 최소 1')
    parser.add_argument('--timeout', type=int, default=30)
    parser.add_argument('--attempts', type=int, default=3, help='일시적 통신 오류 최대 시도 1~3')
    args = parser.parse_args(argv)
    if not args.delay >= 1 or not args.delay <= 60 or not 5 <= args.timeout <= 120:
        parser.error('delay는 1~60초, timeout은 5~120초')
    if not 1 <= args.attempts <= 3:
        parser.error('attempts는 1~3')
    if args.sample is not None and not 1 <= args.sample <= EXPECTED:
        parser.error('sample은 1~720')
    if sum([args.list_only, args.sample is not None, bool(args.game_id)]) > 1:
        parser.error('list-only, sample, game-id는 하나만 선택')
    if args.offline and args.refresh_schedules:
        parser.error('offline과 refresh-schedules는 함께 사용 불가')
    if not args.offline:
        try:
            import curl_cffi  # noqa: F401
        except ImportError:
            parser.error('curl_cffi 미설치: py -m pip install -r requirements_season.txt')
    root = args.out.resolve()
    report_root = root / 'season_2026'
    report_root.mkdir(parents=True, exist_ok=True)
    # OS lock prevents two collectors from modifying the same cache simultaneously.
    lock_handle = (report_root / 'collector.lock').open('a+b')
    try:
        lock_handle.seek(0)
        if sys.platform == 'win32':
            import msvcrt
            if lock_handle.read(1) == b'':
                lock_handle.write(b'0')
                lock_handle.flush()
            lock_handle.seek(0)
            msvcrt.locking(lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock_handle.close()
        print('같은 data 폴더를 사용하는 다른 수집 프로그램이 실행 중입니다.', file=sys.stderr)
        return 1
    try:
        return run(args, root, report_root)
    finally:
        lock_handle.close()


def run(args, root, report_root):
    client = Client(root, args.delay, args.timeout, args.attempts, args.offline)
    games, inventory = schedule_inventory(client, report_root, args.refresh_schedules)
    print(f'목록: {len(games)}/720, 검사 통과={inventory["inventory_passed"]}', flush=True)
    if args.list_only or not inventory['inventory_passed']:
        # Does not replace full-run reports with a list-only report.
        print(f'목록 점검: {report_root / "inventory_check.json"}')
        if not inventory['inventory_passed']:
            print('전체 목록 검사가 통과하지 않아 중계를 수집하지 않았습니다. 오류를 확인하세요.')
        return 0 if inventory['inventory_passed'] else 1
    scope = 'full'
    if args.sample is not None:
        games, scope = games[:args.sample], 'sample'
    if args.game_id:
        games, scope = [g for g in games if g['gameId'] == args.game_id], 'single'
        if not games:
            print('해당 gameId가 이번 시즌 manifest에 없습니다.', file=sys.stderr)
            return 1
    # Trial runs do not replace the whole-season summary.
    run_root = report_root if scope == 'full' else report_root / ('trial_' + scope)
    reports, stopped = [], ''
    try:
        for index, game in enumerate(games, 1):
            gid = game['gameId']
            print(f'[{index}/{len(games)}] {gid} {game.get("awayTeamName")} vs {game.get("homeTeamName")}', flush=True)
            try:
                report = collect_game(game, root, report_root, client)
            except (StopCollection, KeyboardInterrupt) as exc:
                interrupted = {'game_id': gid, 'date': game['gameDate'],
                               'status': 'INTERRUPTED', 'warnings': str(exc) or '사용자 중단',
                               'checked_at_utc': stamp()}
                reports.append(interrupted)
                save_json(report_root / 'games' / gid / 'check.json', interrupted)
                raise
            except (ValueError, OSError, TypeError, KeyError) as exc:
                report = {'game_id': gid, 'date': game['gameDate'],
                          'status': 'ERROR', 'warnings': str(exc), 'checked_at_utc': stamp()}
                save_json(report_root / 'games' / gid / 'check.json', report)
            reports.append(report)
            summarize(run_root, inventory, reports, len(games), scope, '', client.stats)
            print(f'  {report["status"]}: {report.get("text_rows", 0)}행 {report.get("warnings", "")}', flush=True)
    except (StopCollection, KeyboardInterrupt) as exc:
        stopped = str(exc) or '사용자 중단'
        print(f'중단: {stopped}')
    finally:
        result = summarize(run_root, inventory, reports, len(games), scope, stopped, client.stats)
    print(f'결과: {run_root / "run_check.json"}')
    print(f'상태: {result["status"]}, 경기별 상태: {result["status_counts"]}')
    print(NOTE)
    if scope != 'full':
        print('시험 실행입니다. 전체 시즌 완료를 뜻하지 않습니다.')
    return 1 if stopped or any(r['status'] != 'FETCHED' for r in reports) else 0


if __name__ == '__main__':
    sys.exit(main())
