"""
경기 상태 파일들을 훑어서 시연하기 좋은 경기 후보를 뽑음

찾는 것
  끝내기   : 홈팀이 9회말 이후 마지막 득점으로 이김
  역전     : 리드가 바뀐 횟수
  만루     : 만루 상황이 나온 횟수
  연장     : 10회 이상
  접전     : 최종 점수 차 1~2점

시연용 경기
20261007OBLG02026 두산 vs LG (10/7) https://youtu.be/YQD3hMI2LPo
20260516LTOB02026 롯데 9:10 두산 (두산 연장 끝내기 승) https://youtu.be/FaJDs51xcTU?si=yJX9La2_debQxuww
20260904KTHT02026 KT 3:4 KIA (KIA 연장 끝내기 승) https://youtu.be/zqPWIKkZLF0?si=IEGZHRgCcuQ2C8Rc

사용법
  python find_games.py ../../data/raw/b2_state_v2_all/games/ [--top 20] [--team KIA]
"""
import argparse
import glob
import json
import os


def analyze(path):
    d = json.load(open(path, encoding="utf-8"))
    s, rows = d.get("summary", {}), d.get("rows", [])
    if not rows:
        return None
    fa, fh = s.get("final_ours", {}).get("away"), s.get("final_ours", {}).get("home")
    if fa is None or fh is None or not s.get("final_score_match", True):
        return None

    lead, lead_changes, loaded, last_inning = 0, 0, 0, 0
    for r in rows:
        last_inning = max(last_inning, r["inning"])
        sa = r["state_after"]["score"]
        diff = sa["away"] - sa["home"]
        cur = (diff > 0) - (diff < 0)
        if cur != 0 and lead != 0 and cur != lead:
            lead_changes += 1
        if cur != 0:
            lead = cur
        if r["event_type"] == "batter_announcement" and all(
                r["state_before"]["runner_count"][b] > 0 for b in ("1", "2", "3")):
            loaded += 1

    # 끝내기: 마지막 반이닝이 9회 이후 말 공격이고, 그 반이닝 시작 때 홈팀이 이기고 있지 않았는데 홈팀이 이김
    last_half = (rows[-1]["inning"], rows[-1]["inning_half"])
    first_of_last = next(r for r in rows if (r["inning"], r["inning_half"]) == last_half)
    sb = first_of_last["state_before"]["score"]
    walkoff = (fh > fa and last_half[1] == "bottom" and last_half[0] >= 9 and sb["home"] <= sb["away"])

    # 경기 상태 파일 자체 검증 결과
    problems = []
    if s.get("half_innings_not_3_outs"):
        problems.append("3아웃 불일치")
    if s.get("naver_mismatch_rows"):
        problems.append(f'네이버 불일치 {len(s["naver_mismatch_rows"])}')
    if loaded >= 10:
        problems.append("만루 과다")

    score = 3 * walkoff + 2 * min(lead_changes, 3) + min(loaded, 3) + 2 * (last_inning >= 10) + (abs(fa - fh) <= 2)
    return {"game_id": s.get("game_id") or os.path.basename(path)[:-5],
            "match": f'{s.get("away")} {fa} : {fh} {s.get("home")}',
            "끝내기": "O" if walkoff else "", "역전": lead_changes, "만루": loaded,
            "연장": "O" if last_inning >= 10 else "", "점수차": abs(fa - fh), "추천점수": score,
            "문제": ", ".join(problems)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("games_dir")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--team", default=None, help="이 팀이 나온 경기만")
    args = ap.parse_args()

    out = []
    for p in sorted(glob.glob(os.path.join(args.games_dir, "*.json"))):
        try:
            a = analyze(p)
        except Exception:
            continue
        if a and (not args.team or args.team in a["match"]):
            out.append(a)
    bad = [a for a in out if a["문제"]]
    out = [a for a in out if not a["문제"]]
    out.sort(key=lambda a: -a["추천점수"])
    if bad:
        print(f"검증 문제가 있어서 뺀 경기 {len(bad)}개: " + ", ".join(f'{a["game_id"]}({a["문제"]})' for a in bad[:10])
              + (" ..." if len(bad) > 10 else "") + "\n")
    print(f"전체 {len(out)}경기 중 상위 {args.top}개\n")
    print(f'{"경기ID":<20}{"경기":<20}{"끝내기":<5}{"역전":<5}{"만루":<5}{"연장":<5}{"점수차":<6}{"점수"}')
    for a in out[:args.top]:
        print(f'{a["game_id"]:<20}{a["match"]:<20}{a["끝내기"]:<6}{a["역전"]:<6}{a["만루"]:<6}{a["연장"]:<6}{a["점수차"]:<7}{a["추천점수"]}')


if __name__ == "__main__":
    main()