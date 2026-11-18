# 하이라이트 장면 조회 API (B12 영상매칭)

하이라이트 영상의 재생 시간으로 "지금 이 장면은 몇 회 몇 사, 주자·점수가 어떤지"를 돌려준다. 프론트는 영상 옆에 상황 카드를 띄우면 된다.

장면 표는 AI 쪽(`ai/highlight`)이 영상을 미리 분석해 만든 JSON이다. 백엔드는 이걸 SQLite에 넣어 조회만 한다. AI 호출은 없다.

## 서버 실행

```bash
.venv/bin/uvicorn backend.api.main:app --reload --port 8000
```

- 하이라이트 DB(`data/db/highlights.sqlite`)는 git에 없지만, 장면 표가 git에 있어서 **첫 요청 때 자동으로 만든다** (1초 미만). `/games` 용 큰 DB는 필요 없다.
- 장면 표가 바뀌면 DB를 다시 만든다: `.venv/bin/python -m backend.highlight.store build` (또는 `data/db/highlights.sqlite` 를 지우고 서버 재시작)
- 명령줄 확인: `.venv/bin/python -m backend.highlight.store scene YQD3hMI2LPo 757.3`

## 들어 있는 영상

`ai/highlight/games.csv` 에서 용도가 `demo` 인 경기만 넣는다. **평가용(eval) 경기는 넣지 않는다** (시연·화면 테스트에 쓰면 평가가 오염됨).

| video_id | game_id | 경기 | 비고 |
|---|---|---|---|
| `YQD3hMI2LPo` | `20261007OBLG02026` | 10/7 두산 @ LG, LG 7:5 승 | 시연 경기 |
| `FaJDs51xcTU` | `20260516LTOB02026` | 5/16 롯데 @ 두산 | 백업 |
| `zqPWIKkZLF0` | `20260904KTHT02026` | 9/4 KT @ KIA | 백업 |

## 엔드포인트

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/highlights` | 영상 목록 |
| GET | `/highlights/{video_id}` | 영상 정보 |
| GET | `/highlights/{video_id}/scenes` | 장면 표 전체 (추천) |
| GET | `/highlights/{video_id}/scene?t=757.3` | 재생 시간 `t`초의 장면 하나 |

영상 목록·정보 응답

```json
{"video_id": "YQD3hMI2LPo", "game_id": "20261007OBLG02026", "game_date": "2026-10-07",
 "away": "두산", "home": "LG", "scene_count": 79, "duration_sec": 1035.0}
