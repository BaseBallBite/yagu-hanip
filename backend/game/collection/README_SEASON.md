# 2026 KBO 정규시즌 720경기 데이터 사용 안내

2026년 KBO 정규시즌 전체 720경기의 네이버 문자중계 원본을 수집하고 기초 구조를 점검한 자료입니다.

경기 재생, AI 해설, 주자 이동 복원에 활용할 원본을 확보하는 단계입니다.
PlayEvent 정규화, 상태 전/후 의미 확인, 주자 이동 복원, 사실 F 생성은 후속 작업입니다.

## 1. 수집 완료 현황

확인일: 2026-11-04

| 항목 | 결과 |
|---|---|
| 수집 범위 | 2026년 KBO 정규시즌 |
| 경기 날짜 | 2026-03-28 ~ 2026-10-12 |
| 고유 경기 수 | 720경기 |
| 팀별 경기 수 | 10개 구단 모두 144경기 |
| 경기 목록 조회 | 대상 199일 모두 완료 |
| 목록 조회 오류 | 0개 |
| 목록 검토 항목 | 0개 |
| 전체 수집 상태 | PASS |
| 경기별 기초 검사 | 720경기 모두 FETCHED |

`FETCHED`는 수집 및 프로그램의 기초 검사에 통과했다는 뜻입니다.
경기의 모든 문자 기록, 주자 상태, 투구 좌표가 정확하다는 뜻은 아닙니다.

### 샘플 점검

다음 3경기의 문자 기록에서 이닝·순서·득점 일관성을 확인했습니다.

| 경기 | 최종 점수 | 종료 이닝 |
|---|---|---|
| 2026-03-28 KIA–SSG | KIA 6–7 SSG | 9회 |
| 2026-03-28 KT–LG | KT 11–7 LG | 9회 |
| 2026-03-28 키움–한화 | 키움 9–10 한화 | 11회 |

샘플 경기의 최종 점수·종료 이닝·주요 장면을 KBO 홈페이지 게시 기사와 외부 전적 자료로 대조했으며, 확인한 항목에서 불일치는 없었습니다.

대조 자료:

- KIA–SSG: https://www.koreabaseball.com/MediaNews/News/BreakingNews/View.aspx?bdSe=60524
- KT–LG: https://www.koreabaseball.com/MediaNews/News/BreakingNews/View.aspx?bdSe=60523
- 키움–한화: https://www.koreabaseball.com/MediaNews/News/BreakingNews/View.aspx?bdSe=60540
- 키움–한화 전적: https://www.yna.co.kr/view/AKR20260328046251007

720경기 전체의 세부 플레이를 공식 기록지와 대조한 것은 아닙니다.
주자 상태의 의미와 이동, 투구 좌표의 단위·부호도 아직 별도 검증이 필요합니다.

## 2. 데이터 받기

데이터 공유 위치는 팀 노션의 다음 페이지에서 확인합니다.

「1104 - 720경기 원본 수집 및 기초 점검」

해당 페이지의 ‘데이터 첨부’에 등록된 ZIP 파일 또는 다운로드 링크를 이용합니다.

압축 파일명:

`kbo_2026_regular_season_data.zip`

수집 코드와 관련 자료는 추후 팀 GitHub 저장소에 업로드할 예정입니다.
데이터 파일을 열어보는 데 수집 코드는 필요하지 않습니다.

### 압축 해제

1. ZIP 파일을 다운로드합니다.
2. 압축을 모두 풉니다.
3. 다음 두 폴더가 있는지 확인합니다.

- `data/games/`
- `data/season_2026/`

원본 및 파생 파일을 합친 `data` 폴더의 크기는 공유 준비 당시 약 4.86GB입니다.
ZIP 크기는 압축 후 달라질 수 있으며, 압축 해제할 공간도 필요합니다.

데이터를 읽기 위해 수집 명령을 다시 실행할 필요는 없습니다.
JSON·JSONL·CSV·TXT 파일을 확인하는 것만으로는 Python 패키지 설치도 필요하지 않습니다.

`--out` 옵션을 사용하지 않는 경우, `fetch_season.py`와 같은 폴더 아래에 `data` 폴더를 배치합니다. 기존 데이터가 다른 위치에 있다면 8번의 `--out` 사용 방법을 참고합니다.

