
"""R 원문 조회 함수 단위 테스트."""

import sqlite3
import unittest

from backend.explanation.relay_lookup import get_raw_relay_for_play


class RelayLookupTest(unittest.TestCase):

    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.con.row_factory = sqlite3.Row

        self.con.execute(
            """
            CREATE TABLE plays (
                game_id TEXT,
                seq INTEGER,
                play_id TEXT,
                description TEXT
            )
            """
        )

        self.con.executemany(
            "INSERT INTO plays VALUES (?, ?, ?, ?)",
            [
                ("GAME1", 1, "PLAY1", "타자가 안타를 기록했다."),
                ("GAME1", 2, "PLAY2", "투수가 교체되었다."),
                ("GAME2", 1, "PLAY3", None),
            ],
        )

    def tearDown(self):
        self.con.close()

    def test_existing_play(self):
        result = get_raw_relay_for_play(
            self.con, "GAME1", "PLAY1"
        )

        self.assertEqual(result["seq"], 1)
        self.assertEqual(
            result["raw_relay"],
            ["타자가 안타를 기록했다."],
        )

    def test_missing_play(self):
        result = get_raw_relay_for_play(
            self.con, "GAME1", "UNKNOWN"
        )
        self.assertIsNone(result)

    def test_game_mismatch(self):
        result = get_raw_relay_for_play(
            self.con, "GAME2", "PLAY1"
        )
        self.assertIsNone(result)

    def test_null_description(self):
        result = get_raw_relay_for_play(
            self.con, "GAME2", "PLAY3"
        )
        self.assertEqual(result["raw_relay"], [])

    def test_empty_input(self):
        self.assertIsNone(
            get_raw_relay_for_play(self.con, "", "PLAY1")
        )


if __name__ == "__main__":
    unittest.main()