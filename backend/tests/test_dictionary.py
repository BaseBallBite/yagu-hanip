"""B7 사전 API 테스트. 실제 data/dict/dict.json 을 읽는다.

실행 (저장소 루트에서):
    .venv/bin/python -m unittest backend.tests.test_dictionary -v
"""

import unittest

from fastapi.testclient import TestClient

from backend.api.dictionary import get_store, normalize
from backend.api.main import app

client = TestClient(app)


class DictionaryApiTest(unittest.TestCase):
    def test_categories_cover_all_cards(self):
        res = client.get("/dict/categories")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual([k["kind"] for k in body], ["rule", "term"])
        total = sum(k["count"] for k in body)
        self.assertEqual(total, len(get_store().cards))
        for k in body:
            self.assertEqual(k["count"], sum(c["count"] for c in k["categories"]))

    def test_list_filter_by_kind_and_category(self):
        rules = client.get("/dict/cards", params={"kind": "rule"}).json()
        self.assertTrue(rules["count"] > 0)
        self.assertTrue(all(c["kind"] == "rule" for c in rules["items"]))
        run = client.get("/dict/cards", params={"kind": "rule", "category": "주루 규칙"}).json()
        self.assertTrue(run["count"] > 0)
        self.assertTrue(all(c["category"] == "주루 규칙" for c in run["items"]))
        # 목록은 요약만 내려준다
        self.assertNotIn("easy", rules["items"][0])

    def test_bad_kind_is_rejected(self):
        self.assertEqual(client.get("/dict/cards", params={"kind": "x"}).status_code, 422)

    def test_detail_has_full_card_and_related(self):
        res = client.get("/dict/cards/rule.infield_fly")
        self.assertEqual(res.status_code, 200)
        card = res.json()
        self.assertEqual(card["title"], "인필드 플라이")
        self.assertIn("easy", card)
        self.assertIn("when", card)
        self.assertEqual(len(card["related_cards"]), len(card["related"]))
        for r in card["related_cards"]:
            if r["exists"]:
                self.assertIsNotNone(r["title"])

    def test_detail_404(self):
        res = client.get("/dict/cards/term.nope")
        self.assertEqual(res.status_code, 404)

    def test_search_title_exact_first(self):
        items = client.get("/dict/search", params={"q": "인필드 플라이"}).json()["items"]
        self.assertEqual(items[0]["id"], "rule.infield_fly")
        self.assertEqual(items[0]["matched_by"], "title")

    def test_search_ignores_spaces_and_uses_alias(self):
        items = client.get("/dict/search", params={"q": "인필드플라이"}).json()["items"]
        self.assertEqual(items[0]["id"], "rule.infield_fly")
        items = client.get("/dict/search", params={"q": "로봇 심판"}).json()["items"]
        self.assertEqual(items[0]["id"], "rule.abs")
        self.assertEqual(items[0]["matched_by"], "alias")

    def test_search_case_insensitive(self):
        items = client.get("/dict/search", params={"q": "abs"}).json()["items"]
        self.assertIn("rule.abs", [i["id"] for i in items])

    def test_search_empty_and_no_hit(self):
        self.assertEqual(client.get("/dict/search", params={"q": ""}).status_code, 422)
        body = client.get("/dict/search", params={"q": "없는말쀍"}).json()
        self.assertEqual(body["count"], 0)

    def test_events(self):
        body = client.get("/dict/events/walk").json()
        self.assertEqual(body["event_type"], "WALK")
        self.assertIn("rule.base_on_balls", [c["id"] for c in body["items"]])
        self.assertEqual(client.get("/dict/events/NOT_A_TYPE").json()["count"], 0)

    def test_aliases_all_point_to_cards(self):
        aliases = client.get("/dict/aliases").json()
        self.assertTrue(len(aliases) > 0)
        cards = get_store().cards
        self.assertTrue(all(cid in cards for cid in aliases.values()))

    def test_normalize(self):
        self.assertEqual(normalize(" Infield  Fly "), "infieldfly")


if __name__ == "__main__":
    unittest.main()
