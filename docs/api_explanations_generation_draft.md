# 해설 생성 API 연결부 (안전한 초안 / 미완료)

**상태: 실제 Gemini 생성 API는 비활성화.** 사전 생성된 10/7 시연용 API는 별도로 유지한다.

`POST /explanations/generate` (body: `game_id`, `play_id`, `question`)는
현재 기본적으로 **503**을 반환한다. 환경변수 `EXPLANATION_GENERATION_ENABLED=1`
만으로는 생성되지 않는다. 신뢰할 수 있는 R/F/K 조회자와 AI-A GeminiRunner
연결이 빠져 있으므로, 활성화를 시도해도 503이다. 이 제한을 우회하지 말 것.

왜 멈춰 뒀나:
- B4 SQLite에는 플레이 F와 한 줄 설명이 있지만, AI-A가 기대하는 장면별
  **원문 R 전체**, 전체 선수 목록, 관련 카드 K 최대 3장을 구성하는 계약이
  아직 확정되지 않았다. 임의로 R을 재구성하면 잘못된 해설이 나올 수 있다.
- `ai/explain/`의 실험용 프롬프트와 검증 기준을 수정하지 않는다.
- `backend/explanation/pipeline.py`는 **B2 프롬프트 구성 → 생성 함수 주입
  → 규칙 검증기 v2 → 문장별 cited_ids/cited_text**만 수행한다.
- 이 검증은 **임시 규칙 검증(v2)**이고, KLUE 모델 검증을 적용하지 않는다.
  AI-A의 `apply_model.py`/모델을 팀 합의 없이 연결하지 않는다.

안전한 테스트(가상 문장만 사용, 실제 Gemini·DB·평가용 경기 미접근):

```powershell
.\.venv\Scripts\python.exe -m unittest backend.tests.test_explanation_pipeline -v
```

테스트는 가상 장면(`SYNTHETIC_GAME`), 가짜 생성기, 모의 근거를 사용한다.
테스트 환경에서만 해당 함수들을 일시적으로 대체한다. **실제 API는 비활성화 유지.**

다음 선행조건: ① 신뢰 가능한 R/F/K 제공 함수와 `game_id + play_id` 연결
② AI-A 승인된 생성/검증 버전과 `UNKNOWN` 처리 정책 ③ 비용/한도/사용자 인증 정책
④ 검증모델 CPU 지연 측정 및 서비스 포함 여부 ⑤ 팀원 합의 후 프론트 응답 계약.

주의: 평가용 3/28·6/21·7/23·10/11 경기의 자료를 이 연결부 테스트에 사용하지 않는다.
시연용 10/7 해설은 기존 사전 생성 조회 API를 통해서만 반환하며 새로 생성하지 않는다.
