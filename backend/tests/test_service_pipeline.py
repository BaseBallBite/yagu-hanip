"""B2->B3 연결 단위 테스트: 생성기/모델은 주입한 가짜 함수 사용."""
import json
import sqlite3
import tempfile
import unittest
import warnings
from pathlib import Path

from backend.explanation.service_pipeline import build_verified_explanation, load_threshold
from backend.game.store import SCHEMA


class ServicePipelineTests(unittest.TestCase):
    def setUp(self):
        self._warning_ctx = warnings.catch_warnings()
        self._warning_ctx.__enter__()
        warnings.simplefilter("ignore", ResourceWarning)
        self.con = sqlite3.connect(":memory:")
        self.con.row_factory = sqlite3.Row
        self.con.executescript(SCHEMA)
        self.con.execute("INSERT INTO games (game_id,game_date,away,home,play_count) VALUES ('G','2026-10-07','두산','LG',3)")
        rows = [
            (1, "p1", "inning_start", "5회말 LG 공격", None, None, [], []),
            (2, "p2", "batter_announcement", "6번타자 이재원", "이재원", "최민석", [], []),
            (3, "p3", "single", "이재원 : 3루수 앞 내야안타", "이재원", "최민석",
             ["SINGLE", "ADVANCE", "ERROR"], [{"id": "F1", "text": "이재원 : 3루수 앞 내야안타"}]),
        ]
        for seq, pid, event, desc, batter, pitcher, tags, facts in rows:
            self.con.execute("""INSERT INTO plays (game_id,seq,play_id,inning,half,event_type,description,batter,pitcher,
              state_before,state_after,type_tags,facts) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
             ("G", seq, pid, 5, "bottom", event, desc, batter, pitcher, None, None,
              json.dumps(tags, ensure_ascii=False), json.dumps(facts, ensure_ascii=False)))
        self.model_calls = []

    def tearDown(self):
        self.con.close()
        self._warning_ctx.__exit__(None, None, None)

    def fake_generate(self, system, prompt, schema, tag):
        self.assertEqual(tag["condition"], "B2")
        self.assertIn("term.infield_hit", prompt)
        self.assertIn("F1: 이재원", prompt)
        self.assertIn("[현재 해설 대상 및 R 근거 범위]", prompt)
        self.assertIn("R3: TARGET (seq=3)", prompt)
        self.assertIn("문장에 등장하는 모든 선수 이름", prompt)
        self.assertIn("R 또는 F 근거 ID", prompt)
        self.assertIn("득점 원인과 점수", prompt)
        self.assertIn("앞뒤 플레이를 현재 플레이인 것처럼", prompt)
        self.assertIn("사전식 정의를 문장 중간에 그대로 끼워 넣지", prompt)
        self.assertIn("같은 플레이 결과나 아웃 원리를 여러 문장에서 반복하지", prompt)
        self.assertIn("3아웃으로 공격이 끝난 경우", prompt)
        self.assertIn("추측해 이유를 만들어내지", prompt)
        return {"sentences": [
            {"text": "이재원은 3루수 앞 내야안타를 기록했습니다.", "evidence": ["F1"]},
            {"text": "왜 실수했는지는 기록에 나와 있지 않아 알 수 없습니다.", "evidence": ["UNKNOWN"]},
            {"text": "이재원은 8점을 기록했습니다.", "evidence": ["F1"]},
            {"text": "이재원은 3루수 앞 내야안타를 기록했습니다.", "evidence": ["UNKNOWN", "F1"]},
        ]}, {"model": "fake-gemini", "cache_hit": False}

    def fake_support(self, pairs):
        self.model_calls.append(pairs)
        return [0.9] * len(pairs)

    def test_generation_verification_citations(self):
        before = self.con.total_changes
        result = build_verified_explanation(self.con, "G", "p3", "왜 내야안타?",
             generate=self.fake_generate, p_support=self.fake_support, threshold=0.05)
        self.assertEqual(self.con.total_changes, before)
        self.assertEqual(result["display_condition"], "B3")
        self.assertEqual(result["source"], "gemini+rule_v2+klue")
        self.assertEqual(result["generation"]["model"], "fake-gemini")
        self.assertEqual(len(result["sentences"]), 3)
        self.assertEqual(result["dropped_count"], 1)
        self.assertEqual(result["sentences"][0]["cited_ids"], ["F1"])
        self.assertEqual(result["sentences"][0]["cited_text"],
                         [{"id": "F1", "text": "이재원 : 3루수 앞 내야안타"}])
        self.assertEqual(result["sentences"][1]["cited_ids"], ["UNKNOWN"])
        self.assertIsNone(result["sentences"][1]["p_support"])
        self.assertEqual(result["sentences"][2]["cited_ids"], ["F1"])
        self.assertEqual([x["check"] for x in result["sentences"]],
                         ["rule_v2+model", "unknown_rule", "rule_v2+model"])
        self.assertEqual(len(self.model_calls), 1)
        self.assertEqual(len(self.model_calls[0]), 2)
        self.assertEqual(self.model_calls[0][0][1], "이재원 : 3루수 앞 내야안타")

    def test_previous_plate_appearance_is_not_mistaken_for_target(self):
        """Wrong previous batter result must not be returned as current play."""
        for seq, pid, event, desc, name in [
            (4, "p4", "batter_announcement", "7번타자 안재석", "안재석"),
            (5, "p5", "flyout", "안재석 : 중견수 플라이 아웃", "안재석"),
        ]:
            self.con.execute(
                """INSERT INTO plays (game_id,seq,play_id,inning,half,event_type,
                description,batter,pitcher,state_before,state_after,type_tags,facts)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("G", seq, pid, 5, "bottom", event, desc, name, "최민석",
                 None, None, "[]", "[]"),
            )

        def generate(system, prompt, schema, tag):
            self.assertIn("R3: PRIOR_PA (seq=3)", prompt)
            self.assertIn("R5: TARGET (seq=5)", prompt)
            self.assertIn("안재석 : 중견수 플라이 아웃", prompt)
            return {"sentences": [
                {"text": "이재원은 3루수 앞 내야안타를 기록했습니다.",
                 "evidence": ["R2", "R3"]},
                {"text": "안재석은 중견수 플라이 아웃됐습니다.",
                 "evidence": ["R5"]},
                {"text": "앞서 이재원은 3루수 앞 내야안타를 기록했습니다.",
                 "evidence": ["R2", "R3"]},
            ]}, {"model": "fake", "cache_hit": False}

        result = build_verified_explanation(
            self.con, "G", "p5", "안재석은 왜 플라이 아웃됐나요?",
            generate=generate, p_support=self.fake_support, threshold=0.05,
        )
        self.assertEqual(result["verifier"]["checked_sentences"], 3)
        self.assertEqual(result["verifier"]["target_scope_dropped"], 1)
        self.assertEqual(result["dropped_count"], 1)
        self.assertEqual(
            [s["text"] for s in result["sentences"]],
            ["안재석은 중견수 플라이 아웃됐습니다.",
             "앞서 이재원은 3루수 앞 내야안타를 기록했습니다."],
        )

    def test_low_model_support_rejected(self):
        result = build_verified_explanation(self.con, "G", "p3", "질문",
              generate=self.fake_generate, p_support=lambda pairs: [0.01] * len(pairs), threshold=0.05)
        self.assertEqual([x["cited_ids"] for x in result["sentences"]], [["UNKNOWN"]])
        self.assertEqual(result["dropped_count"], 3)

    def test_malformed_model_results_fail_closed(self):
        for fn in (lambda pairs: [], lambda pairs: [float("nan")] * len(pairs),
                   lambda pairs: [2.0] * len(pairs)):
            with self.assertRaises(ValueError):
                build_verified_explanation(self.con, "G", "p3", "질문",
                    generate=self.fake_generate, p_support=fn, threshold=0.05)

    def test_nonexistent_play_does_not_generate(self):
        def no_generate(*args):
            self.fail("unexpected generate")
        self.assertIsNone(build_verified_explanation(self.con, "G", "missing", "질문",
                    generate=no_generate, p_support=self.fake_support, threshold=0.05))

    def test_threshold_from_model_folder(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "threshold.json"
            p.write_text('{"threshold":0.05,"picked_on":"val"}', encoding="utf-8")
            self.assertEqual(load_threshold(temp), 0.05)
            for bad in ('{"threshold":1.3}', '{"threshold":"0.05"}',
                        '{"threshold":true}', '{"threshold":-1}'):
                p.write_text(bad, encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_threshold(temp)
            p.unlink()
            with self.assertRaises(FileNotFoundError):
                load_threshold(temp)


if __name__ == "__main__":
    unittest.main()
