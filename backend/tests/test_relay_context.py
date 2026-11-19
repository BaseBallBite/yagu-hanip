"""B4 R 문맥 조회: 절단 규칙, 현재 타석 투구, 주자 후속, 투수판 이탈 제외."""

import sqlite3
import unittest

from backend.explanation.relay_context import get_relay_context_for_play


class RelayContextTests(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.con.execute(
            """CREATE TABLE plays (
                game_id TEXT, seq INTEGER, play_id TEXT,
                inning INTEGER, half TEXT, event_type TEXT, description TEXT
            )"""
        )
        self.data = [
            ("G", 1, "p1", 1, "bottom", "pitch", "1구 이전 반이닝"),
            ("G", 2, "p2", 2, "top", "inning_start", "2회초 공격"),
            ("G", 3, "p3", 2, "top", "batter_announcement", "1번타자 김철수"),
            ("G", 4, "p4", 2, "top", "single", "이전 타자 안타"),
            ("G", 5, "p5", 2, "top", "pitcher_disengagement", "투수 투수판 이탈"),
            ("G", 6, "p6", 2, "top", "play_notice", "경기 메모"),
            ("G", 7, "p7", 2, "top", "pitch", "1구 이전 타자 공"),
            ("G", 8, "p8", 2, "top", "batter_announcement", "2번타자 이영희"),
            ("G", 9, "p9", 2, "top", "pitch", "1구 스트라이크"),
            ("G", 10, "p10", 2, "top", "PITCHER_STEP_OFF", "투수 투수판 이탈2"),
            ("G", 11, "p11", 2, "top", "pitch", "2구 볼"),
            ("G", 12, "p12", 2, "top", "single", "타자 1루타"),
            ("G", 13, "p13", 2, "top", "runner_advance", "1루주자 김철수 : 3루 진루"),
            ("G", 14, "p14", 2, "top", "run_scored", "3루주자 홍길동 : 홈인"),
            ("G", 15, "p15", 2, "top", "pitch", "1구 뒤 타석 공"),
            ("G", 16, "p16", 2, "top", "pitcher_disengagement", "투수 투수판 이탈3"),
            ("G", 17, "p17", 2, "top", "batter_announcement", "3번타자 박준호"),
            ("G", 18, "p18", 2, "top", "single", "뒤 두번째 플레이"),
            ("G", 19, "p19", 2, "bottom", "inning_start", "2회말 공격"),
            ("OTHER", 1, "op1", 2, "top", "single", "다른 경기"),
        ]
        self.con.executemany("INSERT INTO plays VALUES (?,?,?,?,?,?,?)", self.data)

    def tearDown(self):
        self.con.close()

    def test_window_follows_testset_and_excludes_step_off(self):
        x = get_relay_context_for_play(self.con, "G", "p12")
        self.assertEqual(x["source_seqs"], [2, 3, 4, 6, 8, 9, 11, 12, 13, 14, 17])
        self.assertEqual(x["raw_relay"][0], "2회초 공격")
        self.assertEqual(x["raw_relay"][-1], "3번타자 박준호")
        self.assertTrue(all("투수판 이탈" not in t for t in x["raw_relay"]))
        self.assertNotIn("1구 이전 타자 공", x["raw_relay"])
        self.assertNotIn("1구 뒤 타석 공", x["raw_relay"])
        self.assertEqual(len(x["raw_relay"]), len(x["source_seqs"]))

    def test_no_context(self):
        x = get_relay_context_for_play(self.con, "G", "p12", before_n=0, after_n=0)
        self.assertEqual(x["source_seqs"], [9, 11, 12, 13, 14])

    def test_invalid_ids_and_excluded_target(self):
        self.assertIsNone(get_relay_context_for_play(self.con, "", "p12"))
        self.assertIsNone(get_relay_context_for_play(self.con, "OTHER", "p12"))
        self.assertIsNone(get_relay_context_for_play(self.con, "G", "missing"))
        self.assertIsNone(get_relay_context_for_play(self.con, "G", "p5"))

    def test_invalid_window_sizes(self):
        for x in (-1, 1.5, True):
            with self.assertRaises(ValueError):
                get_relay_context_for_play(self.con, "G", "p12", before_n=x)


if __name__ == "__main__":
    unittest.main()
