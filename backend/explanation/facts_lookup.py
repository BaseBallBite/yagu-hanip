"""기존 B4 DB에서 플레이별 F 근거를 읽기 전용으로 조회한다."""

import sqlite3
from backend.game import store


def get_facts_for_play(
    con: sqlite3.Connection,
    game_id: str,
    play_id: str,
) -> dict | None:
    if not game_id or not play_id:
        return None

    row = con.execute(
        "SELECT seq FROM plays WHERE game_id = ? AND play_id = ?",
        (game_id, play_id),
    ).fetchone()

    if row is None:
        return None

    play = store.get_play(con, game_id, row["seq"])

    if play is None or play["play_id"] != play_id:
        raise RuntimeError("조회된 플레이 ID가 일치하지 않습니다")

    return {
        "game_id": game_id,
        "play_id": play_id,
        "seq": play["seq"],
        "facts": play["facts"],
        "type_tags": play["type_tags"],
    }
