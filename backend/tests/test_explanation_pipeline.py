"""Synthetic-only integration tests. NO real games, DB, Gemini, model, or eval data."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.explanation.pipeline import EvidenceContractError, run_rule_b3


GAME = "SYNTHETIC_GAME"
PLAY = "SYNTHETIC_PLAY"


def fake_context(_req):
    return ({
        "game_id": GAME, "play_id": PLAY,
        "qid": "synthetic", "question": "왜 아웃인가요?",
        "raw_relay": ["가상 타자: 뜬공 아웃"],
        "facts": [{"id": "F1", "text": "가상 타자는 아웃됐습니다."}],
        "card_ids": ["rule.synthetic"],
        "players": ["가상 타자"],
    }, {"rule.synthetic": {"title": "가상 규칙", "text": "뜬공을 잡으면 아웃", "rule_ref": ""}})


class FakeRunner:
    def generate(self, system, prompt, schema, tag):
        assert "가상" in prompt
        assert tag["condition"] == "B2"
        return {"sentences": [
            {"text": "가상 타자는 아웃됐습니다.", "evidence": ["F1"]},
            {"text": "이유는 기록에 없어 알 수 없습니다.", "evidence": ["UNKNOWN"]},
            {"text": "기록에 없는 999점을 획득했습니다.", "evidence": ["F1"]},
            {"text": "근거 표시 없음", "evidence": []},
        ]}, {"cache_hit": False, "model": "mock-no-network"}


class SafePipelineTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_default_disabled_without_accessing_providers(self):
        with patch.dict(os.environ, {"EXPLANATION_GENERATION_ENABLED": "0"}), \
             patch("backend.api.explanations_generate.store.connect") as db, \
             patch("backend.api.explanations_generate.get_live_dependencies") as deps:
            res = self.client.post("/explanations/generate", json={
                "game_id": GAME, "play_id": PLAY, "question": "왜?"})
            self.assertEqual(res.status_code, 503)
            db.assert_not_called()
            deps.assert_not_called()

    def test_default_unconfigured_context_is_503_even_if_opted_in(self):
        with patch.dict(os.environ, {"EXPLANATION_GENERATION_ENABLED": "1", "YAGU_DB": "does-not-exist.sqlite"}), \
             patch("backend.api.explanations_generate.get_live_dependencies") as deps:
            res = self.client.post("/explanations/generate", json={
                "game_id": GAME, "play_id": PLAY, "question": "왜?"})
            self.assertEqual(res.status_code, 503)
            deps.assert_not_called()

    def test_synthetic_mock_pipeline_and_unknown_kept(self):
        item, cards = fake_context(None)
        out = run_rule_b3(item, cards, FakeRunner().generate)
        self.assertEqual(len(out["sentences"]), 2)
        self.assertEqual(out["dropped_count"], 2)
        self.assertEqual(out["sentences"][0]["cited_text"][0]["id"], "F1")
        self.assertEqual(out["sentences"][1]["cited_ids"], ["UNKNOWN"])
        self.assertFalse(out["model_verification_applied"])

    def test_api_with_mock_dependencies(self):
        from unittest.mock import MagicMock
        fake_con = MagicMock()
        fake_con.execute.return_value.fetchone.return_value = (1,)
        expected = {"display_condition": "B3", "source": "gemini+rule_v2+klue", "sentences": []}
        with patch.dict(os.environ, {"EXPLANATION_GENERATION_ENABLED": "1"}), \
             patch("backend.api.explanations_generate.store.connect", return_value=fake_con), \
             patch("backend.api.explanations_generate.get_live_dependencies") as deps, \
             patch("backend.api.explanations_generate.build_verified_explanation", return_value=expected) as build:
            deps.return_value.generate = FakeRunner().generate
            deps.return_value.p_support = lambda pairs: [0.99] * len(pairs)
            deps.return_value.threshold = 0.05
            res = self.client.post("/explanations/generate", json={
                "game_id": GAME, "play_id": PLAY, "question": "왜 아웃인가요?"})
            self.assertEqual(res.status_code, 200, res.text)
            self.assertEqual(res.json(), expected)
            build.assert_called_once()
            fake_con.close.assert_called_once()

    def test_missing_play_rejected_before_runtime(self):
        from unittest.mock import MagicMock
        fake_con = MagicMock()
        fake_con.execute.return_value.fetchone.return_value = None
        with patch.dict(os.environ, {"EXPLANATION_GENERATION_ENABLED": "1"}), \
             patch("backend.api.explanations_generate.store.connect", return_value=fake_con), \
             patch("backend.api.explanations_generate.get_live_dependencies") as deps:
            res = self.client.post("/explanations/generate", json={
                "game_id": GAME, "play_id": "MISSING", "question": "왜?"})
            self.assertEqual(res.status_code, 404)
            deps.assert_not_called()
            fake_con.close.assert_called_once()

    def test_missing_R_prevents_any_call(self):
        item,cards=fake_context(None)
        item["raw_relay"] = []
        with patch.object(FakeRunner(), "generate") as gen:
            with self.assertRaises(EvidenceContractError):
                run_rule_b3(item,cards,gen)
            gen.assert_not_called()

    def test_card_limit(self):
        item,cards=fake_context(None)
        item["card_ids"] = ["a","b","c","d"]
        with self.assertRaises(EvidenceContractError):
            run_rule_b3(item,cards,FakeRunner().generate)

    def test_duplicate_F_ids(self):
        item,cards=fake_context(None)
        item["facts"].append({"id": "F1", "text": "추가 사실"})
        with self.assertRaises(EvidenceContractError):
            run_rule_b3(item,cards,FakeRunner().generate)

    def test_invalid_generated_shape(self):
        item,cards=fake_context(None)
        def bad(*args):return {"sentences": "invalid"}, {}
        with self.assertRaises(EvidenceContractError):
            run_rule_b3(item,cards,bad)

    def test_request_validation(self):
        res=self.client.post("/explanations/generate",json={
            "game_id": GAME, "play_id": PLAY, "question": ""})
        self.assertEqual(res.status_code, 422)


if __name__ == "__main__":
    unittest.main()
