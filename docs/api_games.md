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
| `pitch` | false | 투구 정보 포함 (구종, 구속, 존, 궤적) |

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
 "type_tags": ["SINGLE"],
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
