"""verify_service 상태 규칙 대조 테스트.

  cd ai/explain && python -m unittest test_verify_service_state -v

모델 대신 p_support를 고정값으로 돌려주는 함수를 씀(실제 KLUE가 맞는 상태 문장에 주던 0.001대 점수).
"""
import unittest

import verifier

LOW = lambda pairs: [0.001 for _ in pairs]   # KLUE가 상태 문장을 떨어뜨리던 상황
HIGH = lambda pairs: [0.99 for _ in pairs]

GROUNDOUT = {
    "F1": "1회말, 무사, 주자 없음, 점수 KIA 3-0 키움",
    "F2": "타자 서건창, 투수 양현종",
    "F3": "기록: 서건창 : 2루수 땅볼 아웃 (2루수->1루수 송구아웃)",
    "F4": "이 타석 투구 수 4개, 마지막 공: 4구 슬라이더 133km/h 결과 타격",
    "F5": "플레이 후 1사, 주자 없음, 점수 KIA 3-0 키움",
    "R1": "1구 볼", "R2": "2구 스트라이크", "R3": "3구 파울", "R4": "4구 타격",
}
STEAL = {
    "F1": "2회초, 2사, 1루 (1루 강승호), 점수 두산 0-0 LG",
    "F2": "기록: 1루주자 강승호 : 도루로 2루까지 진루",
    "F3": "플레이 후 2사, 2루 (2루 강승호), 점수 두산 0-0 LG",
}
INNING_END = {
    "F1": "2회초, 2사, 2루 (2루 강승호), 점수 두산 0-0 LG",
    "F2": "타자 양석환, 투수 임찬규",
    "F3": "기록: 양석환 : 3루수 라인드라이브 아웃",
    "F5": "플레이 후 3아웃, 2루 (2루 강승호), 점수 두산 0-0 LG",
}
WALK = {
    "F1": "3회초, 2사, 2루 (2루 강승호), 점수 두산 5-3 LG",
    "F3": "기록: 양석환 : 볼넷",
    "F4": "이 타석 투구 수 7개, 마지막 공: 7구 직구 141km/h 결과 볼",
    "F5": "플레이 후 2사, 1,2루 (1루 양석환, 2루 강승호), 점수 두산 5-3 LG",
    "R1": "1구 볼", "R2": "2구 볼", "R3": "3구 헛스윙", "R4": "4구 볼", "R5": "5구 스트라이크", "R6": "6구 파울", "R7": "7구 볼",
}
HOMER = {
    "F1": "2회초, 무사, 주자 없음, 점수 롯데 0-0 한화",
    "F2": "타자 한동희, 투수 박준영",
    "F3": "기록: 한동희 : 좌익수 뒤 홈런 (홈런거리:110M)",
    "F5": "플레이 후 무사, 주자 없음, 점수 롯데 1-0 한화",
    "F6": "이 플레이로 득점: 롯데 1점",
}
PLAYERS = ["서건창", "양현종", "강승호", "양석환", "임찬규"]


def run(pool, text, ev, p=LOW, **kw):
    out = verifier.verify_service({"sentences": [{"text": text, "evidence": ev}]}, pool, PLAYERS, p, threshold=0.05, **kw)
    return out["sentences"], out["dropped"]