`data/data/`처럼 중복된 폴더 구조가 되지 않도록 확인합니다.

## 3. 처음 확인할 파일

| 목적 | 파일 |
|---|---|
| 720경기 목록·날짜·대진·최종 점수 확인 | `data/season_2026/game_index.csv` |
| 경기별 수집·기초 점검 상태 확인 | `data/season_2026/summary.csv` |
| 전체 실행 결과 확인 | `data/season_2026/run_check.json` |
| 팀별 144경기 확인 | `data/season_2026/team_counts.csv` |
| 경기 문자중계를 읽기 쉽게 확인 | `data/season_2026/games/경기ID/preview.txt` |
| 문자행과 원본 상태 정보 확인 | `data/season_2026/games/경기ID/text_rows.jsonl` |
| 투구 정보 확인 | `data/season_2026/games/경기ID/pitch_rows.jsonl` |
| 이닝별 API 원본 확인 | `data/games/경기ID/inning_01.json` 등 |

예를 들어 2026년 3월 28일 KIA–SSG 경기를 확인하려면 다음 파일을 엽니다.

`data/season_2026/games/20260328HTSK02026/preview.txt`

경기별 원본 JSON은 다음 폴더에 있습니다.

`data/games/20260328HTSK02026/`

## 4. 전체 데이터 구성

| 경로 | 용도 |
|---|---|
| `data/games/경기ID/relay_latest.json` | 기본 문자중계 응답 원본 |
| `data/games/경기ID/inning_01.json` 등 | 이닝별 API 응답 원본 |
| `data/games/경기ID/game.json` | 최초 저장 경기 정보. 기존 파일은 보존 |
| `data/season_2026/manifest.json` | 이번 시즌 목록에서 확인한 경기 전체 메타데이터 |
| `data/season_2026/game_index.csv` | 경기 ID·날짜·대진·최종 점수 |
| `data/season_2026/team_counts.csv` | 팀별 경기 수 |
| `data/season_2026/inventory_check.json` | 목록 검사 및 제외·검토·조회 실패 결과 |
| `data/season_2026/schedules/` | 날짜별 경기 목록 원본 |
| `data/season_2026/summary.csv` | 전체 실행의 경기별 기초 점검표 |
| `data/season_2026/issues.csv` | FETCHED가 아닌 경기 목록 |
| `data/season_2026/run_check.json` | 전체 실행 상태와 완료 조건 검사 |
| `data/season_2026/games/경기ID/text_rows.jsonl` | 문자행 원본 필드와 원본 위치 |
| `data/season_2026/games/경기ID/pitch_rows.jsonl` | 투구 항목 원본 필드와 원본 위치 |
| `data/season_2026/games/경기ID/seqno_collisions.json` | 동일 seqno가 여러 번 등장한 사례 |
| `data/season_2026/games/경기ID/preview.txt` | 사람이 읽기 위한 문자중계 목록 |
| `data/season_2026/games/경기ID/check.json` | 경기별 검사·경고·원본 파일 크기·SHA-256 |

JSONL은 한 줄마다 JSON 객체 하나가 저장되는 형식입니다.

`relay_latest.json`에는 마지막 이닝만 포함될 수 있으므로 이 파일 하나로 전체 경기 내용을 판단하지 않습니다.

기존 `data/summary.csv`와 `data/run_check.json`은 이전 소규모 수집 결과입니다.
720경기의 결과는 반드시 `data/season_2026/` 안에서 확인합니다.

기존 경기 폴더에는 예전 수집기가 만든 CSV·미리보기 파일이 남아 있을 수 있습니다.
전체 시즌 수집기의 파생 파일은 `data/season_2026/games/` 아래에 있습니다.

최신 시즌 목록의 경기 정보는 `manifest.json`과 `game_index.csv`를 참고합니다.

## 5. 현재 데이터의 범위와 한계

API 원본 응답에 제공된 정보는 통째로 저장합니다.
문자중계, `currentGameState`, 선수·라인업·기록·투구 정보가 제공되면 원본에 그대로 남습니다.

