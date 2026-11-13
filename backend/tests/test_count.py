"""투구별 볼·스트라이크 카운트 규칙 테스트.

실행 (저장소 루트에서):
    .venv/bin/python -m unittest backend.tests.test_count -v
"""

import unittest

from backend.game.count import RAW_DIR, apply, pitch_kind, verify
from backend.game.facts import B2_DIR

GAME = "20260328HTSK02026"


def run(results: list[str]) -> tuple[int, int]:
    b = s = 0
    for text in results:
        b, s = apply(b, s, pitch_kind({"result_text": text}))
    return b, s


class CountRuleTest(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(run(["볼", "스트라이크", "헛스윙", "볼"]), (2, 2))

    def test_foul_stops_at_two_strikes(self):
        self.assertEqual(run(["파울", "파울", "파울", "파울"]), (0, 2))

    def test_bunt_foul_with_two_strikes_is_strikeout(self):
        self.assertEqual(run(["스트라이크", "파울", "번트파울"]), (0, 3))

    def test_in_play_keeps_count(self):
        self.assertEqual(run(["볼", "타격"]), (1, 0))

    def test_pitch_clock(self):
        self.assertEqual(run(["피치클락 투수위반 볼", "피치클락 타자위반 스트라이크"]), (1, 1))

    def test_foul_fly_error_is_a_note_not_a_new_pitch(self):
        # '포수 파울 플라이 포구 실책' 은 바로 앞 파울을 설명하는 줄이다
        self.assertEqual(run(["파울", "포수 파울 플라이 포구 실책", "볼"]), (1, 1))

    def test_code_wins_over_text(self):
        self.assertEqual(pitch_kind({"result_code_raw": "S", "result_text": "헛스윙"}), "strike")


@unittest.skipUnless((B2_DIR / f"{GAME}.json").exists() and (RAW_DIR / GAME).exists(),
                     "data/raw 에 B2 상태 또는 시즌 원본이 없음")
class CountMatchesNaverTest(unittest.TestCase):
    def test_matches_raw_current_game_state(self):
        stat = verify([GAME])["stat"]
        self.assertGreater(stat.get("match", 0), 250)
        self.assertEqual(stat.get("mismatch", 0), 0)


if __name__ == "__main__":
    unittest.main()