class StateRuleTest(unittest.TestCase):
    def assertKept(self, pool, text, ev, p=LOW):
        kept, dropped = run(pool, text, ev, p)
        self.assertEqual(len(kept), 1, dropped)
        return kept[0]

    def assertDropped(self, pool, text, ev, p=LOW):
        kept, dropped = run(pool, text, ev, p)
        self.assertEqual(len(dropped), 1, kept)
        return dropped[0]

    # 맞는 상태 문장: 모델 점수가 낮아도 상태 규칙으로 유지
    def test_outs_change_kept(self):
        r = self.assertKept(GROUNDOUT, "이 플레이로 아웃카운트는 무사에서 1사로 늘어났고, 주자는 계속 없는 상태를 유지했습니다.", ["F1", "F5"])
        self.assertEqual(r["check"], "rule_v2+state")

    def test_steal_kept(self):
        self.assertKept(STEAL, "이 도루로 아웃카운트는 2아웃 그대로 유지되었고, 주자 위치는 1루 강승호에서 2루 강승호로 바뀌었습니다.", ["F1", "F3"])

    def test_inning_end_runner_left_kept(self):
        self.assertKept(INNING_END, "이 플레이로 3아웃이 되면서 강승호 선수는 2루에 남은 채 두산의 2회초 공격이 끝났습니다.", ["F5"])

    def test_pitch_count_kept(self):
        self.assertKept(WALK, "양석환 선수는 이 타석에서 7번째 공까지 승부한 끝에 4번째 볼을 골라내며 1루로 진루했습니다.", ["R1", "R2", "R4", "R7", "F4", "F5"])

    # 값이 하나라도 틀리면 삭제 (모델 점수가 높아도)
    def test_wrong_runner_dropped(self):
        # 숫자 검사(규칙 v2)는 '1루'의 1을 위치 숫자로 빼서 못 잡음. 상태 규칙이 잡아야 함
        r = self.assertDropped(GROUNDOUT, "이 플레이로 아웃카운트는 무사에서 1사로 늘어났고, 주자는 1루에 남았습니다.", ["F1", "F5"], HIGH)
        self.assertIn("상태 규칙", r["verdict"])

    def test_wrong_runner_base_dropped(self):
        self.assertDropped(STEAL, "이 도루로 아웃카운트는 2아웃 그대로 유지되었고, 주자 위치는 1루 강승호에서 3루 강승호로 바뀌었습니다.", ["F1", "F3"], HIGH)

    def test_wrong_left_base_dropped(self):
        self.assertDropped(INNING_END, "이 플레이로 3아웃이 되면서 강승호 선수는 3루에 남은 채 두산의 2회초 공격이 끝났습니다.", ["F5"], HIGH)

    def test_wrong_hyphen_score_dropped(self):
        self.assertDropped(GROUNDOUT, "이 플레이로 아웃카운트는 무사에서 1사로 늘어났고, 점수는 KIA 3-1 키움으로 변함이 없었습니다.", ["F1", "F5"], HIGH)

    def test_wrong_runner_dest_dropped(self):
        self.assertDropped(WALK, "양석환 선수는 이 타석에서 7번째 공까지 승부한 끝에 4번째 볼을 골라내며 2루로 진루했습니다.", ["R1", "R2", "R4", "R7", "F4", "F5"], HIGH)

    # 상태는 맞지만 다른 주장이 섞이면 모델로 넘김
    # 11/24 새 3경기(BE1)에서 KLUE가 지운 맞는 상태 문장 (p 0.0012~0.0121)
    def test_new3games_state_sentences_kept(self):
        for text, pool in [
            ("이 플레이로 아웃카운트는 무사에서 1사로 늘어났으며, 주자는 계속 없고 점수도 KIA 3-0 키움으로 변화가 없습니다.", GROUNDOUT),
            ("이 플레이로 아웃카운트는 늘어나지 않아 2사가 이어졌고, 양석환 선수가 1루에 진루하면서 점수는 두산 5-3 LG 상태를 유지했습니다.", WALK),
            ("이 플레이로 아웃카운트의 증가 없이 2사 상태가 유지되었고, 타자 양석환 선수가 1루에 나가 주자가 생겼으며 점수는 여전히 두산 5-3 LG로 유지되었습니다.", WALK),
        ]:
            r = self.assertKept(pool, text, ["F1", "F5"])
            self.assertEqual(r["check"], "rule_v2+state")

    # 11/24 새 경기(BE1): F에 "이 플레이로 득점: 롯데 1점" 형식이 있으면 플레이 전 점수(0-0)도 맞는 값
    def test_scoring_play_before_after_score_kept(self):
        text = "이 홈런으로 롯데가 1점을 올려 점수는 0-0에서 롯데 1-0 한화가 되었으며, 플레이 후에도 아웃카운트 없이 주자가 없는 무사 상태가 이어졌습니다."
        kept, dropped = run(HOMER, text, ["F1", "F5", "F6"], HIGH)
        self.assertEqual(len(kept), 1, dropped)
        wrong = "이 홈런으로 롯데가 1점을 올려 점수는 0-0에서 롯데 2-0 한화가 되었습니다."
        kept, dropped = run(HOMER, wrong, ["F1", "F5", "F6"], HIGH)
        self.assertEqual(len(dropped), 1, kept)

    # F에 주자로 없는 선수를 베이스에 보낸 문장은 삭제
    def test_unknown_runner_dropped(self):
        r = self.assertDropped(GROUNDOUT, "이 플레이로 아웃카운트는 1사가 되었고, 양현종 선수가 1루에 진루했습니다.", ["F2", "F5"], HIGH)
        self.assertEqual(r["check"], "rule_v2+state")

    def test_extra_claim_goes_to_model(self):
        text = "실책 덕분에 아웃카운트는 무사에서 1사로 늘어났고, 주자는 계속 없는 상태를 유지했습니다."
        self.assertDropped(GROUNDOUT, text, ["F1", "F5"], LOW)
        r = self.assertKept(GROUNDOUT, text, ["F1", "F5"], HIGH)
        self.assertEqual(r["check"], "rule_v2+model")

    # 카드만 인용한 문장은 상태 규칙 대상이 아님 (카드 대조를 끄면 모델로 감)
    def test_card_sentence_goes_to_model(self):
        pool = {**GROUNDOUT, "term.ground_ball": "[땅볼] 땅에 튀며 굴러가는 타구"}
        kept, _ = run(pool, "땅볼은 땅에 튀며 굴러가는 타구를 말합니다.", ["term.ground_ball"], HIGH, card_rule=False)
        self.assertEqual(kept[0]["check"], "rule_v2+model")

    # 끄면 예전과 같음
    def test_state_rule_off(self):
        kept, dropped = run(GROUNDOUT, "이 플레이로 아웃카운트는 무사에서 1사로 늘어났고, 주자는 계속 없는 상태를 유지했습니다.",
                            ["F1", "F5"], LOW, state_rule=False)
        self.assertEqual((len(kept), len(dropped)), (0, 1))

    def test_unknown_unchanged(self):
        out = verifier.verify_service({"sentences": [{"text": "투수 교체 이유는 기록에 없어 알 수 없습니다.", "evidence": ["UNKNOWN"]}]},
                                      GROUNDOUT, PLAYERS, LOW)
        self.assertEqual(out["sentences"][0]["check"], "unknown_rule")



