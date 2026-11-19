"""R/F/K -> B2 생성 -> 규칙 v2 + KLUE(B3) 서비스 연결부.

AI-A 실험용 코드와 시연용 API를 변경하지 않고, 생성기와 KLUE 콜백을 주입한다.
"""
from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path
from functools import lru_cache
from typing import Callable

from ai.explain.prompts import (Commentary, SYSTEM_PROMPT, build_user_prompt,
                                evidence_pool, load_cards)
from ai.explain.verifier import verify_service
from backend.explanation.explanation_input import build_explanation_input

CARDS_DIR = Path(__file__).resolve().parents[2] / "cards"
UNKNOWN_CITATION = "기록에 근거 없음 (확인할 수 없는 내용)"


def load_threshold(model_dir: str | Path) -> float:
    """KLUE 모델 폴더 threshold.json 값만 사용한다. 임의 기본값으로 대체하지 않는다."""
    data = json.loads((Path(model_dir) / "threshold.json").read_text(encoding="utf-8"))
    value = data["threshold"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("threshold.json: invalid threshold")
    value = float(value)
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("threshold.json: threshold outside [0, 1]")
    return value


@lru_cache(maxsize=8)
def _get_cards(cards_dir: Path) -> dict:
    """사전 YAML을 서비스 프로세스당 1회만 읽는다."""
    return load_cards(cards_dir)


def _checked_probabilities(p_support: Callable, pairs: list[tuple[str, str]]) -> list[float]:
    """길이/확률 오류를 안전하게 실패 처리 (검증 생략 방지)."""
    probs = list(p_support(pairs))
    if len(probs) != len(pairs):
        raise ValueError("KLUE returned wrong number of scores")
    if any(isinstance(p, bool) or not isinstance(p, (int, float))
           or not math.isfinite(p) or not 0 <= p <= 1 for p in probs):
        raise ValueError("KLUE returned invalid probability")
    return probs


def build_verified_explanation(
    con: sqlite3.Connection,
    game_id: str,
    play_id: str,
    question: str,
    *,
    generate: Callable,
    p_support: Callable,
    threshold: float,
    cards_dir: Path = CARDS_DIR,
) -> dict | None:
    """GeminiRunner.generate와 KLUE load_model의 p_support를 연결한다.

    현재 이 함수는 실제 API 엔드포인트가 아니라, API에서 호출할 서비스 핵심 로직이다.
    플레이가 없거나 R 조회 대상에서 제외되면 None 반환. DB 변경 없음.
    """
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("invalid threshold")
    item = build_explanation_input(con, game_id, play_id, question)
    if item is None:
        return None

    cards = _get_cards(Path(cards_dir))
    pool = evidence_pool(item, cards, "B2")
    user_prompt = build_user_prompt(item, cards, "B2")
    # Service-only guidance: do not change the AI-A prompt or the verifier.
    user_prompt += (
        "\n\n[서비스 해설의 문장별 근거 인용 필수 규칙]\n"
        "1. 문장에 등장하는 모든 선수 이름은 그 이름이 실제로 적혀 있는 "
        "R 또는 F 근거 ID를 해당 문장의 evidence에 반드시 포함하세요.\n"
        "2. 한 문장에 여러 선수가 나오면 각 선수 이름을 뒷받침하는 "
        "근거 ID를 빠짐없이 인용하세요. 단순히 다른 근거에 이름이 존재하는 것으로는 부족합니다.\n"
        "3. 투구 번호와 결과, 주자 위치, 득점 원인과 점수도 각 사실을 직접 "
        "뒷받침하는 R/F 근거를 문장별로 인용하세요.\n"
        "4. K 카드는 야구 용어와 규칙 설명에 사용하고, "
        "실제 선수·경기 기록에 대한 근거를 대체하지 마세요.\n"
        "5. 제공되지 않은 기록이나 근거 ID를 만들어내지 마세요. "
        "근거를 인용할 수 없는 세부 사항은 문장에서 제외하세요.\n"
        "6. 질문의 핵심에 먼저 답하고, 이유를 설명하는 핵심 문장에도 "
        "관련된 R/F/K 근거를 빠짐없이 인용하세요."
    )
    raw, meta = generate(SYSTEM_PROMPT, user_prompt, Commentary,
                         {"qid": item["qid"], "condition": "B2"})
    if not isinstance(raw, dict) or not isinstance(raw.get("sentences"), list):
        raise ValueError("Gemini response has no sentences list")

    verified = verify_service(raw, pool, item["players"],
                              lambda pairs: _checked_probabilities(p_support, pairs),
                              threshold=threshold)
    sentences = []
    for sent in verified["sentences"]:
        cited_ids = sent.get("evidence") or []
        sentences.append({
            "text": sent["text"],
            "cited_ids": cited_ids,
            "cited_text": [{"id": e, "text": UNKNOWN_CITATION if e == "UNKNOWN" else pool[e]}
                           for e in cited_ids],
            "verdict": sent["verdict"],
            "check": sent["check"],
            "p_support": sent["p_support"],
        })
    return {
        "mode": "live",
        "source": "gemini+rule_v2+klue",
        "game_id": item["game_id"],
        "play_id": item["play_id"],
        "seq": item["seq"],
        "question": item["question"],
        "display_condition": "B3",
        "card_ids": item["card_ids"],
        "sentences": sentences,
        "dropped_count": len(verified["dropped"]),
        "verifier": {"threshold": threshold, "checked_sentences": len(raw["sentences"])},
        "generation": {"model": (meta or {}).get("model"), "cache_hit": (meta or {}).get("cache_hit")},
    }
