#!/usr/bin/env python3
"""KBO 문자중계 수집·구조 점검. Python 3.10+, curl_cffi 필요.

참고: https://github.com/wantaekchoi/kbotop
확인한 커밋: 3c941452fcd8b2b5590003c466719fdb8fcc2ccc
src/source/naver/mod.rs의 요청 경로를 참고한 별도 Python 구현.
원본 상태의 의미/주자 이동을 추론하거나 PlayEvent를 완성하는 코드는 아님.
"""
import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

BASE = 'https://api-gw.sports.naver.com'
DEFAULT_OUT = Path(__file__).resolve().parent / 'data'


class StopCollection(Exception):
    pass


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)


def fetch(url, path):
    import curl_cffi

    # 이미 저장한 응답은 다시 사용
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))

    time.sleep(1)
    print(f'  요청 중: {path.name}', flush=True)

    try:
        response = curl_cffi.get(
            url,
            impersonate='chrome',
            timeout=30,
        )
    except Exception as exc:
        print(f'  연결 실패: {exc}', flush=True)
        raise OSError(f'데이터 요청 실패: {exc}') from exc

    print(f'  HTTP {response.status_code}', flush=True)

    if response.status_code in (401, 403, 429):
        raise StopCollection(
            f'HTTP {response.status_code}: 접근/요청 제한으로 중단합니다.'
        )

    if response.status_code != 200:
        raise OSError(f'HTTP 오류: {response.status_code}')

    try:
        data = response.json()
    except ValueError as exc:
        raise ValueError(
            'JSON 형식이 아닌 응답을 받았습니다.'
        ) from exc

    if not isinstance(data, dict) or data.get('success') is False:
        raise ValueError('API가 실패 응답을 반환했습니다.')

    save_json(path, data)
    return data


def relay_data(payload):
    result = payload.get('result')
    if not isinstance(result, dict):
        raise ValueError('result 객체가 없습니다. 응답 형식을 확인하세요.')
    data = result.get('textRelayData')
    if not isinstance(data, dict):
        raise ValueError('textRelayData가 없습니다. 문자중계 미제공 또는 형식 변경 가능.')
    relays = data.get('textRelays')
    if not isinstance(relays, list):
        raise ValueError('textRelays 배열이 없습니다.')
    return data