# BE1 서비스 카드 본문 모양 그대로 (출처 포함)
HIT = ("[안타] (출처: 9.05 안타) 수비 실수 없이 타자가 쳐서 베이스에 나간 거예요. 타자가 친 공이 페어가 되고, "
       "실책이나 야수선택 없이 타자가 1루 이상 가면 안타예요. 1루까지 가면 단타, 2루는 2루타, 3루는 3루타, 홈까지 오면 홈런이에요.")
BB = ("[볼넷] (출처: 용어의 정의 7. BASE ON BALLS, 5.05(b)(1), 규칙위원회 합의(2018.3.5), 9.14) 스트라이크 존을 벗어난 공 4개를 "
      "골라내면 1루로 걸어 나가요. 타자가 치지 않은 공 중 스트라이크 존 밖으로 들어온 공이 4개가 되면 1루가 주어져요. "
      "수비팀 감독이 고의4구를 알리면 공을 던지지 않아도 바로 1루로 보내요(자동 고의4구). 만루에서 볼넷이 나오면 3루 주자가 밀려 들어와 1점이 나요.")
AWARD = ("[안전진루권] (출처: 5.06(b)(2)(3), 5.06(c)(3)) 볼넷이나 몸에 맞는 공처럼 정해진 경우 아웃될 걱정 없이 베이스가 주어지는 거예요. "
         "타자가 아웃될 염려 없이 1루에 나가야 할 때(볼넷, 몸에 맞는 공, 타격방해) 그 때문에 베이스를 비워줘야 하는 주자들도 "
         "한 베이스씩 안전하게 진루해요. 그 밖에 보크가 선언되면 모든 주자가 한 베이스 진루해요. 안전진루권을 얻었다고 해도 베이스를 밟아야 인정돼요.")
