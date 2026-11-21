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
    def test_extra_claim_goes_to_model(self):
        text = "실책 덕분에 아웃카운트는 무사에서 1사로 늘어났고, 주자는 계속 없는 상태를 유지했습니다."
        self.assertDropped(GROUNDOUT, text, ["F1", "F5"], LOW)
        r = self.assertKept(GROUNDOUT, text, ["F1", "F5"], HIGH)
        self.assertEqual(r["check"], "rule_v2+model")

    # 카드만 인용한 문장은 상태 규칙 대상이 아님
    def test_card_sentence_goes_to_model(self):
        pool = {**GROUNDOUT, "term.ground_ball": "[땅볼] 땅에 튀며 굴러가는 타구"}
        kept, _ = run(pool, "땅볼은 땅에 튀며 굴러가는 타구를 말합니다.", ["term.ground_ball"], HIGH)
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


if __name__ == "__main__":
    unittest.main()
