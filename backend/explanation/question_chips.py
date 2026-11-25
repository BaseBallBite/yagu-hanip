"""A4 질문 칩: 플레이 유형 태그별로 보여줄 질문 칩과, 칩별로 AI에 줄 질문·카드.

흐름
- 입구 칩 ``q.why``(「한입만🍙」)는 모든 플레이 공통. 누르면 기본 해설 2~3문장.
- 그 아래 「한입 더」 후속 칩 1~2개는 플레이의 유형 태그(B3)로 정한다.
- 자유 입력은 이번 범위에서 뺀다. 질문 문장은 칩 ID로 고정한다.

허용 범위
- 허용: 규칙 이유, 용어 뜻, 그 규칙·용어가 이번 플레이에 적용된 방식
- 제외: 선수 평가, 예측·작전 평가, 심리·의도 단정, 오심 여부, 카드에 없는 기록

칩 ID는 생성 캐시 키(qid)에 들어가므로 문장(label)을 바꿔도 ID는 유지한다.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

ENTRY_CHIP = "q.why"
FALLBACK_TAG = "기타"


@dataclass(frozen=True)
class Chip:
    id: str
    label: str          # 화면에 보이는 칩 문장
    question: str       # AI에 넘기는 질문 문장
    card_ids: tuple[str, ...] = ()  # 이 질문에 답하려면 꼭 필요한 사전 카드


def _chip(cid: str, label: str, cards: tuple[str, ...] = (), question: str | None = None) -> Chip:
    return Chip(cid, label, question or label, cards)


CHIPS: dict[str, Chip] = {c.id: c for c in [
    _chip("q.why", "한입만🍙",
          question="이 플레이에서 무슨 일이 일어났고, 어떤 규칙이나 용어 때문에 그렇게 됐는지 "
                   "야구 초보자에게 2~3문장으로 쉽게 설명해줘."),
    _chip("q.apply", "이게 이번 플레이에서는 어떻게 적용됐어?"),
    _chip("q.rule_iff", "공을 못 잡아도 왜 타자가 아웃이야?", ("rule.infield_fly",)),
    _chip("q.rule_balk", "보크가 뭐고 왜 주자가 진루해?", ("rule.balk",)),
    _chip("q.rule_force", "태그 없이 베이스만 밟아도 아웃인 이유가 뭐야?", ("rule.force_play",)),
    _chip("q.rule_tagup", "공을 잡은 뒤에 뛰어도 되는 이유가 뭐야?", ("rule.tag_up",)),
    _chip("q.rule_drop3", "삼진인데 왜 1루로 뛰어?", ("rule.dropped_third_strike",)),
    _chip("q.rule_hbp", "공에 맞으면 왜 1루로 가?", ("rule.hit_by_pitch",)),
    _chip("q.rule_walk", "볼넷은 어떤 규칙이야?", ("rule.base_on_balls", "term.ball")),
    _chip("q.rule_interf", "방해는 언제 선언돼?", ("rule.interference", "rule.obstruction")),
    _chip("q.rule_review", "비디오 판독은 언제 쓸 수 있어?", ("rule.video_review",)),
    _chip("q.rule_pc", "투수 교체에는 어떤 규칙이 있어?", ("term.pitching_change", "rule.three_batter_minimum")),
    _chip("q.term_dp", "병살은 어떻게 만들어져?", ("term.double_play",)),
    _chip("q.term_hit", "이건 어떤 안타로 기록돼?", ("term.hit",)),
    _chip("q.term_out", "어떤 타구였고 어떻게 아웃이 됐어?", ("term.out",)),
    _chip("q.term_error", "왜 안타가 아니라 실책이야?", ("term.error", "term.hit")),
    _chip("q.term_fc", "야수선택은 뭐야?", ("term.fielders_choice",)),
    _chip("q.term_wp_pb", "폭투와 포일은 뭐가 달라?", ("term.wild_pitch", "term.passed_ball")),
    _chip("q.term_steal", "도루 성공과 실패는 어떻게 가려?", ("term.stolen_base", "term.caught_stealing")),
    _chip("q.term_pickoff", "견제사는 어떻게 아웃이 돼?", ("term.pickoff",)),
    _chip("q.term_sac", "희생번트·희생플라이는 왜 타수로 안 세?",
          ("term.sacrifice_bunt", "term.sacrifice_fly", "term.at_bat")),
    _chip("q.term_k", "삼진은 어떻게 기록돼?", ("term.strikeout",)),
]}

# 유형 태그 → 후속 칩. 순서가 우선순위다(태그가 여러 개면 위쪽 행을 쓴다).
TAG_CHIPS: dict[str, tuple[str, ...]] = {
    "STRIKEOUT": ("q.apply", "q.term_k"),
    "DROPPED_THIRD_STRIKE": ("q.rule_drop3",),
    "INFIELD_FLY": ("q.rule_iff", "q.apply"),
    "BALK": ("q.rule_balk", "q.apply"),
    "SAC_FLY": ("q.rule_tagup", "q.term_sac"),
    "SAC_BUNT": ("q.term_sac",),
    "TAG_UP": ("q.rule_tagup", "q.apply"),
    "DOUBLE_PLAY": ("q.term_dp",),
    "FORCE_OUT": ("q.rule_force", "q.apply"),
    "WILD_PITCH": ("q.term_wp_pb", "q.apply"),
    "PASSED_BALL": ("q.term_wp_pb", "q.apply"),
    "HIT_BY_PITCH": ("q.rule_hbp", "q.apply"),
    "WALK": ("q.rule_walk", "q.apply"),
    "INTENTIONAL_WALK": ("q.rule_walk", "q.apply"),
    "INTERFERENCE": ("q.rule_interf",),
    "OBSTRUCTION": ("q.rule_interf",),
    "VIDEO_REVIEW": ("q.rule_review",),
    "SINGLE": ("q.term_hit", "q.apply"),
    "DOUBLE": ("q.term_hit", "q.apply"),
    "TRIPLE": ("q.term_hit", "q.apply"),
    "HOME_RUN": ("q.term_hit", "q.apply"),
    "GROUNDOUT": ("q.term_out",),
    "FLYOUT": ("q.term_out",),
    "LINEOUT": ("q.term_out",),
    "ERROR": ("q.term_error", "q.apply"),
    "FIELDERS_CHOICE": ("q.term_fc",),
    "STOLEN_BASE": ("q.term_steal", "q.apply"),
    "CAUGHT_STEALING": ("q.term_steal", "q.apply"),
    "PICKOFF": ("q.term_pickoff", "q.apply"),
    "PITCHING_CHANGE": ("q.rule_pc", "q.apply"),
}
FALLBACK_CHIPS: tuple[str, ...] = ("q.apply",)


def pick_tag(tags: list[str]) -> str:
    """플레이의 유형 태그 중 매핑표에서 가장 위에 있는 것. 없으면 '기타'."""
    upper = {t.upper() for t in tags if isinstance(t, str)}
    for tag in TAG_CHIPS:
        if tag in upper:
            return tag
    return FALLBACK_TAG


def follow_up_ids(tags: list[str]) -> tuple[str, ...]:
    tag = pick_tag(tags)
    return TAG_CHIPS.get(tag, FALLBACK_CHIPS)


def play_tags(con: sqlite3.Connection, game_id: str, play_id: str) -> list[str] | None:
    """플레이의 유형 태그. 플레이가 없으면 None."""
    row = con.execute(
        "SELECT type_tags FROM plays WHERE game_id = ? AND play_id = ?", (game_id, play_id)
    ).fetchone()
    if row is None:
        return None
    try:
        tags = json.loads(row[0] or "[]")
    except (TypeError, ValueError):
        return []
    return [t for t in tags if isinstance(t, str)] if isinstance(tags, list) else []


def chips_for_play(con: sqlite3.Connection, game_id: str, play_id: str) -> dict | None:
    """화면에 줄 칩 목록. 플레이가 없으면 None."""
    tags = play_tags(con, game_id, play_id)
    if tags is None:
        return None
    entry = CHIPS[ENTRY_CHIP]
    return {
        "game_id": game_id,
        "play_id": play_id,
        "tag": pick_tag(tags),
        "entry": {"id": entry.id, "label": entry.label},
        "follow_ups": [{"id": cid, "label": CHIPS[cid].label} for cid in follow_up_ids(tags)],
    }


def allowed_chip_ids(tags: list[str]) -> set[str]:
    return {ENTRY_CHIP, *follow_up_ids(tags)}
