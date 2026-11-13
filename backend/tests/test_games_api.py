"""B4 저장소 + 경기·플레이 조회 API 테스트.
data/raw 의 B1 v2 · B2 · B3 데이터로 3경기짜리 임시 DB를 만들어서 검사한다 (데이터 없으면 건너뜀).

실행 (저장소 루트에서):
    .venv/bin/python -m unittest backend.tests.test_games_api -v
"""

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api import games as games_api
from backend.api.main import app
from backend.game import store
from backend.game.facts import B2_DIR

GAME = "20260328HTSK02026"  # 3/28 KIA 6-7 SSG
RESTORED = "20260415WOHT02026"  # 1회초 이주형 타석: 네이버 원본 누락 → 수동 복원 + 다음 스포츠로 보완
OVERRIDE = "20261003WOHH02026"  # 3회말 정은원 2구: 네이버 값 오류 → 다음 스포츠 값으로 수정
HAS_DATA = (B2_DIR / f"{GAME}.json").exists()
client = TestClient(app)


@unittest.skipUnless(HAS_DATA, "data/raw 에 B1 v2 · B3 v2 데이터가 없음")
class GamesApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        db = Path(cls.tmp.name) / "test.sqlite"
        # 3/28 KIA–SSG + B3 보완 투구가 있는 4/15 키움–KIA, 10/3 키움–한화
        cls.info = store.build(db, game_ids=[GAME, RESTORED, OVERRIDE])
        cls.con = store.connect(db)
        cls._orig = games_api.get_con
        games_api.get_con = lambda: cls.con

    @classmethod
    def tearDownClass(cls):
        games_api.get_con = cls._orig
        cls.con.close()
        cls.tmp.cleanup()

    def test_build_counts(self):
        self.assertEqual(self.info["games"], 3)
        self.assertGreater(self.info["plays"], 0)
        self.assertGreater(self.info["pitches"], 0)

    def test_list_games(self):
        body = client.get("/games").json()
        self.assertEqual(body["count"], 3)
        kia = client.get("/games", params={"date": "2026-03-28", "team": "KIA"}).json()
        self.assertEqual([g["game_id"] for g in kia["games"]], [GAME])

    def test_game_detail(self):
        g = client.get(f"/games/{GAME}").json()
        self.assertEqual((g["away"], g["home"], g["away_score"], g["home_score"]), ("KIA", "SSG", 6, 7))
        self.assertTrue(g["final_score_match"])

    def test_plays_in_order_with_state(self):
        body = client.get(f"/games/{GAME}/plays").json()
        plays = body["plays"]
        self.assertEqual(body["count"], client.get(f"/games/{GAME}").json()["play_count"])
        self.assertEqual([p["seq"] for p in plays], list(range(1, len(plays) + 1)))
        self.assertNotIn("facts", plays[0])
        last = plays[-1]["state_after"]["score"]
        self.assertEqual((last["away"], last["home"]), (6, 7))  # 최종 점수와 B2 상태가 같다

    def test_filter_with_facts_and_pitch(self):
        body = client.get(f"/games/{GAME}/plays",
                          params={"event_type": "single,home_run", "facts": "true"}).json()
        self.assertTrue(body["count"] > 0)
        self.assertTrue(all(p["event_type"] in ("single", "home_run") for p in body["plays"]))
        self.assertTrue(all(p["facts"][0]["id"] == "F1" for p in body["plays"]))
        pitches = client.get(f"/games/{GAME}/plays",
                             params={"event_type": "pitch", "limit": 5, "pitch": "true"}).json()["plays"]
        self.assertEqual(len(pitches), 5)
        self.assertEqual(pitches[0]["pitch"]["pitch_type_raw"], "직구")
        # 같은 타석의 공은 plate_appearance_id 가 같다
        self.assertTrue(pitches[0]["pitch"]["plate_appearance_id"])
        self.assertEqual(pitches[0]["pitch"]["plate_appearance_id"],
                         pitches[1]["pitch"]["plate_appearance_id"])

    def test_single_play(self):
        p = client.get(f"/games/{GAME}/plays/3").json()
        self.assertEqual(p["event_type"], "pitch")
        self.assertEqual(p["pitch"]["speed"], 151.0)
        self.assertIn("1구 직구 151km/h 결과 볼", [f["text"] for f in p["facts"]])

    def test_b3_supplements_reach_db(self):
        # 수동 복원 투구: 타자·투수 칸이 채워지고, 보완한 구종·구속과 출처가 나온다
        p = client.get(f"/games/{RESTORED}/plays/3").json()
        self.assertEqual((p["batter"], p["pitcher"]), ("이주형", "김태형"))
        self.assertEqual((p["pitch"]["pitch_type_raw"], p["pitch"]["speed"]), ("직구", 150.0))
        self.assertIn("다음 스포츠", p["pitch"]["supplement_source"])
        # 네이버 값 오류 수정
        q = client.get(f"/games/{OVERRIDE}/plays/162").json()
        self.assertEqual((q["pitch"]["pitch_type_raw"], q["pitch"]["speed"]), ("스위퍼", 124.0))
        # 보완하지 않은 공은 출처 칸이 비어 있다
        self.assertIsNone(client.get(f"/games/{GAME}/plays/3").json()["pitch"]["supplement_source"])

    def test_pitch_count(self):
        pitches = [p["pitch"] for p in client.get(f"/games/{GAME}/plays",
                   params={"event_type": "pitch", "limit": 6, "pitch": "true"}).json()["plays"]]
        # 첫 공은 0-0 에서 시작하고, 앞 공의 '던진 후' 가 다음 공의 '던지기 전' 이다
        self.assertEqual(pitches[0]["count_before"], {"balls": 0, "strikes": 0})
        for a, b in zip(pitches, pitches[1:]):
            if a["plate_appearance_id"] == b["plate_appearance_id"]:
                self.assertEqual(a["count_after"], b["count_before"])
        # 4/15 '포수 파울 플라이 포구 실책' 줄은 앞 파울과 같은 공이라 카운트가 그대로다
        plays = client.get(f"/games/{RESTORED}/plays",
                           params={"event_type": "pitch", "pitch": "true"}).json()["plays"]
        i = next(i for i, p in enumerate(plays) if "파울 플라이 포구 실책" in p["description"])
        self.assertEqual(plays[i]["pitch"]["count_after"], plays[i - 1]["pitch"]["count_after"])

    def test_not_found(self):
        self.assertEqual(client.get("/games/NOPE").status_code, 404)
        self.assertEqual(client.get(f"/games/{GAME}/plays/99999").status_code, 404)


if __name__ == "__main__":
    unittest.main()
