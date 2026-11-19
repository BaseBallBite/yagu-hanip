"""AI-A 규칙 기준 K 카드 자동 선정. 가상 B4 DB만 사용."""

import json
import sqlite3
import unittest
from pathlib import Path

from backend.explanation.cards_lookup import DICT_PATH, get_cards_for_play, pick_cards, play_type


class CardsLookupTests(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.con.execute("CREATE TABLE plays (game_id TEXT, seq INTEGER, play_id TEXT, event_type TEXT, type_tags TEXT, facts TEXT)")

    def tearDown(self):
        self.con.close()

    def insert(self, game, play_id, event, tags, facts):
        self.con.execute(
            "INSERT INTO plays VALUES (?, ?, ?, ?, ?, ?)",
            (game, 327, play_id, event, json.dumps(tags), json.dumps([{"id": f"F{i}", "text": s} for i, s in enumerate(facts, 1)], ensure_ascii=False)),
        )

    def test_demo_event_and_facts(self):
        self.insert("20261007OBLG02026", "test-play", "single", ["SINGLE", "ADVANCE", "ERROR"], [
            "5회말, 2사, 1,2루 (1루 문보경, 2루 오스틴), 점수 두산 5-5 LG",
            "타자 이재원, 투수 최민석",
            "기록: 이재원 : 3루수 앞 내야안타",
            "주자 기록: 1루주자 문보경 : 2루까지 진루",
            "주자 기록: 2루주자 문보경 : 실책으로 홈인",
            "주자 기록: 2루주자 오스틴 : 3루까지 진루",
            "주자 기록: 3루주자 오스틴 : 실책으로 홈인 (3루수 송구 실책->1루수)",
            "이 타석 투구 수 1개, 마지막 공: 1구 투심 146km/h 결과 타격",
            "플레이 후 2사, 1루 (1루 이재원), 점수 두산 5-7 LG",
            "이 플레이로 득점: LG 2점",
        ])
        result = get_cards_for_play(self.con, "20261007OBLG02026", "test-play")
        self.assertEqual(result["seq"], 327)
        self.assertEqual(result["card_source"], "auto")
        self.assertLessEqual(len(result["card_ids"]), 3)
        self.assertTrue(all(cid in json.loads(DICT_PATH.read_text(encoding="utf-8"))["cards"] for cid in result["card_ids"]))
        self.assertIn("term.error", result["card_ids"])
        self.assertIn("term.infield_hit", result["card_ids"])

    def test_three_run_home_run_does_not_get_grand_slam_card(self):
        self.insert("G1", "HR3", "home_run", ["HOME_RUN", "SCORE"], [
            "2회말, 무사, 1,2루 (1루 문보경, 2루 문정빈), 점수 두산 0-0 LG",
            "타자 이재원, 투수 최민석",
            "기록: 이재원 : 중견수 뒤 홈런",
            "이 플레이로 득점: LG 3점",
        ])
        ids = get_cards_for_play(self.con, "G1", "HR3")["card_ids"]
        self.assertIn("term.home_run", ids)
        self.assertNotIn("term.grand_slam", ids)

    def test_four_run_home_run_keeps_grand_slam_card(self):
        self.insert("G1", "HR4", "home_run", ["HOME_RUN", "SCORE"], [
            "2회말, 무사, 만루 (1루 A, 2루 B, 3루 C), 점수 두산 0-0 LG",
            "타자 D, 투수 E",
            "기록: D : 홈런",
            "이 플레이로 득점: LG 4점",
        ])
        ids = get_cards_for_play(self.con, "G1", "HR4")["card_ids"]
        self.assertIn("term.home_run", ids)
        self.assertIn("term.grand_slam", ids)

    def test_home_run_without_score_keeps_existing_selection(self):
        self.insert("G1", "HR_UNK", "home_run", ["HOME_RUN"], [
            "기록: D : 홈런",
        ])
        ids = get_cards_for_play(self.con, "G1", "HR_UNK")["card_ids"]
        self.assertIn("term.home_run", ids)
        self.assertIn("term.grand_slam", ids)

    def test_direct_card_event_first_then_specific_mapping(self):
        d = {"cards": {
            "rule.balk": {"event_types": ["BALK"], "category": "규칙"},
            "term.specific": {"event_types": ["BALK"], "category": "기록"},
            "term.general": {"event_types": ["BALK", "ERROR", "SINGLE"], "category": "기록"},
            "term.error": {"event_types": [], "category": "수비"},
        }, "event_index": {"BALK": ["term.general", "term.specific"]}, "alias_index": {"실책": "term.error"}}
        p = {"event_type": "BALK", "tags": [], "facts": ["실책"]}
        self.assertEqual(pick_cards(p, d), ["rule.balk", "term.specific", "term.error"])

    def test_alias_exclusions_and_no_match(self):
        d = {"cards": {
            "term.batter": {"event_types": [], "category": "타격"},
            "term.error": {"event_types": [], "category": "수비"},
            "rule.operation": {"event_types": [], "category": "경기 운영"},
        }, "event_index": {}, "alias_index": {"타자": "term.batter", "운영": "rule.operation", "실책": "term.error"}}
        p = {"event_type": "GAME_STOPPAGE", "tags": [], "facts": ["타자 운영 실책"]}
        self.assertEqual(pick_cards(p, d), ["term.error"])
        p["facts"] = ["아무 일도 없음"]
        self.assertEqual(pick_cards(p, d), [])

    def test_missing_id_and_game_isolation(self):
        self.insert("G1", "P1", "single", [], ["안타"])
        self.assertIsNone(get_cards_for_play(self.con, "", "P1"))
        self.assertIsNone(get_cards_for_play(self.con, "G2", "P1"))
        self.assertIsNone(get_cards_for_play(self.con, "G1", "unknown"))
        self.assertEqual(get_cards_for_play(self.con, "G1", "P1")["play_id"], "P1")

    def test_sub_priority_matches_ai_a(self):
        self.assertEqual(play_type({"event_type": "SINGLE", "tags": ["ERROR", "ADVANCE"]}), ("skill", "SINGLE"))
        self.assertEqual(play_type({"event_type": "SINGLE", "tags": ["BALK"]}), ("rule", "BALK"))


if __name__ == "__main__":
    unittest.main()
