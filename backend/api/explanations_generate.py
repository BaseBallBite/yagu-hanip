"""Production-guarded B3 explanation endpoint backed by trusted R/F/K, Gemini and KLUE.

The experimental run_rule_b3() remains available separately, but the HTTP route
must never serve its provisional rule-only output. GET /explanations/demo is unchanged.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.explanation.live_runtime import get_live_dependencies
from backend.explanation.question_chips import CHIPS, allowed_chip_ids, chips_for_play, play_tags
from backend.explanation.question_scope import question_targets_another_batter
from backend.explanation.service_pipeline import build_verified_explanation
from backend.game import store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/explanations", tags=["explanations"])


class GenerateRequest(BaseModel):
    game_id: str = Field(min_length=1, max_length=80)
    play_id: str = Field(min_length=1, max_length=160)
    # 서비스 화면은 chip_id만 보낸다(자유 입력 없음). question은 기존 호출 호환용.
    question: str | None = Field(default=None, min_length=1, max_length=300)
    chip_id: str | None = Field(default=None, min_length=1, max_length=40)


def _open_db():
    db = Path(os.environ.get("YAGU_DB", str(store.DB_PATH)))
    try:
        return store.connect(db)  # B4 uses SQLite mode=ro; never create/modify the DB.
    except (FileNotFoundError, OSError) as exc:
        raise HTTPException(status_code=503, detail="경기 DB를 사용할 수 없습니다") from exc


@router.get("/chips")
def list_question_chips(
    game_id: str = Query(..., min_length=1, max_length=80),
    play_id: str = Query(..., min_length=1, max_length=160),
) -> dict:
    """플레이에 보여줄 질문 칩(입구 q.why + 「한입 더」 후속 칩). Gemini를 부르지 않는다."""
    con = _open_db()
    try:
        chips = chips_for_play(con, game_id, play_id)
    finally:
        con.close()
    if chips is None:
        raise HTTPException(status_code=404, detail="해당 플레이를 찾을 수 없습니다")
    return chips


@router.post("/generate")
def generate_explanation(req: GenerateRequest) -> dict:
    """Generate one B2 answer and return only rule-v2+KLUE verified B3 sentences.

    Explicit operator opt-in avoids accidental network calls and Gemini charges.
    Keep this endpoint local/private until the team adds auth and request limits.
    """
    if (req.question is None) == (req.chip_id is None):
        raise HTTPException(status_code=422, detail="chip_id 또는 question 중 하나만 보내 주세요")
    if not all((req.game_id.strip(), req.play_id.strip(), (req.question or req.chip_id).strip())):
        raise HTTPException(status_code=422, detail="game_id, play_id, 질문은 공백일 수 없습니다")
    chip = CHIPS.get(req.chip_id) if req.chip_id is not None else None
    if req.chip_id is not None and chip is None:
        raise HTTPException(status_code=422, detail="알 수 없는 질문 칩입니다")
    if os.environ.get("EXPLANATION_GENERATION_ENABLED") != "1":
        raise HTTPException(status_code=503, detail="실제 해설 생성 API는 현재 비활성화 상태입니다")

    con = _open_db()

    try:
        # Reject invalid IDs without initializing Gemini/KLUE dependencies.
        row = con.execute(
            "SELECT 1 FROM plays WHERE game_id=? AND play_id=?",
            (req.game_id, req.play_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="해당 플레이를 찾을 수 없습니다")
        # A clearly mismatched batter/play question is a client input error,
        # not a generation failure. Reject before loading Gemini or KLUE.
        if chip is not None:
            # 칩은 플레이 유형에 맞는 것만 허용한다(허용 범위 밖 질문 차단).
            if chip.id not in allowed_chip_ids(play_tags(con, req.game_id, req.play_id) or []):
                raise HTTPException(status_code=422, detail="이 플레이에서는 쓸 수 없는 질문 칩입니다")
            question = chip.question
            extra_cards = chip.card_ids
        else:
            question = req.question
            extra_cards = ()
        if chip is None and question_targets_another_batter(con, req.game_id, req.play_id, question):
            raise HTTPException(
                status_code=422,
                detail="질문에 지정한 타자의 플레이가 선택한 해설 대상과 일치하지 않습니다",
            )
        try:
            deps = get_live_dependencies()
        except (OSError, ValueError, ImportError, RuntimeError) as exc:
            logger.warning("Explanation runtime unavailable: %s", type(exc).__name__)
            raise HTTPException(status_code=503, detail="해설 모델 또는 설정을 사용할 수 없습니다") from exc
        try:
            answer = build_verified_explanation(
                con, req.game_id, req.play_id, question,
                generate=deps.generate, p_support=deps.p_support,
                threshold=deps.threshold,
                extra_card_ids=extra_cards,
            )
        except Exception as exc:
            logger.exception("Explanation generation/verification failed")
            raise HTTPException(status_code=502, detail="해설 생성 또는 검증에 실패했습니다") from exc
        if answer is None:
            raise HTTPException(status_code=404, detail="해당 플레이는 해설 대상이 아닙니다")
        if chip is not None:
            answer["chip_id"] = chip.id
            answer["chip_label"] = chip.label
        return answer
    finally:
        con.close()
