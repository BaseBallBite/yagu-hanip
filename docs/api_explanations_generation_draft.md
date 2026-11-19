# 일반 해설 생성 API (B3 서비스)

`POST /explanations/generate` 요청은 `{ "game_id": "...", "play_id": "...", "question": "..." }` 형태입니다.
기본적으로 비활성(503)이며 `EXPLANATION_GENERATION_ENABLED=1`일 때만 사용할 수 있습니다.
시연용 `GET /explanations/demo`는 별개의 사전 생성된 해설을 반환합니다.

- B4 SQLite의 `plays`를 읽기 전용으로 조회하고 동일 경기/플레이의 R/F/K를 구성합니다.
- AI-A GeminiRunner에서 B2 문장을 한 번 생성합니다(실제 외부 호출, 비용 가능).
- `verify_service()`의 규칙 v2와 실제 KLUE 점수 검증을 통과한 문장만 B3로 반환합니다.
- `UNKNOWN`은 별도 규칙을 통과하면 KLUE 검사 없이 유지합니다.
- `cited_ids`, `cited_text`, `display_condition`을 포함하고 검증 실패 시 미검증 해설을 반환하지 않습니다.

## 로컬 실행 설정

환경 변수 `YAGU_DB`, `GEMINI_API_KEY`, `KLUE_MODEL_DIR`, `KLUE_APPLY_DIR`, `KLUE_PYTHON` 설정 후
`EXPLANATION_GENERATION_ENABLED=1`로 활성화합니다. `KLUE_PYTHON`은 기존 KLUE용 Python 가상환경 실행 파일의 전체 경로입니다.
`threshold.json`에서 임계값을 읽으며, FastAPI 프로세스에서 모델을 재학습하거나 다운로드하지 않습니다.

**주의**: 현재 KLUE worker는 요청별로 모델을 새로 실행하므로 지연이 발생할 수 있습니다. 외부 공개 전에는 인증·요청 제한·비용 통제가 필요합니다.
검증기용 `players` 목록은 B4의 타자/투수 조회에 기반하므로 전체 엔트리와 일치하는지 점검해야 합니다.
실제 Gemini+KLUE 호출 및 10장면 수동 평가가 끝나기 전에는 품질 검증 완료라고 보고하지 않습니다.
평가용 3/28, 6/21, 7/23, 10/11 경기를 시연·화면 테스트에 사용하지 않습니다.

## 테스트

`python -m unittest backend.tests.test_explanation_pipeline backend.tests.test_explanations_generate_service_api backend.tests.test_service_pipeline backend.tests.test_explanations_api -v`

테스트는 합성 DB·모의 Gemini·모의 KLUE를 사용하며 유료 모델 호출이 발생하지 않습니다.