IFF = ("[인필드 플라이] (출처: 용어의 정의 40. INFIELD FLY) 무사나 1사에 주자가 1·2루 또는 만루일 때 내야로 높이 뜬 공이 나오면 "
       "심판이 인필드 플라이를 선언해요. 선언되면 공을 잡든 못 잡든 타자는 아웃이에요.")
CARDS = {**GROUNDOUT, "term.hit": HIT, "rule.base_on_balls": BB, "rule.award_bases": AWARD, "rule.infield_fly": IFF}


class CardRuleTest(unittest.TestCase):
    def check(self, text, ev):
        kept, dropped = run(CARDS, text, ev, LOW)
        return (kept + dropped)[0], bool(kept)

    # BE1 3경기에서 KLUE가 지운 맞는 카드 문장 (p 0.0008~0.0114) -> 유지
    def test_be1_card_sentences_kept(self):
        cases = [
            ("1루타는 타자가 수비 실수 없이 공을 쳐서 1루까지 안전하게 진루하는 안타를 말합니다.", ["term.hit"]),
            ("1루타는 타자가 수비 실수 없이 공을 쳐서 안전하게 1루까지 살아 들어가는 안타를 말합니다.", ["term.hit"]),
            ("1루타(단타)는 수비 실책 없이 타자가 공을 쳐서 1루까지 안전하게 진루하는 안타를 말합니다.", ["term.hit"]),
            ("볼넷은 투수가 던진 공 중 스트라이크 존을 벗어난 공 4개를 골라내면 아웃 걱정 없이 1루로 걸어 나가는 규칙입니다.",
             ["rule.base_on_balls", "rule.award_bases"]),
        ]
        for text, ev in cases:
            r, kept = self.check(text, ev)
            self.assertTrue(kept, (text, r))
            self.assertEqual(r["check"], "rule_v2+card")

    # 카드를 바꿔 쓴 틀린 문장 -> 카드 대조 통과 못 함. 모델(여기서는 낮은 점수)이나 규칙 v2가 지움
    def test_distorted_card_sentences_go_to_model(self):
        cases = [
            ("볼넷은 스트라이크 존을 벗어난 공 3개를 골라내면 1루로 걸어 나가는 규칙입니다.", ["rule.base_on_balls"]),   # 숫자
            ("2루타는 타자가 수비 실수 없이 1루까지 가는 안타를 말합니다.", ["term.hit"]),                               # 구절 섞기
            ("1루타는 타자가 2루까지 가는 안타를 말합니다.", ["term.hit"]),                                               # 베이스
            ("안타는 실책으로 타자가 1루에 나가도 안타로 기록하는 것을 말합니다.", ["term.hit"]),                       # 부정 빠짐
            ("인필드 플라이는 1사에 만루일 때 심판이 선언하는 규칙입니다.", ["rule.infield_fly"]),                       # 조건 좁힘
            ("양석환 선수는 스트라이크 존을 벗어난 공 4개를 골라내 1루로 걸어 나갔습니다.", ["rule.base_on_balls"]),    # 선수 이름
            ("볼넷이 나오면 감독이 퇴장을 당하는 규칙입니다.", ["rule.base_on_balls"]),                                   # 카드에 없는 말
        ]
        for text, ev in cases:
            r, kept = self.check(text, ev)
            self.assertFalse(kept, (text, r))
            self.assertNotEqual(r["check"], "rule_v2+card", (text, r))

    # F/R을 같이 인용한 문장은 카드 대조 대상이 아님
    def test_mixed_citation_not_card_rule(self):
        r, _ = self.check("서건창 선수는 2루수 땅볼로 아웃됐고 안타를 치지 못했습니다.", ["F3", "term.hit"])
        self.assertNotEqual(r["check"], "rule_v2+card")

    def test_card_rule_off(self):
        kept, dropped = run(CARDS, "1루타는 타자가 수비 실수 없이 공을 쳐서 1루까지 안전하게 진루하는 안타를 말합니다.",
                            ["term.hit"], LOW, card_rule=False)
        self.assertEqual((len(kept), len(dropped)), (0, 1))


if __name__ == "__main__":
    unittest.main()
