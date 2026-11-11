"""B3 플레이 사실(F) 테스트. 실제 data/raw 의 B1 v2 · B2 · B3 데이터를 읽는다.
data/raw 는 git에 없으므로 데이터가 없으면 건너뛴다.

실행 (저장소 루트에서):
    .venv/bin/python -m unittest backend.tests.test_facts -v
"""

import unittest
from pathlib import Path

from backend.game.facts import B2_DIR, ROOT, build_facts, build_game_facts, load_game

GAME = "20260328HTSK02026"  # 3/28 KIA–SSG (KIA 6-7 SSG)
HAS_DATA = (B2_DIR / f"{GAME}.json").exists()
ALLOWED_TAGS = {
    line.strip()
    for line in (ROOT / "tools/event_types.txt").read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.startswith("#")
}


def texts(result):
    return [f["text"] for f in result["facts"]]


@unittest.skipUnless(HAS_DATA, "data/raw 에 B1 v2 · B3 v2 데이터가 없음")
class FactsTest(unittest.TestCase):
    def test_every_play_has_well_formed_facts(self):
        for r in build_game_facts(GAME):
            ids = [f["id"] for f in r["facts"]]
            self.assertEqual(ids, [f"F{i}" for i in range(1, len(ids) + 1)], r["seq"])
            for t in texts(r):
                self.assertTrue(t.strip())
                self.assertNotIn("None", t)
            self.assertLessEqual(set(r["type_tags"]), ALLOWED_TAGS, r["seq"])

    def test_single_with_runs(self):
        # 1회초 1사 2,3루, 나성범 우전 1루타 → 3루 주자 김호령 홈인
        seq = next(i for i, row in enumerate(load_game(GAME).rows, 1)
                   if row["description"] == "나성범 : 우익수 앞 1루타")
        r = build_facts(GAME, seq)
        t = texts(r)
        self.assertEqual(r["type_tags"], ["SINGLE"])
        self.assertEqual(t[0], "1회초, 1사, 2,3루 (2루 카스트로, 3루 김호령), 점수 KIA 0-0 SSG")
        self.assertIn("타자 나성범, 투수 화이트", t)
        self.assertIn("주자 기록: 3루주자 김호령 : 홈인", t)
        self.assertIn("이 플레이로 득점: KIA 1점", t)
        self.assertTrue(any(x.startswith("플레이 후 1사, 1,3루") and "KIA 1-0 SSG" in x for x in t))

    def test_pitch_row(self):
        r = build_facts(GAME, 3)  # 1회초 김호령 1구
        t = texts(r)
        self.assertEqual(r["event_type"], "pitch")
        self.assertIn("타자 김호령, 투수 화이트", t)
        self.assertIn("1구 직구 151km/h 결과 볼", t)

    def test_non_pitch_and_restored_pitch(self):
        # 피치클락 위반은 공을 던진 게 아니므로 '기록 없음'이 아니라 '실제 투구 아님'
        clock = build_facts("20260328KTLG02026", 474)
        self.assertIn("피치클락 투수위반 볼 (실제 투구 아님)", texts(clock))
        # 4/15 키움–KIA 1회초 이주형 타석: 원본 누락, B3에서 수동 복원한 투구
        restored = texts(build_facts("20260415WOHT02026", 3))
        self.assertIn("1구 결과 스트라이크 (원본 누락으로 수동 복원, 구종·구속 원본 없음)", restored)

    def test_substitution_says_reason_missing(self):
        game = load_game(GAME)
        seq = next(i for i, row in enumerate(game.rows, 1) if row["event_type"] == "substitution")
        self.assertIn("교체 사유 기록 없음", texts(build_facts(GAME, seq, game)))

    def test_out_of_range(self):
        with self.assertRaises(IndexError):
            build_facts(GAME, 0)

    def test_ai_prompt_accepts_facts(self):
        from ai.explain.prompts import fact_lines

        r = build_facts(GAME, 3)
        self.assertEqual(fact_lines({"facts": r["facts"]}), r["facts"])


if __name__ == "__main__":
    unittest.main()
