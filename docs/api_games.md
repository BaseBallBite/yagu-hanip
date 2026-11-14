# 경기·플레이 조회 API (B4)

프론트 경기 화면용. 2026 정규시즌 720경기의 플레이, 주자·아웃·점수 상태(B2), 플레이 사실 F(B3), 투구(B3)를 돌려준다.

## 서버 실행

```bash
# 1) DB 만들기 (처음 한 번, 약 2~3분). data/raw 에 B1 v2 · B3 v2 데이터가 있어야 함
.venv/bin/python -m backend.game.store build

# 2) 서버 실행 (저장소 루트에서)
.venv/bin/uvicorn backend.api.main:app --reload --port 8000
```

- 주소: `http://localhost:8000` · 자동 문서: `http://localhost:8000/docs`
- CORS: `http://localhost:3000` 허용 (vite 개발 서버)
- DB 파일 `data/db/yagu.sqlite` (약 500MB)는 git에 없다. `data/raw` 가 없으면 DB 파일을 받아서 `data/db/` 에 두거나 `YAGU_DB=경로` 로 지정한다.
- DB가 없으면 `/games` 요청은 503 과 안내 메시지를 돌려준다.

## 엔드포인트

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/games` | 경기 목록. `date=2026-03-28`, `team=KIA` 로 거르기 |
| GET | `/games/{game_id}` | 경기 정보 (팀, 최종 점수, 플레이 수) |
| GET | `/games/{game_id}/plays` | 플레이 목록 + 상태 전/후 |
| GET | `/games/{game_id}/plays/{seq}` | 플레이 1개 상세 (F, 투구 포함) |

`/plays` 옵션

| 파라미터 | 기본 | 설명 |
|---|---|---|
| `from_seq` | 1 | 이 순번부터 |
| `limit` | 전체 | 최대 개수 (최대 2000) |
| `event_type` | 전체 | 쉼표 구분: `single,double,home_run` |
| `facts` | false | F 목록 포함 |
| `pitch` | false | 투구 정보 포함 (구종, 구속, 존, 궤적, 볼·스트라이크 카운트) |

경기 하나 전체(약 600줄)는 옵션 없이 약 320KB, `facts=true&pitch=true` 면 약 600KB.

## 테스트용 game_id

| game_id | 경기 | 결과 |
|---|---|---|
| `20260328HTSK02026` | 3/28 KIA @ SSG | KIA 6-7 SSG (9회말) |
| `20260328KTLG02026` | 3/28 KT @ LG | KT 11-7 LG |

## 꼭 알아둘 점

- **`seq`** 는 경기 안 플레이 순번(1부터). 문자중계 한 줄 = 플레이 1개.
- **상태는 줄 단위다.** 타석 결과 줄(예: `single`) 바로 뒤에 `runner_advance`, `run_scored`, `runner_out` 줄이 따로 온다. 그래서 1루타 줄의 `state_after` 는 "타자가 1루에 나간 직후"이고, 주자 진루와 득점은 다음 줄들에서 반영된다. 화면에 "이 플레이가 끝난 뒤" 상황을 보여주려면 뒤따르는 주자 줄의 마지막 `state_after` 를 쓰면 된다 (F 목록의 "플레이 후 …" 문장이 이미 그렇게 계산되어 있음).
- `state.runners` 는 `{"1": 이름 또는 null, "2": …, "3": …}`, `score` 는 `{"away": n, "home": n}`.
- `half` 는 `top`(초) / `bottom`(말). `away` 가 원정, `home` 이 홈.
- `event_type` 목록: `pitch`, `batter_announcement`, `substitution`, `inning_start`, `single`, `double`, `triple`, `home_run`, `walk`, `strikeout`, `flyout`, `groundout`, `runner_advance`, `run_scored`, `runner_out`, `steal` 등.
- 투구 `zone` 단위는 피트(ft). `x_ft` 는 홈플레이트 가운데 기준 좌우, `height_ft` 는 높이, `top_ft`/`bottom_ft` 는 그 타자의 스트라이크존 위·아래. 존 좌우 끝은 약 ±0.83ft. `visualization_status` 가 `available` 인 공만 그리면 된다.
- `speed` 는 중계 화면 표기 그대로(km/h).
- 투구의 `plate_appearance_id` 가 같으면 같은 타석이다. 타석별 투구 목록은 이 값으로 묶는다.
- **볼·스트라이크 카운트**: 투구의 `count_before` 는 이 공을 던지기 전, `count_after` 는 던진 후 (`{"balls": 1, "strikes": 2}`). 화면의 "현재 카운트"는 마지막 공의 `count_after` 를 쓰면 된다. 볼넷·삼진이 된 공은 `count_after` 가 4볼 / 3스트라이크로 나온다. 타석 결과 줄(예: `single`)에는 투구가 없으니 그 타석 마지막 공의 `count_after` 를 쓴다.
  - 계산 규칙: 볼 +1, 스트라이크·헛스윙 +1, 파울은 2스트라이크 전까지만 +1, 번트파울은 항상 +1, 타격은 그대로. "포수 파울 플라이 포구 실책" 같은 줄은 앞 파울 공의 설명이라 카운트를 바꾸지 않는다.
  - 네이버 원본의 줄별 카운트와 대조: 221,661개 공 중 221,626개 일치. 다른 26개 중 24개는 5/13 NC–롯데 경기로, 원본 카운트가 투구 결과와 맞지 않고 한두 줄씩 밀려 있다. 이 경우 계산 값이 투구 결과와 맞다. 다시 확인: `.venv/bin/python -m backend.game.count verify`
- 경기의 `status` 는 "종료"가 아니라 **경기가 끝난 이닝**(예: `9회말`, `11회말`)이다. 720경기 모두 끝난 경기다.
- DB를 다시 만들면(`store build`) API 서버도 재시작해야 새 DB를 읽는다.
- **`type_tags`** (유형 태그): 이 플레이에 해당하는 경기 이벤트 유형. 이름은 `tools/event_types.txt` 60개(설명 `docs/event_types.md`)이고, 사전 API `/dict/events/{태그}` 로 그 장면의 카드를 바로 찾을 수 있다.
  - 타석 결과 줄은 뒤따르는 주자 줄의 유형까지 모은다. 예: 1루타 뒤 2루주자 진루·3루주자 홈인 → `["SINGLE", "ADVANCE", "SCORE"]`.
  - 주자 줄은 원인 하나만 붙는다: 폭투로 진루 → `WILD_PITCH`, 주자의 재치로 → `ADVANCE_ON_THROW`, 원인 없는 진루·득점 → `ADVANCE`·`SCORE`.
  - 교체 줄은 `PITCHING_CHANGE`, `PINCH_HITTER`, `PINCH_RUNNER`, `DEFENSIVE_SUB`, `POSITION_CHANGE` 중 하나. 마운드 방문 `MOUND_VISIT`, 체크스윙 판정 `CHECK_SWING_CALL`, 투수판 이탈 `PITCHER_STEP_OFF`, 피치클락 위반 투구 `PITCH_CLOCK_VIOLATION` 등 상황 메모에도 붙는다.
  - `TAG_UP` 은 원문 문구가 없어서, 희생플라이·플라이 아웃 뒤에 주자 진루·득점이 있으면 계산으로 붙인다.
  - 투구, 타자 소개, 이닝 시작 줄은 유형이 아니라서 빈 목록이다.

## 응답 예시

`GET /games/20260328HTSK02026`

```json
{"game_id": "20260328HTSK02026", "game_date": "2026-03-28", "start_time": "2026-03-28T14:00:00",
 "away": "KIA", "home": "SSG", "away_code": "HT", "home_code": "SK",
 "away_score": 6, "home_score": 7, "status": "9회말", "final_score_match": true, "play_count": 611}
