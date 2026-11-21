import sqlite3
import unittest
from unittest.mock import patch

from backend.explanation.facts_lookup import get_facts_for_play


class FactsLookupTests(unittest.TestCase):

    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.con.row_factory = sqlite3.Row

        self.con.execute("""
            CREATE TABLE plays (
                game_id TEXT NOT NULL,
                seq INTEGER NOT NULL,
                play_id TEXT NOT NULL UNIQUE,
                PRIMARY KEY (game_id, seq)
            )
        """)

        self.con.execute(
            "INSERT INTO plays VALUES (?, ?, ?)",
            ("SYNTHETIC_GAME", 1, "SYNTHETIC_PLAY")
        )

    def tearDown(self):
        self.con.close()

    def test_valid_play(self):
        fake_play = {
            "play_id": "SYNTHETIC_PLAY",
            "seq": 1,
            "facts": [{"id": "F1", "text": "Synthetic fact"}],
            "type_tags": ["single"],
        }

        with patch(
            "backend.explanation.facts_lookup.store.get_play",
            return_value=fake_play
        ):
            result = get_facts_for_play(
                self.con, "SYNTHETIC_GAME", "SYNTHETIC_PLAY"
            )

        self.assertEqual(result["seq"], 1)
        self.assertEqual(result["facts"], fake_play["facts"])
        self.assertEqual(result["type_tags"], ["single"])

    def test_wrong_game(self):
        with patch(
            "backend.explanation.facts_lookup.store.get_play"
        ) as mocked:
            result = get_facts_for_play(
                self.con, "WRONG_GAME", "SYNTHETIC_PLAY"
            )
            mocked.assert_not_called()

        self.assertIsNone(result)

    def test_unknown_play(self):
        result = get_facts_for_play(
            self.con, "SYNTHETIC_GAME", "UNKNOWN_PLAY"
        )
        self.assertIsNone(result)

    def test_mismatched_play_id(self):
        with patch(
            "backend.explanation.facts_lookup.store.get_play",
            return_value={
                "play_id": "WRONG_PLAY",
                "seq": 1,
                "facts": [],
                "type_tags": [],
            }
        ):
            with self.assertRaises(RuntimeError):
                get_facts_for_play(
                    self.con, "SYNTHETIC_GAME", "SYNTHETIC_PLAY"
                )

    def test_empty_identifiers(self):
        self.assertIsNone(
            get_facts_for_play(self.con, "", "SYNTHETIC_PLAY")
        )
        self.assertIsNone(
            get_facts_for_play(self.con, "SYNTHETIC_GAME", "")
        )


if __name__ == "__main__":
    unittest.main()
