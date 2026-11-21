"""일반 경기 해설용 R/F/K 입력 묶음 생성 (DB/사전 읽기 전용).

AI-A ``ai.explain.prompts`` 가 요구하는 item 형식만 조립한다.
Gemini 호출, 검증, 시연용 해설 JSON 읽기는 이 모듈의 역할이 아니다.
"""

from __future__ import annotations

from hashlib import sha256
import sqlite3
from pathlib import Path

from backend.explanation.cards_lookup import DICT_PATH, get_cards_for_play
from backend.explanation.facts_lookup import get_facts_for_play
from backend.explanation.relay_context import get_relay_context_for_play


def build_explanation_input(
    con: sqlite3.Connection,
    game_id: str,
    play_id: str,
    question: str,
    *,
    dict_path: Path = DICT_PATH,
) -> dict | None:
    """동일 game_id/play_id의 R/F/K를 합쳐 AI-A 입력 dict를 반환.

    플레이 미존재 또는 해설 제외 이벤트면 ``None``.
    ``players``는 B4에 실제로 기록된 타자/투수 이름만 포함하므로
    추후 2단계 검증 연동에서는 전체 선수 명단과 대조해야 한다.
    """
    if not game_id or not play_id:
        return None
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string")

    relay = get_relay_context_for_play(con, game_id, play_id)
    if relay is None:
        return None
    facts = get_facts_for_play(con, game_id, play_id)
    cards = get_cards_for_play(con, game_id, play_id, dict_path=dict_path)
    if facts is None or cards is None:
        raise RuntimeError("R/F/K lookup mismatch")
    identity = {(x['game_id'], x['play_id'], x['seq']) for x in (relay, facts, cards)}
    if len(identity) != 1:
        raise RuntimeError("R/F/K game_id, play_id, or seq mismatch")

    # ID/조건 기반 생성 캐시를 추후 사용할 때, 질문 변경을 구분하도록 한다.
    q = question.strip()
    question_hash = sha256(q.encode("utf-8")).hexdigest()[:16]
    qid = f"SERVICE:{game_id}:{play_id}:{question_hash}"

    # 선수 이름 검증에 필요한 임시 명단. B4에서 투입·타격 기록이 없는
    # 선수는 빠질 수 있으므로, 이 결과만으로 완전한 로스터를 보장하지 않는다.
    names = set()
    for batter, pitcher in con.execute(
        "SELECT batter, pitcher FROM plays WHERE game_id = ?", (game_id,)
    ):
        for name in (batter, pitcher):
            if isinstance(name, str) and name.strip():
                names.add(name.strip())

    return {
        "qid": qid,
        "game_id": game_id,
        "play_id": play_id,
        "seq": relay["seq"],
        "question": q,
        "raw_relay": relay["raw_relay"],
        "raw_relay_source_seqs": relay["source_seqs"],
        "facts": facts["facts"],
        "type_tags": facts["type_tags"],
        "card_ids": cards["card_ids"],
        "card_source": cards["card_source"],
        "players": sorted(names),
    }
