# 테스트셋 작성법

## 추천: 반자동으로 만들기 (BE 상태 복원 결과 사용)

`backend/game/restore_state.py` 결과가 있으면 사람은 **장면·질문·카드만** 고르면 됨.
문자중계(raw_relay), 이닝·아웃·주자·점수(facts), 선수 목록(players)은 자동으로 채워짐.

1. 복원 결과 만들기 (BE 쪽 명령, 레포 맨 위에서):
   ```
   python backend/game/restore_state.py --data <B1 데이터 경로> --out data/raw/b2_state_v2_all --game <경기ID>
   ```
2. 장면 찾기 → 맨 앞 8글자 id 확인 (`⚠` 표시 줄 근처는 피하기). `--no-pitches`를 붙이면 "1구 볼" 같은 투구 줄을 숨김:
   ```
   python build_testset.py list --restored ../../data/raw/b2_state_v2_all --game <경기ID> --inning 7 --no-pitches
   ```
   - 장면은 **결과가 나온 줄**로 고르기 (예: `조형우 : 2루수 앞 땅볼로 출루`, `1루주자 조형우 : 포일로 2루까지 진루`). "5구 타격" 같은 투구 줄 말고
3. `picks_template.csv`를 `picks.csv`로 복사해서 한 줄에 한 문항씩 채움 (엑셀·구글시트 가능)
   - `play_id`에는 list에 나온 8글자 id만 쓰면 됨 (예: `2d77fc57`)
   - `tags`, `card_ids`가 여러 개면 `|`로 구분: `rule.infield_fly|term.out`
   - `extra_facts`: 기록에 없는 사실을 따로 적을 때만 (예: `교체 사유 기록 없음`)
4. 생성 → 검사:
   ```
   python build_testset.py build --restored ../../data/raw/b2_state_v2_all --picks data/picks.csv --out data/testset.jsonl
   python check_testset.py data/testset.jsonl --cards ../../cards
   ```
5. `[주의] 네이버 상태와 불일치`가 뜬 문항은 facts를 원본과 직접 대조하거나 다른 장면으로 바꾸기
6. `players`는 문자중계에 이름이 나온 선수만 모은 것. 출전했지만 한 번도 언급 안 된 선수는 빠질 수 있음

## 직접 쓰기 (복원 결과가 없을 때)

`testset_template.jsonl`을 복사해서 `testset.jsonl`로 이름 바꾸고 채우면 됨.
**한 줄 = 한 문항.** 줄 중간에 엔터 치면 안 됨. 30문항이면 30줄.

다 쓰면 검사부터:
```
python check_testset.py data/testset.jsonl --cards ../../cards
```

## 칸 설명

| 칸 | 필수 | 내용 | 예시 |
|---|---|---|---|
| `qid` | O | 문항 번호. 겹치면 안 됨 | `"Q01"` |
| `type` | O | `규칙` / `상황` / `기술` 중 하나. 10개씩 | `"규칙"` |
| `tags` | | 어려운 케이스 표시: `복합상황`, `지연·누락기록`, `모호한규칙` | `["복합상황"]` |
| `game_id` | | 어느 경기인지. 분석용 | `"20260912_LGDS"` |
| `question` | O | 초보자가 물어볼 법한 질문 한 문장 | `"공을 안 잡았는데 왜 아웃이에요?"` |
| `raw_relay` | O | 그 장면 앞뒤 문자중계를 **한 줄씩** 리스트로. 코드가 R1, R2… 번호를 붙임 | `["7회말 1사 1,2루", "OOO : 내야 뜬공"]` |
| `facts` | | 정리된 경기 기록. `id`는 F1, F2… | `[{"id": "F1", "text": "7회말, 1사 1,2루, 점수 3-2"}]` |
| `card_ids` | O | 관련 카드 id. `cards/` 폴더의 파일 이름에서 `.yaml` 뺀 것 | `["rule.infield_fly", "term.out"]` |
| `players` | O | 그 경기 **출전 선수 전체** 이름. 검증기가 이름 대조에 씀 | `["OOO", "XXX"]` |

## 지켜야 할 것 (루브릭 결정 사항)

- 경기는 2~3개에서 고르고, **카드 만들 때 참고한 경기는 빼기**
- `facts`에는 그 장면에 해당하는 사실만. 해설처럼 쓰지 말고 기록만
- 기록이 누락된 장면이면 `facts`에도 `"교체 사유 기록 없음"`처럼 없다는 걸 적기
- `players`는 그 장면 선수만이 아니라 경기 출전 선수 전부. 적으면 지어낸 이름을 못 잡음
- **테스트셋을 확정하면 이후엔 수정 금지.** 결과 보고 문항 바꾸면 조작이 됨

## 자주 나는 실수

- 큰따옴표(`"`) 대신 작은따옴표(`'`) 쓰기 → JSON 오류
- 마지막 항목 뒤에 쉼표 붙이기 → JSON 오류
- 카드 id 오타 → 검사에서 "카드가 cards 폴더에 없음"으로 잡힘
