"""Guarded draft API for future Gemini generation integration.

Default behavior is intentionally 503: team-approved trusted R/F/K resolver and
Gemini runtime are NOT yet connected. Test code injects fake providers and a
fake generator; production must NEVER accept fabricated evidence from a client.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.explanation.pipeline import EvidenceContractError, run_rule_b3

router = APIRouter(prefix="/explanations", tags=["explanations"])


class GenerateRequest(BaseModel):
    game_id: str = Field(min_length=1, max_length=80)
    play_id: str = Field(min_length=1, max_length=160)
    question: str = Field(min_length=1, max_length=300)


def load_trusted_context(req: GenerateRequest) -> tuple[dict, dict]:
    """Future BE provider: exact play_id -> source R, F, <=3 K, players.

    Deliberately NOT substituting `plays.description` for the full source R or
    guessing a player's full roster. Cannot ship live until this is agreed.
    """
    raise HTTPException(status_code=503, detail="장면별 R/F/K 근거 조회 방식이 아직 확정되지 않았습니다")


def get_live_generator():
    """To be wired to AI-A's GeminiRunner when service runtime is approved."""
    raise HTTPException(status_code=503, detail="Gemini 서비스 연결이 아직 활성화되지 않았습니다")


@router.post("/generate")
def generate_explanation(req: GenerateRequest) -> dict:
    # An explicit operator opt-in is necessary even to use this incomplete API.
    if os.environ.get("EXPLANATION_GENERATION_ENABLED") != "1":
        raise HTTPException(status_code=503, detail="실제 해설 생성 API는 현재 비활성화 상태입니다")
    item, cards = load_trusted_context(req)
    if item.get("game_id") != req.game_id or item.get("play_id") != req.play_id:
        raise HTTPException(status_code=422, detail="요청한 경기/플레이와 근거가 일치하지 않습니다")
    item = {**item, "question": req.question, "qid": "service-request"}
    generator = get_live_generator()
    try:
        result = run_rule_b3(item, cards, generator.generate)
    except EvidenceContractError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    # Network/permission errors will be handled when AI-A runtime is connected.
    return {"game_id": req.game_id, "play_id": req.play_id,
            "question": req.question, **result}
