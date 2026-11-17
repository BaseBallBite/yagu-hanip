"""B2-generation -> B3-rule-verification adapter for a *trusted* evidence bundle.

This module performs NO file writes, network calls, database access, or evaluation-data
lookups. The caller owns the generator implementation and the trusted R/F/K resolver.
Model/KLUE validation is NOT implemented here; the final service policy is pending.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ai.explain.prompts import (Commentary, SYSTEM_PROMPT, build_user_prompt,
                                evidence_pool)
from ai.explain.verifier import verify


class EvidenceContractError(ValueError):
    """The backend-provided R/F/K bundle does not meet the agreed basic shape."""


def _validate(item: dict[str, Any], cards: dict[str, dict]) -> None:
    if not isinstance(item, dict) or not isinstance(cards, dict):
        raise EvidenceContractError("장면 근거 형식이 올바르지 않습니다")
    if not isinstance(item.get("question"), str) or not item["question"].strip():
        raise EvidenceContractError("질문이 비어 있습니다")
    if not isinstance(item.get("qid"), str) or not item["qid"].strip():
        raise EvidenceContractError("qid가 필요합니다")
    raw = item.get("raw_relay")
    facts = item.get("facts")
    ids = item.get("card_ids")
    players = item.get("players")
    if (not isinstance(raw, list) or not raw or
            any(not isinstance(x, str) or not x.strip() for x in raw)):
        raise EvidenceContractError("문자중계 R 목록이 필요합니다")
    if not isinstance(facts, list) or not facts:
        raise EvidenceContractError("플레이 사실 F 목록이 필요합니다")
    fact_ids = []
    for fact in facts:
        if (not isinstance(fact, dict) or not isinstance(fact.get("id"), str)
                or not fact["id"].startswith("F")
                or not fact["id"][1:].isdigit()
                or not isinstance(fact.get("text"), str) or not fact["text"].strip()):
            raise EvidenceContractError("F는 {'id':'F1','text':'...'} 형식이어야 합니다")
        fact_ids.append(fact["id"])
    if len(set(fact_ids)) != len(fact_ids):
        raise EvidenceContractError("F 근거 ID가 중복되었습니다")
    if (not isinstance(ids, list) or len(ids) > 3
            or any(not isinstance(x, str) or not x.strip() for x in ids)
            or len(set(ids)) != len(ids)):
        raise EvidenceContractError("카드 ID는 중복 없이 최대 3개까지 허용합니다")
    if not isinstance(players, list) or any(not isinstance(x, str) for x in players):
        raise EvidenceContractError("선수 이름 목록이 필요합니다")
    if any(cid not in cards for cid in ids):
        raise EvidenceContractError("등록되지 않은 카드 ID가 있습니다")
    if any(cid.startswith(('R', 'F')) and cid[1:].isdigit() for cid in ids):
        raise EvidenceContractError("카드 ID가 R/F 번호와 충돌합니다")


def run_rule_b3(
    item: dict[str, Any],
    cards: dict[str, dict],
    generate: Callable[[str, str, type, dict], tuple[dict, dict]],
) -> dict[str, Any]:
    """Generate B2 once, filter same sentences with AI-A verifier v2.

    `generate(system, prompt, Commentary, tag)` has GeminiRunner.generate signature,
    so the backend can inject that runner after source/approval is settled.
    `item` must be built by a *trusted backend provider*, not copied from the client.
    """
    _validate(item, cards)
    pool = evidence_pool(item, cards, "B2")
    prompt = build_user_prompt(item, cards, "B2")
    output, meta = generate(SYSTEM_PROMPT, prompt, Commentary,
                            {"qid": item["qid"], "condition": "B2"})
    if (not isinstance(output, dict) or not isinstance(output.get("sentences"), list)
            or not isinstance(meta, dict)):
        raise EvidenceContractError("생성 모델 응답 형식이 올바르지 않습니다")
    for sent in output["sentences"]:
        if (not isinstance(sent, dict) or not isinstance(sent.get("text"), str)
                or not isinstance(sent.get("evidence"), list)
                or any(not isinstance(e, str) for e in sent["evidence"])):
            raise EvidenceContractError("생성 문장에 text/evidence가 없습니다")

    # v2 preserves genuine [UNKNOWN] no-information statements. This is a
    # provisional rule-based check, not the team's unresolved KLUE policy.
    filtered = verify(output, pool, item["players"], "v2")
    sentences = []
    for sent in filtered["sentences"]:
        if not sent["text"].strip():
            continue
        cited_ids = sent["evidence"]
        sentences.append({
            "text": sent["text"],
            "cited_ids": cited_ids,
            "cited_text": [
                {"id": cid, "text": pool[cid] if cid in pool else "기록에 근거 없음 (확인할 수 없는 내용)"}
                for cid in cited_ids
            ],
            "verdict": sent["verdict"],
        })
    return {
        "condition": "B3",
        "verification": "rule_v2_provisional",
        "model_verification_applied": False,
        "sentences": sentences,
        "dropped_count": len(filtered["dropped"]),
        "empty": not bool(sentences),
        "meta": {"cache_hit": meta.get("cache_hit"), "model": meta.get("model")},
    }
