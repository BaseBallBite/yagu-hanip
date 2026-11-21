"""HTTP boundary tests. Stub generation and support scores; no Gemini or KLUE calls."""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api import explanations_generate
from backend.api.main import app
from backend.explanation.live_runtime import LiveDependencies, score_with_klue_subprocess
from backend.game.store import SCHEMA


class GenerateExplanationApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.sqlite"
        con = sqlite3.connect(self.db)
        con.executescript(SCHEMA)
        con.execute("INSERT INTO games (game_id,game_date,away,home,play_count) VALUES ('G','2026-10-07','두산','LG',2)")
        for seq, pid, event, desc in [(1, "p1", "batter_announcement", "6번타자 이재원"),
                                       (2, "p2", "single", "이재원 : 3루수 앞 내야안타")]:
            facts = [{"id": "F1", "text": "기록: 이재원 : 3루수 앞 내야안타"}] if pid == "p2" else []
            con.execute("""INSERT INTO plays (game_id,seq,play_id,inning,half,event_type,description,batter,pitcher,
                 state_before,state_after,type_tags,facts) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("G", seq, pid, 5, "bottom", event, desc, "이재원", "최민석", None, None,
                 json.dumps(["SINGLE"] if pid == "p2" else []), json.dumps(facts, ensure_ascii=False)))
        con.commit(); con.close()
        self.calls = []
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def generate(self, system, prompt, schema, tag):
        self.calls.append("gemini")
        return ({"sentences": [{"text": "이재원은 3루수 앞 내야안타를 기록했습니다.", "evidence": ["F1"]},
                               {"text": "왜 그런 판단을 했는지는 기록만으로 알 수 없습니다.", "evidence": ["UNKNOWN"]}]},
                {"model": "fake", "cache_hit": False})

    def support(self, pairs):
        self.calls.append("klue")
        self.assertEqual(len(pairs), 1)
        return [0.99]

    def request(self, **kwargs):
        payload = {"game_id": "G", "play_id": "p2", "question": "왜 내야안타인가요?"}
        payload.update(kwargs)
        deps = LiveDependencies(self.generate, self.support, 0.05)
        with patch.dict("os.environ", {"YAGU_DB": str(self.db), "EXPLANATION_GENERATION_ENABLED": "1"}), \
             patch.object(explanations_generate, "get_live_dependencies", return_value=deps):
            return self.client.post("/explanations/generate", json=payload)

    def test_disabled_by_default(self):
        with patch.dict("os.environ", {"EXPLANATION_GENERATION_ENABLED": "0"}):
            response = self.client.post("/explanations/generate", json={
                "game_id": "G", "play_id": "p2", "question": "질문"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.calls, [])

    def test_cors_preflight_post(self):
        response = self.client.options("/explanations/generate", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("POST", response.headers.get("access-control-allow-methods", ""))

    def test_klue_worker_utf8_subprocess_with_stub_model(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "apply_model.py").write_text(
                "def load_model(model_dir, batch=8):\n"
                "    def score(pairs):\n"
                "        assert pairs == [('이재원', '내야안타')]\n"
                "        return [0.875]\n"
                "    return score\n", encoding="utf-8")
            scores = score_with_klue_subprocess(
                [("이재원", "내야안타")], python=Path(sys.executable),
                model_dir=folder, apply_dir=folder,
            )
        self.assertEqual(scores, [0.875])

    def test_http_success_and_evidence(self):
        response = self.request()
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["display_condition"], "B3")
        self.assertEqual(data["source"], "gemini+rule_v2+klue")
        self.assertEqual(data["sentences"][0]["cited_ids"], ["F1"])
        self.assertEqual(data["sentences"][1]["cited_ids"], ["UNKNOWN"])
        self.assertEqual(self.calls, ["gemini", "klue"])

    def test_not_found_never_generates(self):
        response = self.request(play_id="nonexistent")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.calls, [])

    def test_invalid_request_does_not_generate(self):
        response = self.request(question="  ")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.calls, [])

    def test_unavailable_db_is_503(self):
        with patch.dict("os.environ", {"YAGU_DB": str(self.db.parent / "missing.sqlite"), "EXPLANATION_GENERATION_ENABLED": "1"}):
            response = self.client.post("/explanations/generate", json={
                "game_id": "G", "play_id": "p2", "question": "질문"})
        self.assertEqual(response.status_code, 503)

    def test_failed_verification_is_502_not_unchecked_output(self):
        def broken(_):
            return []
        deps = LiveDependencies(self.generate, broken, 0.05)
        with patch.dict("os.environ", {"YAGU_DB": str(self.db), "EXPLANATION_GENERATION_ENABLED": "1"}), \
             patch.object(explanations_generate, "get_live_dependencies", return_value=deps):
            response = self.client.post("/explanations/generate", json={
                "game_id": "G", "play_id": "p2", "question": "질문"})
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("sentences", response.json())


if __name__ == "__main__":
    unittest.main()
