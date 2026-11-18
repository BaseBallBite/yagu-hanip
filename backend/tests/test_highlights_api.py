"""B12 하이라이트 장면 조회 API 테스트.
git에 있는 장면 표(ai/highlight/output)로 임시 DB를 만들어서 검사한다.

실행 (저장소 루트에서):
    .venv/bin/python -m unittest backend.tests.test_highlights_api -v
"""

import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api import highlights as highlights_api
from backend.api.main import app
from backend.game import store as game_store
from backend.highlight import store

DEMO = "YQD3hMI2LPo"  # 10/7 두산 vs LG (시연 경기)
DEMO_GAME = "20261007OBLG02026"
EVAL_GAMES = {"20261011LTHT02026", "20260723SSWO02026", "20260621SKNC02026", "20260328HTSK02026"}
client = TestClient(app)


class HighlightsApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        db = Path(cls.tmp.name) / "highlights.sqlite"
        cls.info = store.build(db)
        cls.con = store.connect(db, build_if_missing=False)
        cls._orig = highlights_api.get_con
        cls._orig_game = highlights_api.get_game_con
        highlights_api.get_con = lambda: cls.con
        highlights_api.get_game_con = lambda: None  # 기본은 경기 DB 없이 (장면 표 원본 그대로)
        cls.raw = json.loads((store.SCENE_DIR / f"scenes_{DEMO_GAME}.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        highlights_api.get_con = cls._orig
        highlights_api.get_game_con = cls._orig_game
        cls.con.close()
        cls.tmp.cleanup()

    def test_only_demo_games(self):
        """평가용 경기는 DB에 들어가면 안 된다."""
        ids = {h["game_id"] for h in client.get("/highlights").json()["highlights"]}
        self.assertEqual(ids, set(store.demo_game_ids()))
        self.assertIn(DEMO_GAME, ids)
        self.assertFalse(ids & EVAL_GAMES)

    def test_list_and_detail(self):
        h = client.get(f"/highlights/{DEMO}").json()
        self.assertEqual((h["game_id"], h["away"], h["home"], h["game_date"]),
                         (DEMO_GAME, "두산", "LG", "2026-10-07"))
        self.assertEqual(h["scene_count"], len(self.raw["scenes"]))
        self.assertEqual(h["duration_sec"], self.raw["scenes"][-1]["end"])

    def test_scenes_same_as_file(self):
        body = client.get(f"/highlights/{DEMO}/scenes").json()
        self.assertEqual(body["scenes"], self.raw["scenes"])
        self.assertEqual(body["count"], len(self.raw["scenes"]))

    def test_scene_at_time(self):
        # 노션 가이드 예시: 755~760초 5회말 이재원 타석
        s = client.get(f"/highlights/{DEMO}/scene", params={"t": 757.3}).json()
        self.assertEqual((s["status"], s["inning"], s["half"], s["batter"]), ("확정", 5, "말", "이재원"))
        self.assertEqual(s["situation"]["bases"], [True, True, False])

    def test_demo_scenes(self):
        """노션 가이드 '5. 시연 장면' 4개가 영상 시간에 맞는 상황으로 나오는지."""
        cases = [  # 영상 시간, 상태, 이닝, 초말, 타자, 아웃, 주자, 점수(원정, 홈), 방금
            ("7:15", "확정", 3, "초", "김민석", 2, [True, True, True], (1, 3), "양의지 : 몸에 맞는 볼"),
            ("8:00", "추정", 3, "초", "강승호", 2, [False, True, True], (3, 3), "김민석 : 우익수 앞 1루타"),
            ("10:40", "확정", 3, "말", "문보경", 1, [True, True, True], (5, 3), "문정빈 : 볼넷"),
            ("12:35", "확정", 5, "말", "이재원", 2, [True, True, False], (5, 5), "문보경 : 중견수 앞 1루타"),
        ]
        for mmss, status, inning, half, batter, outs, bases, score, prev in cases:
            m, s = mmss.split(":")
            got = client.get(f"/highlights/{DEMO}/scene", params={"t": int(m) * 60 + int(s)}).json()
            sit = got["situation"]
            self.assertEqual(
                (got["status"], got["inning"], got["half"], got["batter"], sit["outs"], sit["bases"],
                 (sit["score_away"], sit["score_home"])),
                (status, inning, half, batter, outs, bases, score), mmss)
            self.assertTrue(got["prev_play"].startswith(prev), mmss)

    def test_scene_boundaries(self):
        """start ≤ t < end: 경계 시간은 뒤 장면에 속한다."""
        scenes = self.raw["scenes"]
        for i in range(1, len(scenes)):
            t = scenes[i]["start"]
            got = client.get(f"/highlights/{DEMO}/scene", params={"t": t}).json()
            self.assertEqual(got, scenes[i], f"t={t}")

    def test_outside_video_is_unknown(self):
        end = self.raw["scenes"][-1]["end"]
        for t in (end, end + 100):
            self.assertEqual(client.get(f"/highlights/{DEMO}/scene", params={"t": t}).json(),
                             {"status": "확인 불가"})

    def test_errors(self):
        self.assertEqual(client.get("/highlights/nope").status_code, 404)
        self.assertEqual(client.get("/highlights/nope/scene", params={"t": 1}).status_code, 404)
        self.assertEqual(client.get(f"/highlights/{DEMO}/scene", params={"t": -1}).status_code, 422)
        self.assertEqual(client.get(f"/highlights/{DEMO}/scene").status_code, 422)

    def test_bad_scene_file_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            bad = dict(self.raw, scenes=[{"start": 10, "end": 5, "status": "확인 불가"}])
            Path(d, f"scenes_{DEMO_GAME}.json").write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaises(ValueError):
                store.build(Path(d) / "x.sqlite", game_ids=[DEMO_GAME], scene_dir=Path(d))


@unittest.skipUnless(game_store.DB_PATH.exists(), "경기 DB(yagu.sqlite)가 없어서 건너뜀")
class HighlightTypeTagsTest(unittest.TestCase):
    """경기 DB가 있으면 장면에 유형 태그가 붙어서 /dict/events/{태그} 로 용어 카드를 찾을 수 있다."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        db = Path(cls.tmp.name) / "highlights.sqlite"
        store.build(db)
        cls.con = store.connect(db, build_if_missing=False)
        cls.game_con = game_store.connect()
        cls._orig, cls._orig_game = highlights_api.get_con, highlights_api.get_game_con
        highlights_api.get_con = lambda: cls.con
        highlights_api.get_game_con = lambda: cls.game_con

    @classmethod
    def tearDownClass(cls):
        highlights_api.get_con, highlights_api.get_game_con = cls._orig, cls._orig_game
        cls.con.close()
        cls.game_con.close()
        cls.tmp.cleanup()

    def test_1235_error_tags(self):
        """12:35 이재원 내야안타 → 실책 홈인. 결과 태그에 ERROR, 방금(문보경 1루타)은 SINGLE."""
        s = client.get(f"/highlights/{DEMO}/scene", params={"t": 755}).json()
        self.assertIn("ERROR", s["result_type_tags"])
        self.assertIn("SINGLE", s["prev_type_tags"])
        # 시연 흐름: 12:35 → 용어 카드 "실책"
        titles = [c["title"] for c in client.get("/dict/events/ERROR").json()["items"]]
        self.assertIn("실책", titles)

    def test_715_hit_by_pitch(self):
        s = client.get(f"/highlights/{DEMO}/scene", params={"t": 435}).json()
        self.assertIn("HIT_BY_PITCH", s["prev_type_tags"])

    def test_scenes_keep_original_fields(self):
        """태그만 더해지고 장면 표 원래 값은 그대로."""
        raw = json.loads((store.SCENE_DIR / f"scenes_{DEMO_GAME}.json").read_text(encoding="utf-8"))
        got = client.get(f"/highlights/{DEMO}/scenes").json()["scenes"]
        extra = {"prev_type_tags", "result_type_tags"}
        self.assertEqual([{k: v for k, v in g.items() if k not in extra} for g in got], raw["scenes"])
        tagged = [g for g in got if "result_type_tags" in g]
        with_id = [r for r in raw["scenes"] if r.get("play_id")]
        self.assertEqual(len(tagged), len(with_id))
        unknown = [g for g in got if g["status"] == "확인 불가"]
        self.assertTrue(all("result_type_tags" not in g for g in unknown))


if __name__ == "__main__":
    unittest.main()