```

**`/scenes` 를 추천한다.** 영상 하나에 장면이 80~110개(시연 경기 약 45KB)뿐이라, 처음에 한 번 받아 두고 프론트가 재생 시간으로 직접 찾으면 `/scene` 을 매초 부를 필요가 없다. 응답은 영상 정보에 `count`, `scenes` 가 붙은 형태다.

`/scene?t=` 는 `start ≤ t < end` 인 장면 하나를 그대로 돌려준다. 경계 시간(예: 760.0)은 뒤 장면에 속한다. 영상 길이를 넘는 등 해당 구간이 없으면 `{"status": "확인 불가"}` 를 돌려준다.

오류: 없는 `video_id` 는 404, `t` 가 없거나 음수면 422.

## 장면 구조

장면들은 0초부터 영상 끝까지 빈틈없이 이어진다. `status` 에 따라 세 가지다.

**확정**: 중계표(전광판)로 상황을 찾은 구간

```json
{
  "start": 755, "end": 760,
  "status": "확정", "confidence": "높음",
  "inning": 5, "half": "말", "batter": "이재원",
  "situation": {"outs": 2, "bases": [true, true, false], "score_away": 5, "score_home": 5},
  "prev_play": "문보경 : 중견수 앞 1루타",
  "result": "이재원 : 3루수 앞 내야안타 → 문보경·오스틴 홈인 [3루수 송구 실책] (5:5 → 5:7)",
  "play_id": "20261007OBLG02026:play:2bcc236e...",
  "prev_play_id": "20261007OBLG02026:play:8740e19e...",
  "play_ids": ["...2bcc236e...", "..."],
  "prev_type_tags": ["SINGLE", "ADVANCE"],
  "result_type_tags": ["SINGLE", "ADVANCE", "ERROR"],
  "restore": ["5회말, 2사, 점수 원정 5 : 홈 5", "1루 주자 문보경 ← 문보경 : 중견수 앞 1루타", "..."]
}
```

**추정**: 중계표가 안 보여서 바로 앞 장면 기준으로 채운 구간. 필드는 확정과 같고 `"status": "추정"`, `"confidence": "추정"` 만 다르다. 정확도가 약 70%라 **화면에서 꼭 구분해서 표시**한다.

**확인 불가**: 상황을 못 찾은 구간. `{"start": 440, "end": 460, "status": "확인 불가"}` 처럼 다른 필드가 없다. 카드를 숨기면 된다.

| 필드 | 뜻 | 화면에서 |
|---|---|---|
| `start`, `end` | 영상 시간(초) | 조회 기준 |
| `status` | 확정 / 추정 / 확인 불가 | 카드 표시 방식 |
| `confidence` | 높음 / 보통 / 낮음 / 추정 | 안 써도 됨 (디버그용) |
| `inning`, `half` | 이닝 숫자, `"초"` 또는 `"말"` | "5회말" |
| `batter` | 지금 타석의 타자 | "타자 이재원" |
| `situation.outs` | 아웃 수 0~2 | 아웃 표시 |
| `situation.bases` | `[1루, 2루, 3루]` 주자 있으면 true | 다이아몬드 |
| `situation.score_away` / `score_home` | 원정/홈 점수 | "두산 5 : 5 LG" |
| `prev_play` | 방금 일어난 플레이 한 줄, 없으면 null | "⚡ 방금" |
| `result` | 이 타석 결과 한 줄 | **"결과 보기"로 접어 두기** (아래 스포일러 참고) |
| `play_id`, `prev_play_id`, `play_ids` | 경기 기록(B4)의 플레이 ID: 이 타석 결과 / 방금 플레이 / 이 장면의 플레이 전부 | 해설·경기 기록과 연결할 때 |
| `prev_type_tags` | `prev_play` 의 유형 태그 (아래 참고) | "⚡ 방금" 옆 용어 카드 |
| `result_type_tags` | `result` 의 유형 태그 | "결과 보기" 펼친 뒤 용어 카드 |
| `restore` | 앞 흐름 문장 목록 | 주자별 출루 이유, 앞선 득점 |

`restore` 에서 화면에 쓸 줄은 `"N루 주자 OOO ← ..."` (주자가 어떻게 나갔는지)와 `"이번 이닝 앞선 득점: ..."` 이다. 나머지 줄은 다른 필드와 겹친다.

**스포일러 주의**: `result` 는 그 타석의 결과라서, 타자가 공을 치기 전 화면에서 보이면 결과를 미리 알려주게 된다 (예: 7:40 김민석이 타석에 서 있는데 "김민석 1루타 → 3:3"이 먼저 보임). 그래서 카드에는 `prev_play`(⚡ 방금)를 기본으로 보여주고, `result` 는 **"▶ 결과 보기" 버튼으로 접어 두었다가 누르면 펼친다** (노션 가이드 1116과 같음). `result_type_tags` 로 띄우는 용어 카드도 결과를 드러내므로 같이 접어 둔다.

**유형 태그 → 용어 카드**: `prev_type_tags`, `result_type_tags` 의 태그로 `GET /dict/events/{태그}` 를 부르면 그 플레이에 맞는 사전 카드가 나온다 (예: 12:35 `result_type_tags` 의 `ERROR` → "실책" 카드). 태그는 경기 DB(B4 `data/db/yagu.sqlite`)에서 `play_id` 로 찾아 붙인다. 경기 DB가 없는 컴퓨터에서는 이 두 필드만 빠지고 나머지는 그대로 나온다. `확인 불가` 장면에는 없다. 태그 목록은 `docs/event_types.md`.

`추정` 카드 문구 예시: "전광판이 확인되지 않아 앞 장면을 기준으로 추정한 정보입니다. 실제와 다를 수 있어요". `확인 불가` 는 카드를 숨기거나 "이 장면은 경기 기록과 연결하지 못했어요".

## 시연 장면 (두산 vs LG, `YQD3hMI2LPo`)

AI 쪽에서 영상과 카드를 미리 맞춰 본 장면이다. 테스트(`test_demo_scenes`)로 API 응답을 고정해 두었다.

| 영상 시간 | `t` | 장면 | 카드 |
|---|---|---|---|
| 7:15 | 435 | 3회초 두산 2사 만루 | ⚡ 방금: 양의지 몸에 맞는 볼 / 주자 3명 출루 이유 |
| 8:00 | 480 | 김민석 동점타 → 3:3 | ⚡ 방금: 김민석 1루타 → 세베리노·안재석 홈인 (1:3 → 3:3), **추정** 구간 |
| 10:40 | 640 | 3회말 LG 1사 만루 | 만루 주자 3명 출루 이유 |
| 12:35 | 755 | 5회말 이재원 타석, 2사 1·2루 | 이재원 타석, 주자 출루 이유 → "결과 보기"로 3루수 송구 실책 결승 2점. `result_type_tags` 의 `ERROR` → `/dict/events/ERROR` "실책" 카드 |

카드 모양 미리 보기 (AI 쪽 도구): `cd ai/highlight && python preview.py output/scenes_20261007OBLG02026.json --at 12:35`. 화면 카드와 이 결과가 같으면 연결이 제대로 된 것이다.

장면 표 형식이나 필드를 바꾸려면 AI 담당(윤경)에게 말한다. 파일이 바뀌면 `python -m backend.highlight.store build` 로 DB를 다시 만든다.

## 경기 기록과 잇기

`game_id` 는 `/games/{game_id}` 와 같은 값이다. 하이라이트 장면에서 그 경기의 플레이 목록·사전 카드로 넘어갈 때 쓴다.
