
"""B4 DB에서 플레이별 R(원문 중계)을 읽기 전용으로 조회한다."""

import sqlite3


def get_raw_relay_for_play(
    con: sqlite3.Connection,
    game_id: str,
    play_id: str,
) -> dict | None:
    """특정 플레이의 원문 중계 1건을 조회한다."""

    if not game_id or not play_id:
        return None

    row = con.execute(
        """
        SELECT seq, description
        FROM plays
        WHERE game_id = ? AND play_id = ?
        """,
        (game_id, play_id),
    ).fetchone()

    if row is None:
        return None

    seq, description = row[0], row[1]

    return {
        "game_id": game_id,
        "play_id": play_id,
        "seq": seq,
        "raw_relay": [description] if description is not None else [],
    }