# AI-A 해설 생성 (야구한입)

조건 R, B0~B3으로 해설을 생성하고, B3는 규칙 기반 검증기로 거름.
429/503 재시도, 결과 캐시, 사용량 기록, 비용 추정까지 포함.

## 파일

| 파일 | 하는 일 |
|---|---|
| `config.py` | 모델, RPM, 재시도 횟수, 단가표 (여기만 고치면 됨) |
| `prompts.py` | 시스템 프롬프트, 조건별 입력 구성, R 템플릿 |
| `gemini_client.py` | 캐시 → 속도 제한 → 호출 → 재시도 → `logs/usage.jsonl` 기록 |
| `verifier.py` | B3 검증기: 근거 표시 / ID 존재 / 숫자 / 선수 이름 대조 |
| `generate.py` | 실행 스크립트 → `outputs/<모델>_<프롬프트버전>/generations.jsonl` |
| `build_testset.py` | BE 상태 복원 결과 + picks.csv → 테스트셋 (raw_relay·facts·players 자동) |
| `check_testset.py` | 테스트셋 형식 검사 (무료) |
| `estimate_cost.py` | 사용량 리포트 + 전체 실험 비용 + 유료 전환 판단 |
| `data/` | 입력 형식 예시 (테스트셋, 카드) |

## 조건

| 조건 | 입력 | LLM 호출 |
|---|---|---|
| R | F 템플릿 + 카드 원문 그대로 | 없음 |
| B0 | 질문 + 문자중계 원문(R1..) | O |
| B1 | B0 + 정리된 기록 F | O |
| B2 | B1 + 카드 K | O |
| B3 | **B2 출력 재사용** + 검증기 | 없음 |

B3를 따로 생성하지 않는 이유: 새로 생성하면 B2와 B3 차이에 '생성 랜덤성'이 섞임. 같은 B2 출력에 검증기만 붙여야 검증기 효과만 비교됨. 호출 수도 문항당 3회로 줄어듦.

## 실행

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...          # Colab이면 userdata에서 읽어서 os.environ에 넣기

python generate.py --dry-run       # API 안 쓰고 파이프라인 확인
python build_testset.py build --restored ../../data/raw/b2_state_v2_all --picks data/picks.csv   # 테스트셋 반자동 생성
python check_testset.py data/testset.jsonl --cards ../../cards   # 테스트셋 형식 검사 (무료)
python generate.py --testset data/testset.jsonl --cards ../../cards
python generate.py --limit 3       # 3문항만 실제 호출 → 실측 토큰 확보
python estimate_cost.py --free-rpd <AI Studio에 뜨는 RPD> --days-left <남은 날>
python generate.py                 # 전체
```

## 한도 대응

- **분당 한도(RPM)**: `config.RPM` 간격으로 호출을 띄움. AI Studio에 뜨는 값보다 조금 낮게 잡을 것
- **429 (분당)**: 서버가 준 `retryDelay`만큼 기다렸다가 재시도. 없으면 4→8→16초… 지수 백오프
- **429 (하루 한도)**: 재시도해도 소용없어서 바로 멈추고 지금까지 결과 저장. 한도는 태평양 자정(한국 오후 4~5시)에 초기화됨. 같은 명령 다시 돌리면 캐시된 건 건너뛰고 이어서 함
- **503/500/504 (서버 과부하)**: 지수 백오프로 최대 6번 재시도
- 실험 도중 모델을 자동으로 바꾸는 fallback은 일부러 안 넣음. 조건마다 모델이 다르면 비교가 무의미해짐

## 캐시

모델 + 프롬프트 버전 + 시스템/사용자 프롬프트 + 생성 설정을 해시해서 `cache/`에 저장.
**프롬프트를 고치면 `config.PROMPT_VERSION`을 올릴 것.** 안 올려도 내용이 바뀌면 키는 바뀌지만, 버전으로 결과 폴더가 나뉘어야 나중에 헷갈리지 않음.
테스트셋·프롬프트 고정 후 최종 생성분은 `cache/`째로 보관하면 재현 근거가 됨.

## 입력 형식

자세한 작성법은 `data/TESTSET_GUIDE.md`, 빈 양식은 `data/testset_template.jsonl`.

`data/testset_sample.jsonl` 한 줄 = 한 문항
- `raw_relay`: 문자중계 줄 리스트 → 자동으로 R1, R2… 번호 붙음
- `facts`: `{"id": "F1", "text": ...}` 리스트 (BE/DB 쪽에서 만들어 주는 F)
- `card_ids`: 이 문항에 붙일 카드 ID
- `players`: 이 경기 선수 이름 목록 (검증기 이름 대조용)

## 검증기 한계

- 숫자는 아라비아 숫자 + "1사/원아웃" 같은 아웃카운트 표현만 정규화함. "세 번째", "두 점" 같은 한글 수사는 못 잡음
- 이름은 `players` 목록에 있는 이름만 검사함. 목록에 없는 선수를 지어내면 못 잡으니 목록은 그 경기 출전 선수 전체로 넣을 것
- 근거 표시 없는 문장은 접속 문장이어도 지움 (채점에서도 접속 문장은 분모에서 빠지니까 지표엔 영향 적음)