def number(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def final_inning(data, game):
    # 종료된 경기만 처리. score의 '-'는 미실시 반이닝이므로 제외.
    candidates = []
    n = number(data.get('inn'))
    if n:
        candidates.append(n)
    for row in data.get('textRelays') or []:
        n = number(row.get('inn'))
        if n:
            candidates.append(n)
    score = data.get('inningScore') or {}
    for side in ('home', 'away'):
        for key, value in (score.get(side) or {}).items():
            n = number(key)
            if n and value is not None and str(value).strip() not in ('', '-'):
                candidates.append(n)
    match = re.search(r'(\d+)회', str(game.get('statusInfo', '')))
    if match:
        candidates.append(int(match.group(1)))
    if not candidates or not 1 <= max(candidates) <= 30:
        raise ValueError('마지막 이닝을 확인할 수 없습니다. 원본을 직접 점검하세요.')
    return max(candidates)


def flatten(relays):
    """검사용 문자중계 행. currentGameState를 직전/직후로 해석하지 않음."""
    output, seen, duplicates = [], set(), 0
    for relay in relays:
        for index, item in enumerate(relay.get('textOptions') or []):
            key = (str(relay.get('inn')), str(relay.get('homeOrAway')),
                   str(relay.get('no')), str(item.get('seqno')), str(item.get('text')))
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            state = item.get('currentGameState')
            state = state if isinstance(state, dict) else {}
            output.append({
                'inning': relay.get('inn'), 'half_raw': relay.get('homeOrAway'),
                'relay_no': relay.get('no'), 'seqno': item.get('seqno'),
                'text': item.get('text', ''), 'type': item.get('type'),
                'ptsPitchId': item.get('ptsPitchId'),
                'has_line_state': bool(state),
                'homeScore': state.get('homeScore'), 'awayScore': state.get('awayScore'),
                'out': state.get('out'), 'ball': state.get('ball'),
                'strike': state.get('strike'), 'base1': state.get('base1'),
                'base2': state.get('base2'), 'base3': state.get('base3'),
                'batter': state.get('batter'), 'pitcher': state.get('pitcher'),
                '_source_index': index,
            })
    output.sort(key=lambda r: (number(r['inning']) or 0, number(r['half_raw']) or 0,
                              number(r['relay_no']) or 0,
                              number(r['seqno']) if number(r['seqno']) is not None else r['_source_index']))
    for row in output:
        row.pop('_source_index')
    return output, duplicates


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def collect_game(game, out):
    gid = str(game.get('gameId', ''))
    if not re.fullmatch(r'[A-Za-z0-9_-]+', gid):
        raise ValueError('유효하지 않은 gameId')
    folder = out / 'games' / gid
    save_json(folder / 'game.json', game)
    url = f'{BASE}/schedule/games/{urllib.parse.quote(gid, safe="")}/relay'
    latest = relay_data(fetch(url, folder / 'relay_latest.json'))
    last = final_inning(latest, game)
    relays, missing, errors, wrong = [], [], [], []
    for inning in range(1, last + 1):
        print(f'    {inning}/{last}회 조회', flush=True)
        try:
            data = relay_data(fetch(f'{url}?inning={inning}', folder / f'inning_{inning:02d}.json'))
            all_rows = data['textRelays']
            matching = [row for row in all_rows if number(row.get('inn')) == inning]
            if len(matching) != len(all_rows):
                wrong.append(inning)
            if not matching or not any(r.get('textOptions') for r in matching):
                missing.append(inning)
            relays.extend(matching)
        except StopCollection:
            raise
        except (ValueError, OSError, urllib.error.URLError) as exc:
            errors.append(f'{inning}회: {exc}')
    rows, duplicates = flatten(relays)
    state_count = sum(bool(row['has_line_state']) for row in rows)
    pitch_count = sum(len(r.get('ptsOptions') or []) for r in relays)
    warnings = []
    if missing:
        warnings.append(f'빈 이닝={missing}')
    if wrong:
        warnings.append(f'요청과 다른 이닝 포함={wrong}')
    warnings.extend(errors)
    if duplicates:
        warnings.append(f'동일 문자행 중복={duplicates}')
    if rows and state_count != len(rows):
        warnings.append(f'행별 상태 누락={len(rows) - state_count}')
    if not pitch_count:
        warnings.append('투구 좌표 자료 없음')
    if not rows:
        warnings.append('문자중계 행 없음')
    if any(number(r['seqno']) is None for r in rows):
        warnings.append('seqno 누락: 정렬 수동 확인 필요')
    report = {
        'game_id': gid, 'date': game.get('gameDate'),
        'away': game.get('awayTeamName'), 'home': game.get('homeTeamName'),
        'status': 'CHECK' if warnings else 'FETCHED',
        'last_inning': last, 'innings_with_text': len(set(r['inning'] for r in rows)),
        'text_rows': len(rows), 'rows_with_state': state_count,
        'pitch_rows': pitch_count, 'warnings': ' | '.join(warnings),
    }
    save_json(folder / 'check.json', report)
    save_json(folder / 'relay_blocks.json', relays)
    # 고정 헤더를 남겨 빈 데이터도 빈 CSV로 식별 가능.
    fields = list(rows[0]) if rows else ['inning', 'half_raw', 'relay_no', 'seqno', 'text']
    write_csv(folder / 'text_rows.csv', rows, fields)
    (folder / 'preview.txt').write_text('\n'.join(
        f"{r['inning']}회{'초' if str(r['half_raw']) == '0' else '말'} "
        f"[{r['seqno']}] {r['text']}" for r in rows), encoding='utf-8')
    return report


def truthy(value):
    return str(value).lower() in ('true', '1', 'y', 'yes')


def main():
    parser = argparse.ArgumentParser(description='종료된 KBO 경기 최대 50개 수집·점검')
    parser.add_argument('--start', required=True, help='시작일 YYYY-MM-DD')
    parser.add_argument('--end', required=True, help='종료일 YYYY-MM-DD')
    parser.add_argument('--limit', type=int, default=1, help='한 번에 확인할 경기 수 1~50, 기본 1')
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    try:
        start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    except ValueError:
        parser.error('날짜는 YYYY-MM-DD 형식이어야 합니다.')
    if start > end or (end - start).days > 366:
        parser.error('날짜는 순서대로 입력하고 조회 범위는 366일 이내로 지정하세요.')
    if not 1 <= args.limit <= 50:
        parser.error('--limit은 1~50이어야 합니다.')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    reports, seen, schedule_errors = [], set(), []
    stop_message = ''
    try:
        day = start
        while day <= end and len(seen) < args.limit:
            daystr = day.isoformat()
            print(f'경기 목록: {daystr}', flush=True)
            params = urllib.parse.urlencode({
                'fields': 'basic', 'upperCategoryId': 'kbaseball', 'categoryId': 'kbo',
                'fromDate': daystr, 'toDate': daystr,
            })
            try:
                payload = fetch(f'{BASE}/schedule/games?{params}', out / 'schedules' / f'{daystr}.json')
                games = (payload.get('result') or {}).get('games')
                if not isinstance(games, list):
                    raise ValueError('games 배열이 없습니다.')
                total = number((payload.get('result') or {}).get('gameTotalCount'))
                if total is not None and total > len(games):
                    schedule_errors.append(f'{daystr}: 목록 일부만 반환됨({len(games)}/{total})')
            except StopCollection:
                raise
            except (ValueError, OSError, urllib.error.URLError) as exc:
                schedule_errors.append(f'{daystr}: {exc}')
                games = []
            for game in games:
                if (game.get('statusCode') != 'RESULT' or truthy(game.get('cancel'))
                        or truthy(game.get('suspended'))):
                    continue
                gid = str(game.get('gameId', ''))
                if not gid or gid in seen:
                    continue
                seen.add(gid)
                print(f'[{len(seen)}/{args.limit}] {gid} {game.get("awayTeamName")} vs {game.get("homeTeamName")}', flush=True)
                try:
                    report = collect_game(game, out)
                except (StopCollection, KeyboardInterrupt) as exc:
                    reports.append({'game_id': gid, 'status': 'INTERRUPTED', 'warnings': str(exc) or '사용자 중단'})
                    raise
                except (ValueError, OSError, urllib.error.URLError) as exc:
                    report = {'game_id': gid, 'status': 'ERROR', 'warnings': str(exc)}
                reports.append(report)
                print(f'  {report["status"]}: 문자 {report.get("text_rows", 0)}행 / {report.get("warnings", "")}', flush=True)
                if len(seen) >= args.limit:
                    break
            day += timedelta(days=1)
    except (StopCollection, KeyboardInterrupt) as exc:
        stop_message = str(exc) or '사용자 중단'
        print(f'중단: {stop_message}')
    finally:
        fields = ['game_id', 'date', 'away', 'home', 'status', 'last_inning',
                  'innings_with_text', 'text_rows', 'rows_with_state', 'pitch_rows', 'warnings']
        write_csv(out / 'summary.csv', reports, fields)
        save_json(out / 'run_check.json', {
            'start': args.start, 'end': args.end, 'limit': args.limit,
            'selected_games': len(seen), 'reported_games': len(reports),
            'schedule_errors': schedule_errors, 'stop_message': stop_message,
            'note': 'FETCHED는 수집·기초 구조 검사 통과. 경기 완전성·주자 복원 정확성 보장 아님.',
        })
    print(f'점검표: {out / "summary.csv"}')
    print('FETCHED도 경기 초반/중반/마지막과 원본 상태의 의미를 수동 확인하세요.')
    return 1 if stop_message or schedule_errors or not reports or any(r['status'] != 'FETCHED' for r in reports) else 0


if __name__ == '__main__':
    sys.exit(main())
