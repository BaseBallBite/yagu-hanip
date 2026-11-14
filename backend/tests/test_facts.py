"""B3 플레이 사실(F) 테스트. 실제 data/raw 의 B1 v2 · B2 · B3 데이터를 읽는다.
data/raw 는 git에 없으므로 데이터가 없으면 건너뛴다.

실행 (저장소 루트에서):
    .venv/bin/python -m unittest backend.tests.test_facts -v
"""

import unittest
from pathlib import Path

from backend.game.facts import (B1_TAG, B2_DIR, EVENT_TAG, ROOT, build_facts, build_game_facts, load_game,
                                row_tags)

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
        self.assertEqual(r["type_tags"], ["SINGLE", "ADVANCE", "SCORE"])  # 뒤따른 주자 줄: 2루→3루 진루, 홈인
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
        # 4/15 키움–KIA 1회초 이주형 타석: 네이버 원본 누락 → B1 v2 수동 복원 행.
        # 구종·구속은 data/supplements/pitch_supplements.json (다음 스포츠 중계)로 보완,
        # 타자·투수 이름은 같은 반이닝 기록에서 채운다.
        restored = texts(build_facts("20260415WOHT02026", 3))
        self.assertIn("타자 이주형, 투수 김태형", restored)
        self.assertIn("1구 직구 150km/h 결과 스트라이크 (네이버 원본 누락, 다음 스포츠 문자중계로 보완)",
                      restored)
        # 10/3 키움–한화 3회말 정은원 2구: 네이버 값이 깨져 있어 다음 스포츠 값으로 수정 (override)
        fixed = texts(build_facts("20261003WOHH02026", 162))
        self.assertIn("2구 스위퍼 124km/h 결과 타격 (네이버 값 구종 없음·151km/h를 다음 스포츠 문자중계 값으로 수정)",
                      fixed)
        single = texts(build_facts("20260415WOHT02026", 6))
        self.assertIn("기록: 이주형 : 좌익수 앞 1루타", single)
        self.assertFalse(any("기록 없음" in t for t in single))

    def test_substitution_says_reason_missing(self):
        game = load_game(GAME)
        seq = next(i for i, row in enumerate(game.rows, 1) if row["event_type"] == "substitution")
        self.assertIn("교체 사유 기록 없음", texts(build_facts(GAME, seq, game)))

    def test_out_of_range(self):
        with self.assertRaises(IndexError):
            build_facts(GAME, 0)

    def test_sac_fly_tag_up(self):
        # 3/28 KT–LG 3회말 문성주 희생플라이 → 3루주자 오스틴 홈인
        r = build_facts("20260328KTLG02026", 240)
        self.assertEqual(r["type_tags"], ["SAC_FLY", "SCORE", "TAG_UP"])

    def test_ai_prompt_accepts_facts(self):
        from ai.explain.prompts import fact_lines

        r = build_facts(GAME, 3)
        self.assertEqual(fact_lines({"facts": r["facts"]}), r["facts"])


