"""R/F/K 입력 조립: AI-A 프롬프트 및 근거 ID 호환성 검증."""

import json
import sqlite3
import unittest
import warnings
from pathlib import Path

from ai.explain.prompts import build_user_prompt, evidence_pool, load_cards
from backend.explanation.explanation_input import build_explanation_input
from backend.game.store import SCHEMA

ROOT = Path(__file__).resolve().parents[2]


class ExplanationInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # AI-A load_cards() opens YAML files without context managers;
        # silence only that existing ResourceWarning during fixture loading.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            cls.cards = load_cards(ROOT / "cards")

    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.con.row_factory = sqlite3.Row
        self.con.executescript(SCHEMA)
        self.con.execute(
            "INSERT INTO games (game_id, game_date, away, home, play_count) VALUES (?,?,?,?,?)",
            ("G", "2026-10-07", "두산", "LG", 4),
        )
        rows = [
            (1, "p1", "inning_start", "5회말 LG 공격", None, None, [], []),
            (2, "p2", "batter_announcement", "6번타자 이재원", "이재원", "최민석", [], []),
            (3, "p3", "pitcher_disengagement", "투수 투수판 이탈", None, None, [], []),
            (4, "p4", "single", "이재원 : 3루수 앞 내야안타", "이재원", "최민석", ["SINGLE", "ADVANCE", "ERROR"],
             [{"id": "F1", "text": "이재원 : 3루수 앞 내야안타"}, {"id": "F2", "text": "3루수 송구 실책"}]),
        ]
        for seq, pid, ev, desc, batter, pitcher, tags, facts in rows:
            self.con.execute(
                """INSERT INTO plays (game_id,seq,play_id,inning,half,event_type,description,batter,pitcher,
                  state_before,state_after,type_tags,facts) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("G", seq, pid, 5, "bottom", ev, desc, batter, pitcher, None, None,
                 json.dumps(tags, ensure_ascii=False), json.dumps(facts, ensure_ascii=False)),
            )

    def tearDown(self):
        self.con.close()

    def test_ai_a_input_and_evidence_pool(self):
        item = build_explanation_input(self.con, "G", "p4", "왜 실책으로 점수가 났어?")
        self.assertEqual(item["raw_relay"], ["5회말 LG 공격", "6번타자 이재원", "이재원 : 3루수 앞 내야안타"])
        self.assertEqual(item["raw_relay_source_seqs"], [1,2,4])
        self.assertEqual([f["id"] for f in item["facts"]], ["F1", "F2"])
        self.assertEqual(item["card_ids"], ["term.error", "term.hit", "term.infield_hit"])
        self.assertEqual(item["players"], ["이재원", "최민석"])
        self.assertEqual(item["card_source"], "auto")
        pool = evidence_pool(item, self.cards, "B2")
        self.assertEqual(set(pool), {"R1", "R2", "R3", "F1", "F2", *item["card_ids"]})
        prompt = build_user_prompt(item, self.cards, "B2")
        self.assertIn("왜 실책으로 점수가 났어?", prompt)
        self.assertIn("R3: 이재원", prompt)
        self.assertIn("F2: 3루수 송구 실책", prompt)
        self.assertIn("term.infield_hit", prompt)

    def test_question_changes_qid_not_sources(self):
        a = build_explanation_input(self.con, "G", "p4", "왜 실책?")
        b = build_explanation_input(self.con, "G", "p4", "왜 안타?")
        self.assertNotEqual(a["qid"], b["qid"])
        self.assertEqual(a["card_ids"], b["card_ids"])
        self.assertEqual(a["raw_relay"], b["raw_relay"])

    def test_missing_and_excluded(self):
        self.assertIsNone(build_explanation_input(self.con, "G", "missing", "질문"))
        self.assertIsNone(build_explanation_input(self.con, "OTHER", "p4", "질문"))
        self.assertIsNone(build_explanation_input(self.con, "G", "p3", "질문"))
        with self.assertRaises(ValueError):
            build_explanation_input(self.con, "G", "p4", "   ")

    def test_does_not_write_to_db(self):
        before = self.con.total_changes
        build_explanation_input(self.con, "G", "p4", "질문")
        self.assertEqual(self.con.total_changes, before)


if __name__ == "__main__":
    unittest.main()