제공되지 않은 값은 추정하거나 채우지 않습니다.
모든 경기에서 동일한 필드가 제공된다고 보장하지 않습니다.

이번 작업에 포함하지 않은 내용:

- PlayEvent 정규화
- 정정·재전송·별개 이벤트의 의미 판정
- 상태 정보가 플레이 직전인지 직후인지 판정
- 주자 신원 및 이동 복원
- 플레이 사실 F 생성
- AI 해설 생성
- DB 및 API 서버 구현

원본 데이터는 보존하고, 정규화 결과는 별도로 관리합니다.

## 6. 정규화 및 AI 사용 시 주의사항

### 동일 seqno

같은 `seqno`에 서로 다른 문자 내용이 존재할 수 있습니다.
`seqno`만을 기준으로 중복을 제거하면 정상 기록이 사라질 수 있습니다.

전체 시즌 수집기는 동일 `seqno`라는 이유로 문자행을 삭제하지 않습니다.
`text_rows.jsonl`의 `raw`에 원본 문자 항목을 보존합니다.

`source_file`, `block_index`, `item_index`는 원본 위치를 찾기 위한 정보입니다.
`source_ref`는 현재 저장본의 위치 식별자이며, 원본 갱신 후에도 영구적으로 유지되는 플레이 ID는 아닙니다.

표시 순서는 열람을 돕기 위한 순서입니다.
정정·재전송 의미 판정이 끝난 정규화 순서는 아닙니다.

### 상태 정보

- `currentGameState`가 문자행의 직전 상태인지 직후 상태인지 확인해야 합니다.
- `base1`, `base2`, `base3`을 의미 확인 없이 선수 ID로 해석하지 않습니다.
- 상태 정보의 존재 여부와 상태 값의 정확성은 별개입니다.
- 끝내기·미실시 반이닝·정정·재개 상황은 별도 처리가 필요합니다.

### 투구 정보

구종·구속이 `textOptions`에, 좌표·궤적 계수가 `ptsOptions`에 나뉘어 있을 수 있습니다.
두 원본을 함께 보존합니다.

투구 식별자의 연결 관계, 좌표 단위와 부호를 확인하지 않고 합치거나 변환하지 않습니다.
투구 항목 개수는 모든 투구 좌표가 유효하다는 뜻이 아닙니다.

### 점검 결과 해석

이닝별 점수 합계와 경기 목록의 최종 점수 비교는 같은 네이버 데이터 안의 대조입니다.
주자 상태를 계산해 최종 점수를 복원한 검증은 아닙니다.

문자중계 한 행이 반드시 한 투구나 한 타석을 뜻하지 않습니다.
현재 파일을 완성된 PlayEvent나 사실 F로 간주하지 않습니다.

## 7. 수집 기준

- 기간: 2026-03-28 ~ 2026-10-12
- 대상: KBO 10개 구단 정규시즌 경기
- 기대 규모: 고유 경기 720개, 팀별 참가 경기 144개

공식 일정 근거:

- 개막 및 경기 수: https://www.koreabaseball.com/MediaNews/Notice/View.aspx?bdSe=11794
- 정규시즌 종료 발표: https://www.koreabaseball.com/MediaNews/Notice/View.aspx?bdSe=12189

경기 선택 기준은 날짜, `categoryId=kbo`, 10개 구단 코드, 종료 상태 `RESULT`, 취소 아님, 최종 점수 존재입니다.

올스타 등 다른 팀 코드의 경기는 제외하고 사유를 기록합니다.
종료 상태가 아닌 구단 경기는 검토 항목으로 남깁니다.
종료 상태인데 `suspended` 표시가 남은 경기는 포함하되 `CHECK`로 표시합니다.

720경기·팀별 144경기 검사는 경기 수 확인용 보조 검사이며, 경기별 공식 ID 대조를 대신하지 않습니다.

이 프로그램은 2026년 일정에 맞춰져 있으므로 다른 시즌에 그대로 사용하지 않습니다.

## 8. 수집 코드 실행 안내

이하 내용은 수집 코드를 직접 실행하거나 유지보수할 때 참고합니다.

이미 전달받은 데이터를 사용하는 팀원은 수집 코드를 다시 실행할 필요가 없습니다.

### 실행 환경