class RowTagsTest(unittest.TestCase):
    """줄 하나 → 유형 태그 (docs/event_types.md 60개 기준). 데이터 없이 돈다."""

    CASES = [
        # 교체
        ("substitution", "투수 화이트 : 투수 전영준 (으)로 교체", ["PITCHING_CHANGE"]),
        ("substitution", "9번타자 김규성 : 대타 고종욱 (으)로 교체", ["PINCH_HITTER"]),
        ("substitution", "1루주자 최형우 : 대주자 박정우 (으)로 교체", ["PINCH_RUNNER"]),
        ("substitution", "대타 고종욱 : 좌익수(으)로 수비위치 변경", ["POSITION_CHANGE"]),
        ("substitution", "대타 한준수 : 포수 김태군 (으)로 교체", ["DEFENSIVE_SUB"]),
        ("substitution", "2루수 김선빈 : 2루수 홍종표 (으)로 교체", ["DEFENSIVE_SUB"]),
        # 주자 이동: 원인 없는 진루·득점, 원인 있는 진루, 아웃
        ("runner_advance", "1루주자 박찬호 : 2루까지 진루", ["ADVANCE"]),
        ("run_scored", "3루주자 김호령 : 홈인", ["SCORE"]),
        ("runner_advance", "1루주자 박지훈 : 주자의 재치로 2루까지 진루", ["ADVANCE_ON_THROW"]),
        ("runner_advance", "1루주자 김현수 : 다른주자수비하는 사이 2루까지 진루 (우익수->포수)",
         ["ADVANCE_ON_PLAY"]),
        ("runner_advance", "2루주자 박해민 : 폭투로 3루까지 진루", ["WILD_PITCH"]),
        ("runner_advance", "1루주자 이주형 : 투수 실책으로 2루까지 진루 (투수 견제 송구 실책->1루수)",
         ["ERROR"]),
        ("runner_out", "1루주자 김도영 : 포스아웃 (유격수->2루수 2루 터치아웃)", ["FORCE_OUT"]),
        ("runner_out", "2루주자 문보경 : 태그아웃 (좌익수->포수 태그아웃)", ["TAG_OUT"]),
        ("runner_out", "1루주자 정현창 : 폭투사이 진루실패아웃 (포수->2루수 태그아웃)", ["OUT_ON_ADVANCE"]),
        ("runner_out", "1루주자 김한홀 : 타구맞음 아웃", ["BATTED_BALL_HIT_RUNNER"]),
        ("steal", "1루주자 신민재 : 이중도루로 2루까지 진루", ["STOLEN_BASE"]),
        ("steal", "1루주자 김지찬 : 무관심도루로 2루까지 진루", ["UNCONTESTED_ADVANCE"]),
        ("caught_stealing", "1루주자 박성한 : 이중도루 실패시 2루까지 진루", ["DOUBLE_STEAL_ADVANCE"]),
        ("caught_stealing", "1루주자 최원준 : 도루실패아웃 (투수 견제->1루수->2루수 태그아웃)", ["CAUGHT_STEALING"]),
        ("run_scored", "3루주자 박민우 : 이중도루로 홈인", ["STOLEN_BASE"]),
        ("runner_advance", "1루주자 김현수 : 주루방해로 2루까지 진루", ["OBSTRUCTION"]),
        # 타석 결과
        ("triple_play", "전병우 : 3루수 삼중살 아웃 (3루수->2루수->1루수 송구아웃)", ["TRIPLE_PLAY"]),
        ("bunt_out", "김호령 : 투수 번트 아웃 (투수->1루수 송구아웃)", ["BUNT_OUT"]),
        ("batted_ball_out", "정준재 : 타구맞음 아웃", ["BATTED_BALL_HIT_RUNNER"]),
        ("reach_unspecified", "박찬호 : 유격수 앞 땅볼로 출루", ["FIELDERS_CHOICE"]),
        ("flyout", "박한결 : 유격수 인필드플라이 아웃", ["FLYOUT", "INFIELD_FLY"]),
        # 상황 메모
        ("mound_visit", "코칭스태프 마운드 방문", ["MOUND_VISIT"]),
        ("check_swing_notice", "5회초 7번타순 3구 체크스윙 → 노 스윙 : 키움 김건희", ["CHECK_SWING_CALL"]),
        ("pitcher_disengagement", "투수 투수판 이탈", ["PITCHER_STEP_OFF"]),
        ("pitch", "2구 피치클락 투수위반 볼", ["PITCH_CLOCK_VIOLATION"]),
        ("ejection_notice", "5회초 7번타순 2구 후 헤드샷 관련 퇴장: 한화 엄상백", ["EJECTION"]),
        ("abs_notice", "2회초 1번타순 6구 후 ABS 추적 실패로 심판 자체 판정: 볼", ["ABS_STATUS"]),
        ("break_notice", "6회초 5번타순 초구 전 2분간 폭염 관련 쿨링 브레이크 추가", ["GAME_STOPPAGE"]),
        ("play_notice", "7회말 3번타순 6구 후 21:16~21:56 (40분간) 우천 관련(으)로 경기 중단",
         ["GAME_STOPPAGE"]),
        ("play_notice", "7회말 1번타순 1구 후 와인드업 투구 자세에서 자유족을 뺀 이후 투수판 이탈 경고: 두산 김동주",
         ["WARNING"]),
        ("play_notice", "5회말 1번타순 1구 후 고의낙구 선언", ["INTENTIONAL_DROP"]),
        ("play_notice", "7회말 6번타순 4구 후 21:12~21:22 (10분간) 김성철 대기심이 주심(으)로 교체",
         ["UMPIRE_CHANGE"]),
        ("play_notice", "9회초 7번타순 6구 후 2루베이스 맞고 좌중간 방향으로 굴절", ["RULING_NOTE"]),
        ("play_notice", "2회초 8번타순 2구 후 타구가 천장에 맞음: NC 김형준", ["RULING_NOTE"]),
        ("play_notice", "11회말 1번타순 1구 후 2루주자 정수빈 3피트라인 아웃 선언", ["INTERFERENCE"]),
        ("game_status_notice", "7회말 1번타순 2구 후 강우 콜드게임 선언", ["GAME_CALLED"]),
        ("video_review", "9회말 2번타순 2구 후 21:42 비디오판독 판정 항의 관련 퇴장: 롯데 김태형 감독",
         ["VIDEO_REVIEW", "EJECTION"]),
        ("video_review", "4회초 9번타순 초구 전 방송사 중계시스템 오류로 인하여 비디오판독 불가한 상태로 경기진행",
         ["ADMIN_NOTE"]),
    ]

    def test_cases(self):
        for et, text, want in self.CASES:
            self.assertEqual(row_tags(et, text), want, text)
            self.assertLessEqual(set(want), ALLOWED_TAGS, text)

    def test_all_60_types_have_a_rule(self):
        """구조 행 2개와 계산으로 붙는 TAG_UP 말고는 모든 유형이 줄 규칙 하나 이상으로 나온다."""
        covered = {t for _, _, want in self.CASES for t in want}
        covered |= set(EVENT_TAG.values()) | set(B1_TAG.values())
        self.assertEqual(ALLOWED_TAGS - covered, {"SEPARATOR", "GAME_RESULT_NOTICE", "TAG_UP"})


if __name__ == "__main__":
    unittest.main()
