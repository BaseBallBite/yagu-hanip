"""Production-guarded B3 explanation endpoint backed by trusted R/F/K, Gemini and KLUE.

The experimental run_rule_b3() remains available separately, but the HTTP route
must never serve its provisional rule-only output. GET /explanations/demo is unchanged.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.explanation.live_runtime import get_live_dependencies
from backend.explanation.service_pipeline import build_verified_explanation
from backend.game import store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/explanations", tags=["explanations"])


class GenerateRequest(BaseModel):
    game_id: str = Field(min_length=1, max_length=80)
    play_id: str = Field(min_length=1, max_length=160)
    question: str = Field(min_length=1, max_length=300)


@router.post("/generate")
def generate_explanation(req: GenerateRequest) -> dict:
    """Generate one B2 answer and return only rule-v2+KLUE verified B3 sentences.

    Explicit operator opt-in avoids accidental network calls and Gemini charges.
    Keep this endpoint local/private until the team adds auth and request limits.
    """
    if not all((req.game_id.strip(), req.play_id.strip(), req.question.strip())):
        raise HTTPException(status_code=422, detail="game_id, play_id, question은 공백일 수 없습니다")
    if os.environ.get("EXPLANATION_GENERATION_ENABLED") != "1":
        raise HTTPException(status_code=503, detail="실제 해설 생성 API는 현재 비활성화 상태입니다")

    db = Path(os.environ.get("YAGU_DB", str(store.DB_PATH)))
    try:
        con = store.connect(db)  # B4 uses SQLite mode=ro; never create/modify the DB.
    except (FileNotFoundError, OSError) as exc:
        raise HTTPException(status_code=503, detail="경기 DB를 사용할 수 없습니다") from exc

    try:
        # Reject invalid IDs without initializing Gemini/KLUE dependencies.
        row = con.execute(
            "SELECT 1 FROM plays WHERE game_id=? AND play_id=?",
            (req.game_id, req.play_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="해당 플레이를 찾을 수 없습니다")
        try:
            deps = get_live_dependencies()
        except (OSError, ValueError, ImportError, RuntimeError) as exc:
            logger.warning("Explanation runtime unavailable: %s", type(exc).__name__)
            raise HTTPException(status_code=503, detail="해설 모델 또는 설정을 사용할 수 없습니다") from exc
        try:
            answer = build_verified_explanation(
                con, req.game_id, req.play_id, req.question,
                generate=deps.generate, p_support=deps.p_support,
                threshold=deps.threshold,
            )
        except Exception as exc:
            logger.exception("Explanation generation/verification failed")
            raise HTTPException(status_code=502, detail="해설 생성 또는 검증에 실패했습니다") from exc
        if answer is None:
            raise HTTPException(status_code=404, detail="해당 플레이는 해설 대상이 아닙니다")
        return answer
    finally:
        con.close()