- Python 3.10 이상
- 외부 패키지: `curl_cffi`
- 실제 수집 환경: Windows, VS Code, Python 3.13.3

FastAPI, Rust, kbotop 실행파일, Gemini API 키는 필요하지 않습니다.

### 필요한 파일

- `fetch_season.py`
- `requirements_season.txt`

기존 소규모 수집용 `fetch_games.py`와 별개로 실행합니다.

`fetch_games.py`의 `--start`, `--end`, `--limit` 옵션을 `fetch_season.py`에 사용하지 않습니다.

### GitHub 코드 및 데이터 경로

수집 코드는 팀 GitHub 저장소의 다음 위치에서 관리합니다.

```text
backend/data_pipeline/season/
├── fetch_season.py
├── fetch_games.py
├── recheck_missing_inning.py
├── test_recheck_missing_inning.py
├── requirements_season.txt
└── README_SEASON.md
```

GitHub에는 수집 코드와 설명서를 업로드하며, 720경기 원본 데이터는 팀 노션에서 별도로 공유합니다.

`fetch_season.py`는 기본적으로 코드 파일과 같은 폴더의 `data/`를 사용합니다.

기존 데이터가 다른 위치에 있다면 `--out` 옵션으로 데이터 폴더 경로를 지정할 수 있습니다.

**실행 예시 (팀 GitHub 저장소 최상위 폴더 기준)**

```powershell
py .\backend\data_pipeline\season\fetch_season.py --out "C:\path\to\naver_relay_starter\data" --offline --list-only
```

- `--out`: 기존 데이터 폴더 경로 지정
- `--offline`: 새 API 요청 없이 저장된 응답 사용
- `--list-only`: 정규시즌 경기 목록 점검

위 데이터 경로는 예시이므로 실제 압축 해제한 `data` 폴더의 경로로 변경해야 합니다.

데이터 폴더에는 다음 구조가 있어야 합니다.

```text
data/
├── games/
└── season_2026/
```

오프라인 목록 점검에는 `season_2026/schedules/`의 기존 일정 응답 파일도 필요합니다.

ZIP 압축파일 자체가 아니라 압축 해제된 `data` 폴더를 지정해야 합니다.

**주의:** 오프라인 점검도 일부 목록 및 검증 파일을 갱신할 수 있으므로, 기존 결과를 그대로 보존해야 한다면 데이터 폴더를 복사한 뒤 실행합니다.

기존 720경기 데이터를 재수집할 필요는 없습니다.

### 패키지 설치

`requirements_season.txt` 내용:

```text
curl_cffi
```

아래 기본 실행 명령어는 VS Code에서 `backend/data_pipeline/season/` 폴더를 열고 터미널을 실행한 경우를 기준으로 합니다.

```powershell
py --version
Get-Location
Get-ChildItem
py -m pip install -r requirements_season.txt
```

팀 GitHub 저장소의 최상위 폴더에서 패키지를 설치한다면 다음 명령어를 사용합니다.

```powershell
py -m pip install -r .\backend\data_pipeline\season\requirements_season.txt
```

`py` 대신 `python`을 사용하는 환경에서는 명령어의 `py`를 `python`으로 바꿉니다.

바탕화면의 작업 폴더와 복제한 GitHub 저장소 폴더는 자동으로 동기화되지 않습니다.

프로그램을 실행하는 것만으로 GitHub에 코드가 업로드되지는 않습니다.

## 9. 경기 목록 점검

```powershell
py fetch_season.py --list-only
```

시작·종료 날짜와 경기 수 기준은 프로그램에 들어 있습니다.

각 날짜의 경기 목록을 조회하고 성공한 응답을 저장합니다.
휴식일의 정상적인 빈 목록과 요청 실패를 구분합니다.

넓은 날짜 범위를 한 번에 요청하면 목록이 잘릴 수 있으므로 날짜별로 요청합니다.
`gameTotalCount`와 실제 반환된 목록 길이도 비교합니다.

결과 확인:

```powershell
Get-Content .\data\season_2026\inventory_check.json -Raw -Encoding UTF8
Import-Csv .\data\season_2026\team_counts.csv | Format-Table
```

전체 수집 진행 조건:

