"""Question/target preflight checks; no Gemini, KLUE, or file DB required."""
import os
import sqlite3
import unittest
from unittest.mock import Mock, patch

from fastapi import HTTPException

from backend.api.explanations_generate import GenerateRequest, generate_explanation
from backend.explanation.question_scope import question_targets_another_batter


class QuestionScopeTests(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.con.execute(
            "CREATE TABLE plays (game_id TEXT, play_id TEXT, seq INTEGER, "
            "event_type TEXT, batter TEXT, pitcher TEXT, description TEXT)"
        )
        self.con.executemany(
            "INSERT INTO plays VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("G1", "P8", 8, "groundout", "박찬호", "임찬규",
                 "박찬호 : 3루수 땅볼 아웃"),
                ("G1", "P16", 16, "flyout", "안재석", "임찬규",
                 "안재석 : 중견수 플라이 아웃"),
                ("G1", "P61", 61, "steal", "양석환", "임찬규",
                 "1루주자 강승호 : 2루 도루"),
                ("G1", "P75", 75, "runner_advance", "문보경", "최준호",
                 "1루주자 문정빈 : 2루까지 진루"),
                ("G1", "P55", 55, "single", "강승호", "임찬규",
                 "강승호 : 중견수 앞 1루타"),
                ("G2", "UNRELATED", 1, "groundout", "외부선수", "임찬규",
                 "외부선수 : 땅볼 아웃"),
            ],
        )

    def tearDown(self):
        self.con.close()

    def check(self, play_id, question):
        return question_targets_another_batter(self.con, "G1", play_id, question)

    def test_reject_clear_previous_batter_outcome(self):
        self.assertTrue(self.check(
            "P16", "박찬호가 3루수 땅볼로 아웃된 과정을 설명해 주세요."
        ))
        self.assertTrue(self.check(
            "P16", "박찬호가 3루수 땅볼로 아웃된 상황을 설명해 주세요."
        ))

    def test_allow_correct_target_and_generic_question(self):
        self.assertFalse(self.check("P16", "안재석의 플라이 아웃을 설명해 주세요."))
        self.assertFalse(self.check("P16", "이 플레이는 왜 아웃인가요?"))

    def test_allow_earlier_play_as_context(self):
        self.assertFalse(self.check(
            "P16", "앞서 박찬호가 땅볼 아웃된 이후 안재석은 어떻게 됐나요?"
        ))
        self.assertFalse(self.check(
            "P16", "박찬호의 땅볼과 안재석의 플라이 아웃을 비교해 주세요."
        ))

    def test_allow_steal_and_runner_advance(self):
        self.assertFalse(self.check("P61", "강승호가 도루한 과정은 무엇인가요?"))
        self.assertFalse(self.check("P75", "문정빈이 왜 진루했나요?"))
        self.assertFalse(self.check("P55", "주자 문정빈이 왜 아웃됐나요?"))

    def test_same_game_only(self):
        self.assertFalse(self.check("P16", "외부선수의 땅볼 아웃을 설명해 주세요."))

    def test_incomplete_metadata_is_inconclusive(self):
        fake_con = Mock()
        fake_con.execute.return_value.fetchone.return_value = (1,)
        self.assertFalse(question_targets_another_batter(
            fake_con, "G1", "P16", "박찬호가 땅볼 아웃됐나요?"
        ))

    def test_http_422_before_model_initialization(self):
        # The route must not load model dependencies or return 502.
        req = GenerateRequest(
            game_id="G1", play_id="P16",
            question="박찬호가 3루수 땅볼로 아웃된 과정을 설명해 주세요.",
        )
        with patch.dict(os.environ, {"EXPLANATION_GENERATION_ENABLED": "1"}), \
             patch("backend.api.explanations_generate.store.connect", return_value=self.con), \
             patch("backend.api.explanations_generate.get_live_dependencies") as deps:
            with self.assertRaises(HTTPException) as ctx:
                generate_explanation(req)
            self.assertEqual(ctx.exception.status_code, 422)
            self.assertIn("일치하지", ctx.exception.detail)
            deps.assert_not_called()


if __name__ == "__main__":
    unittest.main()
