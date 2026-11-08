"""B7 사전·검색 API.

data/dict/dict.json(카드 원본은 cards/ 의 yaml)을 읽어서 사전 화면에 필요한 조회를 제공한다.
카드 내용은 여기서 고치지 않는다. 카드를 고치려면 cards/ 의 yaml 을 고치고 build_dict.py 를 다시 돌린다.

엔드포인트 (접두어 /dict):
    GET /dict/categories            구분(규칙/용어)별 카테고리와 카드 수
    GET /dict/cards                 카드 목록 (kind, category 로 거르기)
    GET /dict/cards/{card_id}       카드 상세 + 관련 카드 요약
    GET /dict/search?q=...          제목·별칭·설명 검색 (공백 무시, 별칭 포함)
    GET /dict/events/{event_type}   경기 이벤트에 연결된 카드
    GET /dict/aliases               용어 밑줄용 별칭 표 (긴 표기부터)
"""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DICT_PATH = REPO_ROOT / "data" / "dict" / "dict.json"

KIND_LABELS = {"rule": "규칙", "term": "용어"}
# 카드 템플릿(cards/_template.yaml)에 적힌 카테고리 순서. 목록에 없는 카테고리는 뒤에 붙인다.
CATEGORY_ORDER = {
    "rule": ["기본 규칙", "타격 규칙", "주루 규칙", "수비 규칙", "특수 상황"],
    "term": ["투구·구종", "타격", "주루", "수비", "기록·통계", "경기 운영"],
}
SUMMARY_FIELDS = ("id", "kind", "title", "category", "one_liner", "review_status")

_SPACE_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """검색 비교용: 공백을 모두 빼고 소문자로 바꾼다. (alias_index 키와 같은 방식)"""
    return _SPACE_RE.sub("", text).lower()


class DictStore:
    def __init__(self, data: dict[str, Any]) -> None:
        self.cards: dict[str, dict] = data["cards"]
        self.alias_index: dict[str, str] = data.get("alias_index", {})
        self.event_index: dict[str, list[str]] = data.get("event_index", {})
        # 검색용으로 미리 정규화해 둔다.
        self._norm_title = {cid: normalize(c["title"]) for cid, c in self.cards.items()}
        self._norm_aliases = {
            cid: [normalize(a) for a in c.get("aliases", [])] for cid, c in self.cards.items()
        }
        self._norm_text = {
            cid: normalize(c.get("one_liner", "") + " " + c.get("easy", ""))
            for cid, c in self.cards.items()
        }

    @classmethod
    def from_file(cls, path: Path) -> "DictStore":
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f))

    # ---- 조회 ----

    def summary(self, card: dict) -> dict:
        return {k: card.get(k) for k in SUMMARY_FIELDS}

    def categories(self) -> list[dict]:
        result = []
        for kind, label in KIND_LABELS.items():
            counts: dict[str, int] = {}
            for c in self.cards.values():
                if c["kind"] == kind:
                    counts[c["category"]] = counts.get(c["category"], 0) + 1
            order = CATEGORY_ORDER.get(kind, [])
            names = [n for n in order if n in counts] + sorted(n for n in counts if n not in order)
            result.append({
                "kind": kind,
                "label": label,
                "count": sum(counts.values()),
                "categories": [{"name": n, "count": counts[n]} for n in names],
            })
        return result

    def list_cards(self, kind: str | None = None, category: str | None = None) -> list[dict]:
        cards = [
            c for c in self.cards.values()
            if (kind is None or c["kind"] == kind) and (category is None or c["category"] == category)
        ]
        cards.sort(key=lambda c: (c["kind"], c["category"], c["title"]))
        return [self.summary(c) for c in cards]

    def get_card(self, card_id: str) -> dict | None:
        card = self.cards.get(card_id)
        if card is None:
            return None
        related = []
        for rid in card.get("related", []):
            rc = self.cards.get(rid)
            # 아직 없는 카드를 가리킬 수 있다(빌드 때 경고만 뜸). 화면이 링크를 끌 수 있게 표시한다.
            related.append(
                {"id": rid, "exists": rc is not None,
                 "title": rc["title"] if rc else None,
                 "one_liner": rc["one_liner"] if rc else None}
            )
        return {**card, "related_cards": related}

    def search(self, q: str, limit: int = 20) -> list[dict]:
        """제목 > 별칭 > 설명 순으로 점수를 매긴다. 같은 점수면 제목이 짧은 카드가 먼저."""
        nq = normalize(q)
        if not nq:
            return []
        hits = []
        for cid, card in self.cards.items():
            title = self._norm_title[cid]
            aliases = self._norm_aliases[cid]
            if title == nq:
                score, by = 100, "title"
            elif nq in aliases:
                score, by = 90, "alias"
            elif title.startswith(nq):
                score, by = 70, "title"
            elif any(a.startswith(nq) for a in aliases):
                score, by = 60, "alias"
            elif nq in title:
                score, by = 50, "title"
            elif any(nq in a for a in aliases):
                score, by = 40, "alias"
            elif nq in self._norm_text[cid]:
                score, by = 10, "text"
            else:
                continue
            hits.append((score, len(card["title"]), card["title"], by, card))
        hits.sort(key=lambda h: (-h[0], h[1], h[2]))
        return [{**self.summary(card), "matched_by": by, "score": score}
                for score, _, _, by, card in hits[:limit]]

    def cards_for_event(self, event_type: str) -> list[dict]:
        ids = self.event_index.get(event_type.upper(), [])
        return [self.summary(self.cards[i]) for i in ids if i in self.cards]


@lru_cache(maxsize=1)
def get_store() -> DictStore:
    path = Path(os.environ.get("DICT_PATH", DEFAULT_DICT_PATH))
    return DictStore.from_file(path)


router = APIRouter(prefix="/dict", tags=["dictionary"])


@router.get("/categories")
def categories() -> list[dict]:
    return get_store().categories()


@router.get("/cards")
def list_cards(
    kind: str | None = Query(None, pattern="^(rule|term)$", description="rule(규칙) 또는 term(용어)"),
    category: str | None = Query(None, description="예: 주루 규칙, 투구·구종"),
) -> dict:
    items = get_store().list_cards(kind, category)
    return {"count": len(items), "items": items}


@router.get("/cards/{card_id}")
def card_detail(card_id: str) -> dict:
    card = get_store().get_card(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"카드를 찾을 수 없어요: {card_id}")
    return card


@router.get("/search")
def search(
    q: str = Query(..., min_length=1, description="검색어. 공백은 무시하고 별칭도 찾음"),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    items = get_store().search(q, limit)
    return {"query": q, "count": len(items), "items": items}


@router.get("/events/{event_type}")
def cards_for_event(event_type: str) -> dict:
    items = get_store().cards_for_event(event_type)
    return {"event_type": event_type.upper(), "count": len(items), "items": items}


@router.get("/aliases")
def aliases() -> dict:
    """해설 문장에 밑줄을 칠 때 쓰는 표. 키는 공백을 뺀 표기, 값은 카드 id. 긴 표기부터 정렬돼 있다."""
    return get_store().alias_index