- `inventory_passed`: `true`
- `selected_games`: `720`
- `checked_days`와 `expected_days`: 동일
- 각 팀의 `games`: `144`
- `schedule_errors`, `review_items`: 빈 배열
- `stop_message`: 빈 문자열

조건을 충족하지 않으면 전체 수집을 시작하지 않습니다.
숫자를 강제로 맞추거나 검사를 삭제하지 말고 오류·검토 항목을 확인합니다.

## 10. 한 경기 시험 및 전체 수집

### 한 경기 시험

```powershell
py fetch_season.py --game-id 20260719HTSK02026
```

정상적인 기존 원본은 재사용합니다.

시험 결과:

`data/season_2026/trial_single/run_check.json`

한 경기 시험은 전체 시즌 수집이 아니므로 전체 완료 상태인 `PASS`가 되지 않는 것이 정상입니다.
`status_counts`와 해당 경기의 경고를 확인합니다.

### 전체 수집

```powershell
py fetch_season.py
```

목록을 점검한 뒤 전체 720경기를 처리합니다.
기존의 유효한 원본은 재사용합니다.

- 새 요청마다 기본 2초 대기
- 기본 요청 타임아웃 30초
- 병렬 요청 없음
- 같은 데이터 폴더에 대해 여러 수집기를 동시에 실행하지 않음
- 기존 `fetch_games.py`도 동시에 실행하지 않음

전체 수집에는 수 시간이 걸릴 수 있습니다.
실제 시간은 저장본 수, 네트워크 상태, 재시도 횟수에 따라 달라집니다.

컴퓨터가 절전 상태로 들어가지 않도록 합니다.
중단하려면 `Ctrl+C`를 한 번 누르고 저장·종료 메시지를 기다립니다.

## 11. 중단 또는 오류 후 이어받기

같은 명령을 다시 실행합니다.

```powershell
py fetch_season.py
```

이미 저장된 원본은 검사 후 재사용합니다.
누락되거나 손상된 저장본은 다시 요청합니다.

- 일시적인 타임아웃·서버 오류: 최대 3회까지 간격을 늘려 시도
- 손상된 기존 파일: `.invalid-숫자` 이름으로 보존
- 구조가 잘못된 새 응답: `.rejected-숫자.txt`로 보존
- HTTP/API 코드 401·403·429: 자동 재시도 없이 전체 수집 중단

접근·요청 제한이 발생하면 즉시 반복 실행하거나 우회하지 말고 접근 가능 여부를 확인합니다.

점수 불일치 등 내용 검사에서 `CHECK`가 된 정상 형식의 응답은 재실행만으로 바뀌지 않을 수 있습니다.
원본을 삭제하지 말고 `issues.csv`와 해당 경기의 `check.json`을 먼저 확인합니다.

목록 캐시를 갱신할 필요가 있을 때만 사용합니다.

```powershell
py fetch_season.py --list-only --refresh-schedules
```

## 12. 전체 결과 확인

```powershell
Get-Content .\data\season_2026\run_check.json -Raw -Encoding UTF8
Import-Csv .\data\season_2026\summary.csv | Group-Object status | Select-Object Name,Count
Import-Csv .\data\season_2026\issues.csv | Format-Table game_id,status,warnings -Wrap
```

주요 성공 조건 예시:

```json
{
  "scope": "full",
  "status": "PASS",
  "inventory_passed": true,
  "selected_games": 720,
  "reported_games": 720,
  "status_counts": {
    "FETCHED": 720
  },
  "stop_message": ""
}
```

위 JSON은 주요 항목만 표시한 예시입니다.
실제 파일에는 실행 시각·통신 횟수 등의 추가 항목이 있습니다.
최신 `inventory_check.json`도 함께 확인합니다.

### 상태 의미

| 상태 | 의미 |
|---|---|
| FETCHED | 해당 경기 수집 및 기초 검사 통과 |
| CHECK | 원본은 있으나 추가 확인 필요 |
| ERROR | 경기 처리 실패 |
| INTERRUPTED | 처리 도중 중단 |
| PASS | 전체 실행의 완료 조건 충족 |
| INCOMPLETE | 전체 완료 조건 미충족. 일부 경기 시험 실행도 포함 |