```

`GET /games/20260328HTSK02026/plays?from_seq=27&limit=1&pitch=true`

```json
{"game_id": "20260328HTSK02026", "away": "KIA", "home": "SSG", "count": 1, "plays": [
 {"seq": 27, "play_id": "20260328HTSK02026:play:3cbeb5…", "inning": 1, "half": "top",
  "event_type": "pitch", "description": "3구 타격", "batter": "나성범", "pitcher": "화이트",
  "state_before": {"outs": 1, "runners": {"1": null, "2": "카스트로", "3": "김호령"},
                   "runner_count": {"1": 0, "2": 1, "3": 1}, "score": {"away": 0, "home": 0}},
  "state_after":  {"outs": 1, "runners": {"1": null, "2": "카스트로", "3": "김호령"},
                   "runner_count": {"1": 0, "2": 1, "3": 1}, "score": {"away": 0, "home": 0}},
  "type_tags": [],
  "pitch": {"pitch_number": 3, "pitch_type": "fastball", "pitch_type_raw": "직구", "speed": 150.0,
            "result_text": "타격", "result_code": "H", "visualization_status": "available",
            "plate_appearance_id": "20260328HTSK02026:pa:…",
            "count_before": {"balls": 1, "strikes": 1}, "count_after": {"balls": 1, "strikes": 1},
            "zone": {"x_ft": 0.797228, "height_ft": 2.711197, "top_ft": 3.344, "bottom_ft": 1.622},
            "trajectory": {"duration_s": 0.3806, "release_ft": [-1.65, 50.0, 5.93],
                           "velocity_ft_s": [9.16, -135.5, -6.10], "acceleration_ft_s2": [-14.3, 31.4, -12.4]}}}
]}
```

`GET /games/20260328HTSK02026/plays/28` (1회초 나성범 1루타)

```json
{"game_id": "20260328HTSK02026", "seq": 28, "event_type": "single",
 "description": "나성범 : 우익수 앞 1루타", "batter": "나성범", "pitcher": "화이트",
 "state_before": {"outs": 1, "runners": {"1": null, "2": "카스트로", "3": "김호령"}, "score": {"away": 0, "home": 0}, "…": "…"},
 "state_after":  {"outs": 1, "runners": {"1": "나성범", "2": "카스트로", "3": "김호령"}, "score": {"away": 0, "home": 0}, "…": "…"},
 "type_tags": ["SINGLE", "ADVANCE", "SCORE"],
 "facts": [
  {"id": "F1", "text": "1회초, 1사, 2,3루 (2루 카스트로, 3루 김호령), 점수 KIA 0-0 SSG"},
  {"id": "F2", "text": "타자 나성범, 투수 화이트"},
  {"id": "F3", "text": "기록: 나성범 : 우익수 앞 1루타"},
  {"id": "F4", "text": "주자 기록: 2루주자 카스트로 : 3루까지 진루"},
  {"id": "F5", "text": "주자 기록: 3루주자 김호령 : 홈인"},
  {"id": "F6", "text": "이 타석 투구 수 3개, 마지막 공: 3구 직구 150km/h 결과 타격"},
  {"id": "F7", "text": "플레이 후 1사, 1,3루 (1루 나성범, 3루 카스트로), 점수 KIA 1-0 SSG"},
  {"id": "F8", "text": "이 플레이로 득점: KIA 1점"}],
 "pitch": null}
```
