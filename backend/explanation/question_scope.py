"""Conservative preflight check for a question about the *wrong batter's* play.

This only rejects a narrow, explicit mismatch. It is not a semantic question
parser: ambiguous and multi-player/context questions continue to the existing
R/F/K -> Gemini -> verifier flow. Read-only database access.
"""
from __future__ import annotations

import re
import sqlite3

# Only single-batter outcome plays. Runner events are deliberately excluded:
# asking about a runner rather than the current batter is often correct.
_BATTER_OUTCOME_EVENTS = {
    "groundout", "flyout", "lineout", "popout", "strikeout",
    "single", "double", "triple", "home_run", "walk", "hit_by_pitch",
    "double_play", "sac_fly", "sac_bunt",
}
_OUTCOME_WORDS = re.compile(
    r"땅볼|플라이|뜬공|라인드라이브|삼진|안타|홈런|볼넷|"
    r"사구|몸에\s*맞|병살|희생(?:번트|플라이)|아웃"
)
# If the question explicitly concerns context or runners, do not reject it.
_CONTEXT_WORDS = re.compile(
    r"앞서|앞선|이전|직전|그\s*전|이후|다음|"
    r"주자|진루|도루|득점|타점|실책|송구|비교|연속"
)


def question_targets_another_batter(
    con: sqlite3.Connection, game_id: str, play_id: str, question: str
) -> bool:
    """True only for a clearly named *other batter* with a finished-play term.

    This avoids guessing about generic questions, pitcher/runner involvement,
    references to the target batter, and contextual multi-play questions.
    """
    target = con.execute(
        "SELECT batter, pitcher, event_type, description "
        "FROM plays WHERE game_id=? AND play_id=?",
        (game_id, play_id),
    ).fetchone()
    if target is None:
        return False  # The API handles missing play_id separately (404).
    if len(target) != 4:
        # Partial test doubles cannot establish a mismatch; do not guess.
        return False

    batter, pitcher, event_type, description = target
    if not isinstance(batter, str) or not batter.strip():
        return False
    if not isinstance(event_type, str) or event_type.lower() not in _BATTER_OUTCOME_EVENTS:
        return False

    q = question.strip()
    batter = batter.strip()
    if batter in q or not _OUTCOME_WORDS.search(q) or _CONTEXT_WORDS.search(q):
        return False

    # Only recognize explicit names of batters appearing in this *same game*.
    # A named runner, fielder, or pitcher must not be mistaken for a wrong batter.
    other_batters = {
        name.strip() for (name,) in con.execute(
            "SELECT DISTINCT batter FROM plays "
            "WHERE game_id=? AND batter IS NOT NULL AND batter<>?",
            (game_id, batter),
        )
        if isinstance(name, str) and len(name.strip()) >= 2
        and name.strip() != (pitcher or "").strip()
        and name.strip() in q
    }
    if len(other_batters) != 1:
        return False
    other = next(iter(other_batters))
    # If the other player is explicitly part of this play's own record, the
    # question may refer to a legitimate participant rather than another play.
    if other in (description or ""):
        return False
    return True
