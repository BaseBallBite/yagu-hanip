# 시연용 해설 조회 API (10/7 두산–LG 전용)

이 API는 **발표용으로 이미 생성된** H01~H03 해설만 반환합니다. Gemini API 호출,
검증 모델 실행, DB 생성/수정, 평가용 경기 접근이 **없습니다**.
전체 해설 생성 API와 실시간 문자중계 폴링은 **이 작업에 포함되지 않습니다**.

- 승인된 경기: `20261007OBLG02026` (10월 7일 두산–LG, `YQD3hMI2LPo`)
- 해설 원본(읽기 전용): `ai/explain/be/be_highlight_20261007OBLG02026.json`
- `play_id`: 위 JSON의 `play_id` 또는 `/highlights/YQD3hMI2LPo/scene?t=755` 응답의 `play_id`를 **변경 없이 사용**
- 평가용 3/28, 6/21, 7/23, 10/11 및 기타 경기: 조회 대상 아님 (404)

## 요청

- `GET /explanations/demo/questions?game_id=...&play_id=...` — H01~H03 질문 목록
- `GET /explanations/demo?game_id=...&play_id=...&qid=H01` — 해당 B3 해설
- `GET /explanations/demo?game_id=...&play_id=...&question=<저장된 질문>` — 질문 문장으로 정확히 조회

`qid`와 `question` 중 **하나만** 전달해야 합니다. 등록되지 않은 질문은 **404**이며 Gemini로 자동 생성하지 않습니다.

## 응답

```json
{
  "mode": "demo",
  "source": "precomputed",
  "game_id": "20261007OBLG02026",
  "play_id": "<장면표의 play_id>",
  "qid": "H01",
  "question": "안타 쳤는데 왜 실책으로 점수가 났어요?",
  "display_condition": "B3",
  "sentences": [
    {
      "text": "<기존 시연 JSON에 저장된 문장 그대로>",
      "cited_ids": ["R8", "F2", "term.infield_hit"],
      "cited_text": [{"id": "R8", "text": "<기존 근거 원문>"}],
      "verdict": "통과"
    }
  ],
  "verifier": "B2+verifier_v2"
}
```

`sentences`는 **시연 JSON의 B3 데이터를 그대로 전달**합니다. 여기의 예시 문장은 형식만 설명합니다.
특히 H03의 `UNKNOWN` 근거는 **기록에 없는 이유를 단정하지 않는 정상 응답**이므로 삭제하거나 재검증하지 않습니다.
R/B0 비교용 해설은 이 API에서 반환하지 않습니다.

## 로컬 테스트 (Windows / 저장소 루트)

```powershell
py -m unittest backend.tests.test_explanations_api -v
```

FastAPI / httpx가 설치된 가상환경에서 실행해야 합니다. 이 테스트는 10/7 시연 JSON만 읽으며
평가 데이터, Gemini, KLUE, DB에 접근하지 않습니다.

## 통합 작업 시 주의

- `backend/api/main.py`에 라우터만 추가했습니다. 기존 `/games`, `/highlights`, `/dict`는 수정하지 않았습니다.
- 생성 코드 `ai/explain/`과 하이라이트 장면표 원본은 수정하지 않았습니다.
- 최신 `main` 및 팀원 PR과 비교한 후에만 병합하세요. 11/16 ZIP을 기준으로 작성한 패치입니다.
- 향후 실제 생성 API에는 별도 POST 경로를 설계하고, 선택된 Gemini/검증기 버전을 확정하세요.
