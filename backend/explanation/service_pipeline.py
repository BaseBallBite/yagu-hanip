"""R/F/K -> B2 생성 -> 규칙 v2 + KLUE(B3) 서비스 연결부.

AI-A 실험용 코드와 시연용 API를 변경하지 않고, 생성기와 KLUE 콜백을 주입한다.
"""
from __future__ import annotations

import json
import math
import re
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


# Explicit references to earlier plays are legitimate context, not target claims.
_PRIOR_CONTEXT_RE = re.compile(r"앞서|앞선|이전|직전|전\s*타석|그\s*전에|먼저|당시")
_COMPLETED_EVENTS = {
    "groundout", "flyout", "lineout", "popout", "strikeout", "single",
    "double", "triple", "home_run", "walk", "hit_by_pitch", "double_play",
    "steal", "caught_stealing", "runner_advance", "error", "fielder_choice",
    "sac_fly", "sac_bunt",
}


def _relay_scope(con: sqlite3.Connection, item: dict) -> tuple[str, set[str], set[str]]:
    """Annotate R provenance without removing valid before/after evidence.

    Determine the current plate appearance from the latest batter announcement
    in the selected R window. When it is absent, conservatively disable the
    previous-plate-appearance guard rather than guessing a boundary.
    """
    seqs = item["raw_relay_source_seqs"]
    if len(seqs) != len(item["raw_relay"]):
        raise RuntimeError("R text / source-seq mismatch")
    if not seqs:
        return "", set(), set()
    qmarks = ",".join("?" for _ in seqs)
    event_by_seq = {
        seq: event for seq, event in con.execute(
            f"SELECT seq, event_type FROM plays WHERE game_id=? AND seq IN ({qmarks})",
            (item["game_id"], *seqs),
        )
    }
    if len(event_by_seq) != len(set(seqs)):
        raise RuntimeError("R provenance lookup mismatch")
    target_seq = item["seq"]
    announcements = [
        seq for seq in seqs
        if seq <= target_seq and event_by_seq[seq] == "batter_announcement"
    ]
    pa_start = max(announcements) if announcements else None
    previous_r = set()
    previous_completed_r = set()
    labels = []
    for index, seq in enumerate(seqs, 1):
        key = f"R{index}"
        if seq == target_seq:
            relation = "TARGET"
        elif seq > target_seq:
            relation = "AFTER"
        elif pa_start is None:
            relation = "BEFORE"  # PA boundary is unknown; do not guess.
        else:
            relation = "CURRENT_PA" if seq >= pa_start else "PRIOR_PA"
        labels.append(f"{key}: {relation} (seq={seq})")
        if pa_start is not None and seq < pa_start:
            previous_r.add(key)
            if event_by_seq[seq] in _COMPLETED_EVENTS:
                previous_completed_r.add(key)
    return "\n".join(labels), previous_r, previous_completed_r


def _is_unanchored_previous_play(sent: dict, previous_r: set[str],
                                 previous_completed_r: set[str]) -> bool:
    """Reject standalone earlier-play outcomes supported only by old R (+ K).

    Do not reject F-backed current-play claims, current-PA pitches, UNKNOWN,
    or explicit statements introduced as earlier context. This is intentionally
    conservative: it is NOT a general semantic play-identity verifier.
    """
    refs = sent.get("evidence") or []
    if not isinstance(refs, list) or not refs or not all(isinstance(e, str) for e in refs):
        return False
    if "UNKNOWN" in refs or any(e.startswith("F") for e in refs):
        return False
    r_refs = {e for e in refs if re.fullmatch(r"R[1-9]\d*", e)}
    if not r_refs or not r_refs <= previous_r or not (r_refs & previous_completed_r):
        return False
    return not _PRIOR_CONTEXT_RE.search(sent.get("text", ""))


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
    # R IDs are trustworthy but neighboring plays are context, not the target.
    r_labels, previous_r, previous_completed_r = _relay_scope(con, item)
    target_row = con.execute(
        "SELECT event_type, description FROM plays WHERE game_id=? AND play_id=?",
        (game_id, play_id),
    ).fetchone()
    if target_row is None:
        raise RuntimeError("target play disappeared after R/F/K lookup")
    user_prompt += (
        "\n\n[현재 해설 대상 및 R 근거 범위]\n"
        f"TARGET seq={item['seq']}, event={target_row[0]}, 기록={target_row[1]}\n"
        "PRIOR_PA는 앞선 타석, CURRENT_PA는 현재 타석의 투구/상황, "
        "AFTER는 이후 기록입니다. TARGET과 혼동하지 마세요.\n"
        f"{r_labels}"
    )
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
    user_prompt += (
        "\n\n[서비스 해설의 자연스러움과 상황 정확성]\n"
        "1. 질문 대상 플레이의 기록을 우선 설명하세요. 질문의 표현과 실제 R/F 기록이 "
        "충돌하면 기록을 따르고, 앞뒤 플레이를 현재 플레이인 것처럼 설명하지 마세요.\n"
        "2. K 카드의 사전식 정의를 문장 중간에 그대로 끼워 넣지 마세요. "
        "설명이 필요할 때만 자연스럽고 짧은 야구 표현으로 풀어 쓰세요.\n"
        "3. 같은 플레이 결과나 아웃 원리를 여러 문장에서 반복하지 마세요. "
        "사건과 이유, 플레이 후 상태 변화 가운데 질문에 필요한 내용만 간결하게 설명하세요.\n"
        "4. 야구 용어를 설명할 때 R/F/K 근거와 어긋나는 표현이나 "
        "지나친 단정은 피하세요.\n"
        "5. 아웃카운트와 주자 변화를 설명할 때 F의 플레이 전후 상태를 구분하세요. "
        "3아웃으로 공격이 끝난 경우에는 주자가 다음 공격에도 남는 듯이 표현하지 마세요.\n"
        "6. 주자 진루나 득점의 원인이 제공된 근거에 없으면 "
        "추측해 이유를 만들어내지 마세요."
    )
    raw, meta = generate(SYSTEM_PROMPT, user_prompt, Commentary,
                         {"qid": item["qid"], "condition": "B2"})
    if not isinstance(raw, dict) or not isinstance(raw.get("sentences"), list):
        raise ValueError("Gemini response has no sentences list")

    verified = verify_service(raw, pool, item["players"],
                              lambda pairs: _checked_probabilities(p_support, pairs),
                              threshold=threshold)
    sentences = []
    target_scope_dropped = 0
    for sent in verified["sentences"]:
        if _is_unanchored_previous_play(sent, previous_r, previous_completed_r):
            target_scope_dropped += 1
            continue
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
        "dropped_count": len(verified["dropped"]) + target_scope_dropped,
        "verifier": {"threshold": threshold, "checked_sentences": len(raw["sentences"]),
                     "target_scope_dropped": target_scope_dropped},
        "generation": {"model": (meta or {}).get("model"), "cache_hit": (meta or {}).get("cache_hit")},
    }