`CHECK`를 일괄적으로 `FETCHED`로 바꾸지 않습니다.
문자중계 요청 실패와 투구 자료 미제공 등은 원인이 다르므로 경고를 구분해서 확인합니다.

### 오프라인 재검사

필요한 경우 네트워크 요청 없이 저장된 파일을 검사할 수 있습니다.

```powershell
py fetch_season.py --offline
```

이 명령도 점검표와 파생 파일을 갱신할 수 있습니다.
같은 코드의 검사를 반복하는 것이므로 독립적인 야구 내용 검증은 아닙니다.

한 경기 시험은 전체 실행의 요약 점검표를 덮어쓰지 않습니다.

## 13. 문제를 공유할 때

다음 자료를 먼저 확인합니다.

- `data/season_2026/inventory_check.json`
- `data/season_2026/run_check.json`
- `data/season_2026/issues.csv`
- 문제가 있는 경기의 `data/season_2026/games/경기ID/check.json`

전체 원본을 삭제하거나 경기 수를 강제로 720개로 맞추지 않습니다.
오류를 공유할 때 API 키·토큰·쿠키·비밀번호는 포함하지 않습니다.

## 14. 코드 테스트 및 수집 결과 확인

### 누락 이닝 점검 코드 테스트

`test_recheck_missing_inning.py`는 `recheck_missing_inning.py`의 동작을 확인하는 테스트 코드입니다.

동일 응답 비교, 첫 타석 복구 후보 식별, 기존 원본 보존, 접근 제한 시 요청 중단 등을 테스트합니다.

VS Code에서 수집 코드가 있는 폴더를 열고 다음 명령어를 실행합니다.

```powershell
py -m unittest test_recheck_missing_inning -v
```

이 테스트는 임시 데이터와 가짜 응답을 사용하므로 네이버 API에 직접 요청하거나 기존 720경기 원본을 변경하지 않습니다.

해당 테스트는 **누락 이닝 재점검 기능을 검증하는 것으로, 전체 720경기 수집 기능을 검증하는 테스트는 아닙니다.**

### 720경기 수집 결과 확인

전체 정규시즌 수집 결과는 다음 파일에서 확인할 수 있습니다.

- `data/season_2026/inventory_check.json`: 전체 경기 목록과 팀별 경기 수 점검
- `data/season_2026/run_check.json`: 전체 수집 완료 상태
- `data/season_2026/summary.csv`: 720경기 개별 수집·검사 결과
- `data/season_2026/issues.csv`: 추가 확인이 필요한 경기 목록

기존 수집 결과에서는 720경기 모두 `FETCHED`, 전체 상태 `PASS`, 10개 구단 각각 144경기를 확인했습니다.

이 결과는 원본 수집 및 기초 구조 점검의 완료를 의미하며, 모든 문자중계·주자 상태·투구 좌표의 실제 정확성을 보장하지는 않습니다.

상세 작업 결과와 데이터 공유 위치는 팀 노션의 「1104 - 720경기 원본 수집 및 기초 점검」 페이지를 참고합니다.

## 15. 보관 및 공유 원칙

- 원본과 파생 데이터는 팀 내부 개발·확인용으로 공유합니다.
- 노션 첨부 또는 연결된 저장 공간의 접근 권한은 팀원으로 제한합니다.
- 원본 데이터와 전체 ZIP 파일은 공개 저장소에 올리지 않습니다.
- 공유 후에도 로컬 원본을 보관합니다.
- 정규화 결과는 원본과 별도로 관리합니다.
- 수집 코드·설명서·요약 점검 결과는 추후 팀 GitHub 저장소에 공유합니다.

## 16. 출처

참고 저장소:

https://github.com/wantaekchoi/kbotop

참고 소스:

- `src/source/naver/mod.rs`
- `src/source/naver/dto.rs`

참고 커밋:

`3c941452fcd8b2b5590003c466719fdb8fcc2ccc`

수집 경로:

- `/schedule/games?...fromDate=...&toDate=...`
- `/schedule/games/{game_id}/relay`
- `/schedule/games/{game_id}/relay?inning=N`

네이버 비공식 엔드포인트를 사용하므로 응답 구조와 접근 가능 여부가 변경될 수 있습니다.