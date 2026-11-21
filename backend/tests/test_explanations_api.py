"""Approved 2026-10-07 demo ONLY.  No Gemini, model, evaluation fixtures, or DB writes.

Run from repository root: py -m unittest backend.tests.test_explanations_api -v
"""

import hashlib
import json
import unittest

from fastapi.testclient import TestClient

from backend.api.explanations import DEMO_GAME_ID, DEMO_JSON
from backend.api.main import app

client = TestClient(app)


class ExplanationDemoApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw_bytes = DEMO_JSON.read_bytes()
        cls.fixture = json.loads(cls.raw_bytes)
        cls.play_id = cls.fixture["play_id"]
        assert cls.fixture["game_id"] == DEMO_GAME_ID
        assert cls.fixture["scene"]["video_id"] == "YQD3hMI2LPo"

    def params(self, **kwargs):
        return {"game_id": DEMO_GAME_ID, "play_id": self.play_id, **kwargs}

    def test_questions_from_approved_fixture_only(self):
        response = client.get("/explanations/demo/questions", params=self.params())
        self.assertEqual(response.status_code, 200)
        self.assertEqual([q["qid"] for q in response.json()["questions"]], ["H01", "H02", "H03"])
        self.assertEqual(response.json()["video_id"], "YQD3hMI2LPo")

    def test_h01_to_h03_exact_b3_no_comparison_leak(self):
        for expected in self.fixture["questions"]:
            got = client.get("/explanations/demo", params=self.params(qid=expected["qid"]))
            self.assertEqual(got.status_code, 200)
            body = got.json()
            self.assertEqual(body["source"], "precomputed")
            self.assertEqual(body["display_condition"], "B3")
            self.assertEqual(body["sentences"], expected["answers"]["B3"]["sentences"])
            self.assertNotIn("answers", body)  # never expose R and B0 comparison outputs

    def test_exact_question_lookup(self):
        q = self.fixture["questions"][1]
        got = client.get("/explanations/demo", params=self.params(question=q["question"]))
        self.assertEqual(got.status_code, 200)
        self.assertEqual(got.json()["qid"], "H02")

    def test_unknown_preserved_in_h03(self):
        got = client.get("/explanations/demo", params=self.params(qid="H03"))
        self.assertEqual(got.status_code, 200)
        self.assertTrue(any("UNKNOWN" in s["cited_ids"] for s in got.json()["sentences"]))
        self.assertTrue(any(x["id"] == "UNKNOWN" for s in got.json()["sentences"] for x in s["cited_text"]))

    def test_non_demo_game_and_other_play_not_available(self):
        # Synthetic IDs only: do not open or load evaluation fixtures.
        self.assertEqual(client.get("/explanations/demo", params={
            "game_id": "NOT_A_DEMO_GAME", "play_id": self.play_id, "qid": "H01"
        }).status_code, 404)
        self.assertEqual(client.get("/explanations/demo", params=self.params(
            play_id="not-a-demo-play", qid="H01"
        )).status_code, 404)

    def test_unlisted_question_no_live_fallback(self):
        self.assertEqual(client.get("/explanations/demo", params=self.params(qid="H99")).status_code, 404)
        self.assertEqual(client.get("/explanations/demo", params=self.params(
            question="등록되지 않은 질문"
        )).status_code, 404)

    def test_invalid_selector_rejected(self):
        self.assertEqual(client.get("/explanations/demo", params=self.params()).status_code, 422)
        self.assertEqual(client.get("/explanations/demo", params=self.params(
            qid="H01", question="이중 선택"
        )).status_code, 422)
        self.assertEqual(client.get("/explanations/demo", params=self.params(qid=" ")).status_code, 422)
        self.assertEqual(client.get("/explanations/demo/questions").status_code, 422)

    def test_fixture_untouched(self):
        before = hashlib.sha256(self.raw_bytes).hexdigest()
        client.get("/explanations/demo/questions", params=self.params())
        client.get("/explanations/demo", params=self.params(qid="H01"))
        self.assertEqual(hashlib.sha256(DEMO_JSON.read_bytes()).hexdigest(), before)


if __name__ == "__main__":
    unittest.main()
