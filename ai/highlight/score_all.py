"""
여러 경기 합쳐서 채점 + 정답표 오류 검사

사용법 (ai/highlight 안에서)
  python score_all.py 20260328HTSK02026=readings_v2.json 20260621SKNC02026 20260723SSWO02026 20261011LTHT02026

  - 경기ID만 쓰면 readings_<경기ID>.json 을 씀
  - 경기ID=파일 로 쓰면 그 파일을 씀 (3/28은 readings_v2.json)
  - 정답표는 eval/정답표_<경기ID>.csv

하는 일
  1) 정답표 검사: 정답 타자가 그 이닝 기록에 실제로 있는지 확인
     (투수 이름을 적었거나, 오타, 다른 이닝 타자를 적은 경우를 찾아줌)
  2) 경기별 + 전체 채점 (그대로 믿기 / 기록 대조 / 기록 대조 + 10초 이어받기)
  3) 보고서용 표를 score_all_report.md 로 저장
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import match  # noqa: E402
import score  # noqa: E402

GAMES_DIR = os.path.join(HERE, "..", "..", "data", "raw", "b2_state_v2_all", "games")
HALF_KO = {"top": "초", "bottom": "말"}
METHODS = [("그대로 믿기", "strict", 0), ("기록 대조", "soft", 0), ("기록 대조 + 10초 이어받기", "soft", 10)]


def check_truth(truth, pas, rows):
    """정답 타자가 그 반이닝 타석 목록에 있는지 확인."""
    by_half = defaultdict(set)
    all_batters = set()
    for p in pas:
        if p["moments"]:
            by_half[(p["inning"], p["half"])].add(p["batter"])
            all_batters.add(p["batter"])
    pitchers = set()
    for r in rows:
        for m in re.finditer(r"투수\s+([가-힣A-Za-z]+)", r["description"]):
            pitchers.add(m.group(1))

    warns = []
    for t in truth:
        if t["truth"] is None:
            continue
        inn, half, name = t["truth"]
        if half is None:
            warns.append((t["time"], f"{inn}회 초/말이 비어 있음"))
            continue
        if name in by_half[(inn, half)]:
            continue
        where = f"{inn}회{HALF_KO[half]}"
        if name in pitchers and name not in all_batters:
            why = "투수 이름으로 보임"
        elif name in all_batters:
            others = [f"{i}회{HALF_KO[h]}" for (i, h), names in sorted(by_half.items()) if name in names]
            why = f"이 이닝 타자가 아님 (실제로는 {', '.join(others)}에 타석)"
        else:
            similar = [b for b in all_batters if len(b) == len(name) and sum(a != c for a, c in zip(b, name)) == 1]
            why = "경기 기록에 없는 이름" + (f" (혹시 {similar[0]}?)" if similar else "")
        warns.append((t["time"], f"{where} '{name}' → {why}. 이 이닝 타자: {', '.join(sorted(by_half[(inn, half)]))}"))
    return warns


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)

    totals = {name: [] for name, _, _ in METHODS}
    per_game = []
    all_warns = []

    for a in args:
        gid, _, rpath = a.partition("=")
        rpath = rpath or f"readings_{gid}.json"
        gpath = os.path.join(GAMES_DIR, f"{gid}.json")
        tpath = os.path.join(HERE, "eval", f"정답표_{gid}.csv")
        for p in (gpath, rpath, tpath):
            if not os.path.exists(p):
                sys.exit(f"파일 없음: {p}")

        rows = json.load(open(gpath, encoding="utf-8"))["rows"]
        pas = match.build_plate_appearances(rows)
        readings = json.load(open(rpath, encoding="utf-8"))
        truth = score.load_truth(tpath)

        for t, msg in check_truth(truth, pas, rows):
            all_warns.append((gid, t, msg))

        row = {"game": gid, "n": len(truth)}
        for name, mode, carry in METHODS:
            g = score.grade(truth, score.predict(readings, pas, mode, carry))
            totals[name].extend(g)
            row[name] = g
        per_game.append(row)

    # 1) 정답표 검사
    print("=" * 60)
    if all_warns:
        print(f"⚠️  정답표 확인 필요 {len(all_warns)}개 (고친 뒤 다시 돌리는 걸 추천)")
        for gid, t, msg in all_warns:
            print(f"  {gid}  {int(t)//60}:{int(t)%60:02d}  {msg}")
    else:
        print("정답표 검사: 문제 없음")

    # 2) 채점
    def stats(g):
        has = [x for x in g if x["truth"] is not None]
        hit = sum(1 for x in has if x["grade"] == "맞음")
        linked = [x for x in g if x["pred"] is not None]
        lhit = sum(1 for x in linked if x["grade"] == "맞음")
        wrong = sum(1 for x in g if x["grade"].startswith("틀림"))
        return hit, len(has), lhit, len(linked), wrong

    def pct(a, b):
        return f"{a/b:.0%}" if b else "-"

    lines = ["# 하이라이트 연결 평가 결과 (v2 프롬프트)", "",
             f"평가 경기 {len(per_game)}개, 정답 장면 {sum(r['n'] for r in per_game)}개", ""]

    lines += ["## 전체", "", "| 방식 | 맞게 찾은 비율 | 확정한 것 중 맞은 비율 | 틀린 연결 |", "|---|---|---|---|"]
    for name, _, _ in METHODS:
        h, n, lh, ln, w = stats(totals[name])
        lines.append(f"| {name} | {pct(h, n)} ({h}/{n}) | {pct(lh, ln)} ({lh}/{ln}) | {w}개 |")

    lines += ["", "## 경기별 (기록 대조 기준)", "",
              "| 경기 | 장면 | 맞게 찾은 비율 | 확정한 것 중 맞은 비율 | 틀린 연결 |", "|---|---|---|---|---|"]
    for r in per_game:
        h, n, lh, ln, w = stats(r["기록 대조"])
        lines.append(f"| {r['game']} | {r['n']} | {pct(h, n)} ({h}/{n}) | {pct(lh, ln)} ({lh}/{ln}) | {w}개 |")

    lines += ["", "## 장면 종류별 (기록 대조, 전체)", "", "| 종류 | 장면 | 결과 |", "|---|---|---|"]
    for kind in ("전광판 있음", "타자 줄 없음", "전광판 없음", "타석 없음"):
        sub = [x for x in totals["기록 대조"] if x["kind"] == kind]
        if sub:
            c = Counter(x["grade"] for x in sub)
            lines.append(f"| {kind} | {len(sub)} | " + ", ".join(f"{k} {v}" for k, v in c.most_common()) + " |")

    wrong = [(r["game"], x) for r in per_game for x in r["기록 대조"] if x["grade"].startswith("틀림")]
    if wrong:
        lines += ["", "## 틀린 연결 (기록 대조)", "", "| 경기 | 영상 시간 | 정답 | 시스템 |", "|---|---|---|---|"]
        for gid, x in wrong:
            t = x["truth"]
            p = x["pred"]
            tt = "확인 불가" if t is None else f"{t[0]}회{HALF_KO.get(t[1], '?')} {t[2]}"
            pp = f"{p[0]}회{HALF_KO[p[1]]} {p[2]}"
            lines.append(f"| {gid} | {int(x['time'])//60}:{int(x['time'])%60:02d} | {tt} | {pp} |")

    report = "\n".join(lines)
    print("=" * 60)
    print(report)
    open(os.path.join(HERE, "score_all_report.md"), "w", encoding="utf-8").write(report + "\n")
    print("\n저장: score_all_report.md")


if __name__ == "__main__":
    main()