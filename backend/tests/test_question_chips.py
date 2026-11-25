"""A4 질문 칩: 매핑표, 칩 목록 API, chip_id로 해설 요청. Gemini·KLUE는 부르지 않는다."""
from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from ai.explain.prompts import load_cards
from backend.api import explanations_generate
from backend.api.main import app
from backend.explanation.live_runtime import LiveDependencies
from backend.explanation.question_chips import (
    CHIPS, ENTRY_CHIP, FALLBACK_TAG, TAG_CHIPS, follow_up_ids, pick_tag,
)
from backend.game.store import SCHEMA

ROOT = Path(__file__).resolve().parents[2]
REAL_DB = ROOT / "data" / "db" / "yagu.sqlite"


class ChipTableTests(unittest.TestCase):
    def test_22_chips_and_every_mapped_chip_exists(self):
        self.assertEqual(len(CHIPS), 22)
        for tag, ids in TAG_CHIPS.items():
            self.assertTrue(1 <= len(ids) <= 2, tag)
            for cid in ids:
                self.assertIn(cid, CHIPS, tag)
                self.assertNotEqual(cid, ENTRY_CHIP, "입구 칩은 후속 칩이 아니다")

    def test_chip_cards_exist_in_card_folder(self):
        cards = load_cards(ROOT / "cards")
        for chip in CHIPS.values():
            for cid in chip.card_ids:
                self.assertIn(cid, cards, chip.id)

    def test_unknown_tag_falls_back(self):
        self.assertEqual(pick_tag(["SOMETHING_NEW"]), FALLBACK_TAG)
        self.assertEqual(follow_up_ids([]), ("q.apply",))

    def test_priority_follows_table_order(self):
        # 태그가 여러 개면 매핑표에서 위에 있는 행을 쓴다(SINGLE 행이 ERROR 행보다 위).
        self.assertEqual(pick_tag(["ERROR", "SINGLE"]), "SINGLE")
        self.assertEqual(pick_tag(["walk"]), "WALK")

    @unittest.skipUnless(REAL_DB.exists(), "실제 경기 DB 없음")
    def test_every_tag_in_real_db_is_mapped(self):
        """완료 조건: BE가 정한 유형 태그 전부에 칩이 매핑됨."""
        con = sqlite3.connect(f"file:{REAL_DB}?mode=ro", uri=True)
        try:
            tags = set()
            for (raw,) in con.execute("SELECT type_tags FROM plays"):
                tags.update(json.loads(raw or "[]"))
        finally:
            con.close()
        self.assertTrue(tags)
        self.assertEqual(sorted(t for t in tags if t not in TAG_CHIPS), [])


class ChipApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.sqlite"
        con = sqlite3.connect(self.db)
        con.executescript(SCHEMA)
        con.execute("INSERT INTO games (game_id,game_date,away,home,play_count) VALUES ('G','2026-10-07','두산','LG',2)")
        for seq, pid, event, desc, tags in [
            (1, "p1", "batter_announcement", "6번타자 이재원", []),
            (2, "p2", "walk", "이재원 : 볼넷", ["WALK"]),
        ]:
            facts = [{"id": "F1", "text": "기록: 이재원 : 볼넷"}] if pid == "p2" else []
            con.execute("""INSERT INTO plays (game_id,seq,play_id,inning,half,event_type,description,batter,pitcher,
                 state_before,state_after,type_tags,facts) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("G", seq, pid, 5, "bottom", event, desc, "이재원", "최민석", None, None,
                 json.dumps(tags), json.dumps(facts, ensure_ascii=False)))
        con.commit(); con.close()
        self.prompts: list[str] = []
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def env(self):
        return patch.dict("os.environ", {"YAGU_DB": str(self.db), "EXPLANATION_GENERATION_ENABLED": "1"})

    def generate(self, system, prompt, schema, tag):
        self.prompts.append(prompt)
        return ({"sentences": [{"text": "이재원은 볼넷으로 1루에 나갔습니다.", "evidence": ["F1"]}]},
                {"model": "fake", "cache_hit": False})

    def post(self, **payload):
        body = {"game_id": "G", "play_id": "p2", **payload}
        deps = LiveDependencies(self.generate, lambda pairs: [0.99] * len(pairs), 0.05)
        with self.env(), patch.object(explanations_generate, "get_live_dependencies", return_value=deps):
            return self.client.post("/explanations/generate", json=body)

    def test_chips_endpoint_returns_entry_and_follow_ups(self):
        with self.env():
            res = self.client.get("/explanations/chips", params={"game_id": "G", "play_id": "p2"})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["tag"], "WALK")
        self.assertEqual(body["entry"], {"id": "q.why", "label": "한입만🍙"})
        self.assertEqual([c["id"] for c in body["follow_ups"]], ["q.rule_walk", "q.apply"])

    def test_chips_endpoint_404_for_unknown_play(self):
        with self.env():
            res = self.client.get("/explanations/chips", params={"game_id": "G", "play_id": "nope"})
        self.assertEqual(res.status_code, 404)

    def test_generate_with_chip_adds_chip_cards_and_fixed_question(self):
        res = self.post(chip_id="q.rule_walk")
        self.assertEqual(res.status_code, 200, res.text)
        body = res.json()
        self.assertEqual(body["chip_id"], "q.rule_walk")
        self.assertEqual(body["question"], "볼넷은 어떤 규칙이야?")
        self.assertEqual(body["card_ids"][:2], ["rule.base_on_balls", "term.ball"])
        self.assertIn("rule.base_on_balls:", self.prompts[0])
        self.assertIn("term.ball:", self.prompts[0])

    def test_chip_not_allowed_for_this_play_is_rejected_before_gemini(self):
        res = self.post(chip_id="q.rule_balk")
        self.assertEqual(res.status_code, 422)
        self.assertEqual(self.prompts, [])

    def test_unknown_chip_and_both_fields_are_rejected(self):
        self.assertEqual(self.post(chip_id="q.nope").status_code, 422)
        self.assertEqual(self.post(chip_id="q.why", question="왜?").status_code, 422)
        self.assertEqual(self.post().status_code, 422)
        self.assertEqual(self.prompts, [])


if __name__ == "__main__":
    unittest.main()
