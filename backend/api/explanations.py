"""Read-only, demo-only explanation endpoints.

The single approved 2026-10-07 Doosan–LG highlight has pre-generated H01–H03
answers.  These endpoints NEVER call Gemini, run a verifier, write to the DB,
or look up evaluation games.  Live generation is intentionally out of scope.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/explanations/demo", tags=["explanations"])

# Explicit allowlist. Do not scan ai/explain for other files: some are evaluation data.
DEMO_GAME_ID = "20261007OBLG02026"
DEMO_JSON = (
    Path(__file__).resolve().parents[2]
    / "ai" / "explain" / "be" / f"be_highlight_{DEMO_GAME_ID}.json"
)


def _load_demo(game_id: str, play_id: str) -> dict:
    """Match BOTH requested IDs against the single approved demo fixture."""
    if game_id != DEMO_GAME_ID:
        raise HTTPException(status_code=404, detail="시연용 해설을 찾을 수 없습니다")
    try:
        data = json.loads(DEMO_JSON.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=503, detail="시연용 해설 파일을 읽을 수 없습니다") from exc

    if not isinstance(data, dict) or data.get("game_id") != DEMO_GAME_ID or not isinstance(data.get("questions"), list):
        raise HTTPException(status_code=503, detail="시연용 해설 파일 형식이 올바르지 않습니다")
    if play_id != data.get("play_id"):
        raise HTTPException(status_code=404, detail="해당 플레이의 시연용 해설을 찾을 수 없습니다")
    return data


@router.get("/questions")
def demo_questions(
    game_id: str = Query(..., description="승인된 시연용 경기 ID"),
    play_id: str = Query(..., description="하이라이트 장면표의 play_id"),
) -> dict:
    """Return the H01–H03 question list; never return R/B0 evaluation comparisons."""
    data = _load_demo(game_id, play_id)
    return {
        "mode": "demo",
        "game_id": data["game_id"],
        "play_id": data["play_id"],
        "video_id": data.get("scene", {}).get("video_id"),
        "questions": [
            {
                "qid": q["qid"],
                "question": q["question"],
                "tags": q.get("tags", []),
                "display_condition": q["display_condition"],
            }
            for q in data["questions"]
        ],
    }


@router.get("")
def demo_explanation(
    game_id: str = Query(...),
    play_id: str = Query(...),
    qid: str | None = Query(None, description="H01, H02 또는 H03"),
    question: str | None = Query(None, description="저장된 질문 문장과 정확히 일치해야 함"),
) -> dict:
    """Read ONLY a pre-approved B3 answer, selected by qid OR exact question.

    Unknown questions return 404 (no Gemini fallback). UNKNOWN citations remain
    visible: an honest 'not in records' response must not be removed.
    """
    if (qid is None) == (question is None):
        raise HTTPException(status_code=422, detail="qid 또는 question 중 하나만 입력해 주세요")
    if qid is not None and not qid.strip() or question is not None and not question.strip():
        raise HTTPException(status_code=422, detail="빈 질문은 사용할 수 없습니다")

    data = _load_demo(game_id, play_id)
    match = next(
        (q for q in data["questions"]
         if (q.get("qid") == qid if qid is not None else q.get("question") == question)),
        None,
    )
    if match is None:
        raise HTTPException(status_code=404, detail="저장된 시연 질문이 없습니다")

    condition = match.get("display_condition")
    if condition != "B3":
        raise HTTPException(status_code=503, detail="시연 표시 조건이 B3가 아닙니다")
    answer = match.get("answers", {}).get(condition)
    if not isinstance(answer, dict) or not isinstance(answer.get("sentences"), list):
        raise HTTPException(status_code=503, detail="저장된 B3 해설이 올바르지 않습니다")

    return {
        "mode": "demo",
        "source": "precomputed",
        "game_id": data["game_id"],
        "play_id": data["play_id"],
        "qid": match["qid"],
        "question": match["question"],
        "display_condition": condition,
        "sentences": answer["sentences"],  # Preserve text, cited_ids, cited_text, verdict verbatim.
        "verifier": answer.get("verifier"),
    }
