"""B4 플레이의 K(규칙/용어 카드) 자동 선정. DB와 사전은 읽기 전용.

선정 우선순위는 AI-A 11/13 make_testset.py 의 play_type()/pick_cards()와 동일하다.
서비스에서 Downloads 폴더의 실험용 스크립트를 참조하지 않도록 해당 규칙만 포함한다.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

DICT_PATH = Path(__file__).resolve().parents[2] / "data" / "dict" / "dict.json"

RULE_EVENTS = {"INFIELD_FLY", "DROPPED_THIRD_STRIKE", "SAC_FLY", "TRIPLE_PLAY"}
RULE_TAGS = {"BALK", "INTERFERENCE", "OBSTRUCTION", "VIDEO_REVIEW"}
SITU_EVENTS = {"DOUBLE_PLAY", "FORCE_OUT", "SAC_BUNT", "ERROR", "FIELDERS_CHOICE", "INTENTIONAL_WALK"}
SITU_TAGS = {"WILD_PITCH", "PASSED_BALL", "STOLEN_BASE", "CAUGHT_STEALING", "PICKOFF"}
SKILL_EVENTS = {"STRIKEOUT", "HOME_RUN", "DOUBLE", "TRIPLE", "SINGLE", "FLYOUT", "GROUNDOUT", "LINEOUT", "WALK", "HIT_BY_PITCH"}

# 원본 make_testset.py의 GENERIC. 별칭으로만 매칭될 경우 제외한다.
GENERIC = {
    "term.batter", "term.runner", "term.pitcher", "term.catcher", "term.infielder",
    "term.outfielder", "term.foul_tip", "term.inning", "term.out",
    "rule.substitution", "term.batting_order", "term.base", "term.run",
}


def play_type(play: dict) -> tuple[str | None, str]:
    """AI-A play_type과 같은 방식으로 카드 선정용 sub를 결정한다."""
    ev, tags = play["event_type"], set(play["tags"])
    if ev in RULE_EVENTS or (tags & RULE_TAGS):
        return "rule", (sorted(tags & RULE_TAGS)[0] if tags & RULE_TAGS and ev not in RULE_EVENTS else ev)
    if ev in SITU_EVENTS or (tags & SITU_TAGS):
        return "situation", (sorted(tags & SITU_TAGS)[0] if tags & SITU_TAGS and ev not in SITU_EVENTS else ev)
    if ev in SKILL_EVENTS:
        return "skill", ev
    return None, ev


def pick_cards(play: dict, dictionary: dict, k: int = 3, sub: str | None = None) -> list[str]:
    """AI-A make_testset.py의 pick_cards() 우선순위를 보존한다."""
    cards, alias, ev_idx = dictionary["cards"], dictionary["alias_index"], dictionary["event_index"]
    ids: list[str] = []
    keys = ([sub] if sub else []) + [play["event_type"]] + list(play["tags"])
    for key in keys:  # 이름과 직접 일치하는 카드 1장 우선
        for prefix in ("rule.", "term."):
            cid = prefix + key.lower()
            if cid in cards and cid not in ids:
                ids.append(cid)
    ids = ids[:1]

    candidates: list[str] = []
    for key in keys:
        candidates += ev_idx.get(key, [])
    # 동률이면 event_index의 원래 순서를 유지한다(원본 sorted의 안정 정렬).
    candidates = sorted(dict.fromkeys(candidates), key=lambda cid: len(cards[cid].get("event_types", [])))
    ids += [cid for cid in candidates if cid not in ids][: 2 - len(ids) if len(ids) < 2 else 1]

    for fact in play["facts"]:
        text, index = fact.replace(" ", ""), 0
        while index < len(text):
            for token in alias:  # dict.json의 alias_index 순서를 그대로 사용
                if token and text.startswith(token, index):
                    cid = alias[token]
                    if cid not in ids and cid not in GENERIC and cards[cid]["category"] != "경기 운영":
                        ids.append(cid)
                    index += len(token) - 1
                    break
            index += 1
    return ids[:k]


def get_cards_for_play(
    con: sqlite3.Connection,
    game_id: str,
    play_id: str,
    dict_path: Path = DICT_PATH,
) -> dict | None:
    """B4의 이벤트·태그·F를 이용해 최대 3장 카드 ID를 반환한다."""
    if not game_id or not play_id:
        return None
    row = con.execute(
        "SELECT seq, event_type, type_tags, facts FROM plays WHERE game_id = ? AND play_id = ?",
        (game_id, play_id),
    ).fetchone()
    if row is None:
        return None
    seq, event_type, tags_json, facts_json = row[0], row[1], row[2], row[3]
    tags = json.loads(tags_json)
    facts = json.loads(facts_json)
    play = {
        "event_type": event_type.upper(),  # B4 lowercase -> AI-A uppercase 이벤트 명
        "tags": [tag.upper() for tag in tags],
        "facts": [fact["text"] for fact in facts],
    }
    _, sub = play_type(play)
    dictionary = json.loads(Path(dict_path).read_text(encoding="utf-8"))
    ids = pick_cards(play, dictionary, sub=sub)
    # 삼진이라는 이벤트만으로 파울 팁 여부는 알 수 없다.
    # B4 사실 또는 이벤트 태그에 파울 팁이 명시된 경우에만 해당 카드를 제공한다.
    # 단순한 "파울" 또는 "헛스윙" 기록은 파울 팁의 증거가 아니다.
    if play["event_type"] == "STRIKEOUT" and "term.foul_tip" in ids:
        explicit_foul_tip = "FOUL_TIP" in play["tags"] or any(
            re.search(r"파울\s*팁|foul[\s_-]*tip", fact, re.IGNORECASE)
            for fact in play["facts"]
        )
        if not explicit_foul_tip:
            ids.remove("term.foul_tip")

    # SINGLE 이벤트만으로 내야안타인지 판단할 수 없다.
    # 명시적인 외야 안타 기록이 있을 때만 내야안타 카드를 제외한다.
    if play["event_type"] == "SINGLE" and "term.infield_hit" in ids:
        hit_records = [fact for fact in play["facts"] if fact.startswith("기록:")]
        if any(
            re.search(r"좌익수|중견수|우익수", fact) and "내야안타" not in fact
            for fact in hit_records
        ):
            ids.remove("term.infield_hit")

    # 주자 없는 땅볼 아웃은 주자를 진루시키는 진루타가 될 수 없다.
    # 주자 유무가 불명확하면 기존 카드 선정을 유지한다.
    if play["event_type"] == "GROUNDOUT" and "term.productive_out" in ids:
        before = next(
            (fact for fact in play["facts"] if re.match(r"^\d+회[초말],", fact)),
            None,
        )
        if before and re.search(r"(?:^|,\s*)주자 없음(?:,|$)", before):
            ids.remove("term.productive_out")

    # 이벤트 종류만으로는 만루홈런 여부를 알 수 없다. B4 득점 사실이
    # 명시되어 있고 4득점이 아니라면 만루홈런 카드는 제거한다.
    # 득점 정보가 없으면 추측하여 제거하지 않는다.
    if play["event_type"] == "HOME_RUN" and "term.grand_slam" in ids:
        for fact in play["facts"]:
            match = re.search(r"이 플레이로 득점:\s*.*?\s+(\d+)점", fact)
            if match:
                if int(match.group(1)) != 4:
                    ids.remove("term.grand_slam")
                break
    return {
        "game_id": game_id,
        "play_id": play_id,
        "seq": seq,
        "card_ids": ids,
        "card_source": "auto",
    }
