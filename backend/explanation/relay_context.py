"""서비스용 B4 문자중계 문맥(R) 조회 (읽기 전용).

AI-A build_testset.py 의 앞 6줄/뒤 1줄 규칙을 적용한다.
투수판 이탈 행은 서비스 해설 근거에서 제외한다.
기존 플레이 한 줄 조회(get_raw_relay_for_play)는 변경하지 않는다.
"""

from __future__ import annotations

import re
import sqlite3

_PITCH_RE = re.compile(r"^\s*\d+구")
_RUNNER_LINE_RE = re.compile(r"^\s*(?:[123]루주자|타자주자)")
_EXCLUDED = {"pitcher_disengagement", "PITCHER_STEP_OFF"}


def _is_pitch(row: dict) -> bool:
    return bool(_PITCH_RE.match(row["description"] or ""))


def _is_excluded(row: dict) -> bool:
    return row["event_type"] in _EXCLUDED


def get_relay_context_for_play(
    con: sqlite3.Connection,
    game_id: str,
    play_id: str,
    before_n: int = 6,
    after_n: int = 1,
) -> dict | None:
    """해당 플레이의 R 근거와 인접한 원문 문맥을 조회한다.

    같은 반이닝 안에서 이전 비투구 6줄(현재 타석 투구는 별도 포함),
    대상 행, 뒤따르는 주자 기록 전부, 이후 비투구 1줄을 선택한다.
    결과의 ``raw_relay`` 는 ai.explain.prompts.raw_lines() 와 호환된다.
    ``source_seqs`` 는 R1, R2...에 대응하는 B4 seq (검증/추적용)다.
    이 함수는 DB에 어떤 쓰기도 하지 않는다.
    """
    if not game_id or not play_id:
        return None
    if any(type(n) is not int or n < 0 for n in (before_n, after_n)):
        raise ValueError("before_n / after_n must be non-negative integers")

    selected = con.execute(
        """SELECT seq, play_id, inning, half, event_type, description
           FROM plays WHERE game_id = ? ORDER BY seq""",
        (game_id,),
    ).fetchall()
    rows = [
        {"seq": r[0], "play_id": r[1], "inning": r[2], "half": r[3],
         "event_type": r[4], "description": r[5] or ""}
        for r in selected
    ]
    idx = next((i for i, r in enumerate(rows) if r["play_id"] == play_id), None)
    if idx is None:
        return None
    target = rows[idx]
    if _is_excluded(target):
        return None

    half = target["inning"], target["half"]
    same_half = lambda r: (r["inning"], r["half"]) == half

    before = []
    nonpitch_count = 0
    in_current_pa = True
    for row in reversed(rows[:idx]):
        if not same_half(row):
            break
        if _is_excluded(row):
            continue
        if _is_pitch(row):
            if in_current_pa:
                before.append(row)
            continue
        if nonpitch_count >= before_n:
            break
        before.append(row)
        nonpitch_count += 1
        if row["event_type"] == "batter_announcement":
            in_current_pa = False

    after = []
    j = idx + 1
    while j < len(rows) and same_half(rows[j]):
        row = rows[j]
        if _is_excluded(row):
            j += 1
            continue
        if not _RUNNER_LINE_RE.match(row["description"]):
            break
        after.append(row)
        j += 1

    nonpitch_count = 0
    while j < len(rows) and same_half(rows[j]) and nonpitch_count < after_n:
        row = rows[j]
        j += 1
        if _is_excluded(row) or _is_pitch(row):
            continue
        after.append(row)
        nonpitch_count += 1

    window = [*reversed(before), target, *after]
    nonempty = [row for row in window if row["description"].strip()]
    return {
        "game_id": game_id,
        "play_id": play_id,
        "seq": target["seq"],
        "raw_relay": [row["description"] for row in nonempty],
        "source_seqs": [row["seq"] for row in nonempty],
    }
