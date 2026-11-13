"""
하이라이트 연결 채점: 사람 정답표 vs 시스템 매칭 결과

사용법
  python score.py <경기상태.json> <readings.json> <정답표.csv> [--carry 10]

정답표.csv 열: 영상시간, time_sec, 정답_회, 정답_초말, 정답_타자, 비고
  - 정답_타자가 비어 있으면 '확인 불가'가 정답
  - 비고에 '전광판 없음' → 전광판 없는 장면, '타자 줄 없음' → 전광판 일부만 있는 장면

비교하는 방식
  strict : Gemini가 읽은 값을 그대로 믿음 (하나라도 다르면 탈락)
  soft   : 기록과 대조 (이닝·점수·타자만 필수, 아웃·주자는 점수로 비교)
  soft+이어받기 : soft 결과가 확인 불가면, 앞쪽 N초 안에 확정된 장면 결과를 이어받음
"""
import argparse
import csv
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import match  # noqa: E402

HALF = {"초": "top", "말": "bottom"}


def load_truth(path):
    rows = []
    for r in csv.DictReader(open(path, encoding="utf-8-sig")):
        note = r.get("비고", "") or ""
        batter = (r.get("정답_타자") or "").strip()
        kind = "전광판 없음" if "전광판 없음" in note else ("타자 줄 없음" if "타자 줄 없음" in note else "전광판 있음")
        if not batter or batter in ("확인 불가", "없음"):
            kind = "타석 없음"
        rows.append({
            "time": float(r["time_sec"]),
            "truth": None if not batter or batter in ("확인 불가", "없음") else
                     (int(r["정답_회"]), HALF.get(r["정답_초말"].strip()), batter),
            "kind": kind, "note": note,
        })
    return rows


def predict(readings, pas, mode, carry=0, order=False):
    labels = []
    for rd in sorted(readings, key=lambda r: r["time_sec"]):
        res = match.match_scene(rd, pas, mode)
        labels.append((float(rd["time_sec"]), res["pa_id"] if res["status"] == "확정" else None))
    if order:
        labels = match.order_filter(labels, pas)
    out, last = {}, None
    for t, pa_id in labels:
        if pa_id is not None:
            p = pas[pa_id]
            pred = (p["inning"], p["half"], p["batter"])
            last = (t, pred)
        elif carry and last and t - last[0] <= carry:
            pred = last[1]
        else:
            pred = None
        out[t] = pred
    return out


def grade(truth_rows, pred):
    res = []
    for r in truth_rows:
        p = pred.get(r["time"])
        t = r["truth"]
        if t is None:
            g = "맞음(확인 불가)" if p is None else "틀림(억지 연결)"
        elif p is None:
            g = "미연결"
        elif p == t:
            g = "맞음"
        else:
            g = "틀림(오연결)"
        res.append({**r, "pred": p, "grade": g})
    return res


def summarize(name, graded):
    n = len(graded)
    linked = [g for g in graded if g["pred"] is not None]
    correct = [g for g in graded if g["grade"].startswith("맞음")]
    wrong = [g for g in graded if g["grade"].startswith("틀림")]
    has_truth = [g for g in graded if g["truth"] is not None]
    hit = [g for g in has_truth if g["grade"] == "맞음"]
    prec = sum(1 for g in linked if g["grade"] == "맞음") / len(linked) if linked else 0
    print(f"\n[{name}]")
    print(f"  전체 정답률      {len(correct)}/{n} = {len(correct)/n:.0%}")
    print(f"  연결 재현율      {len(hit)}/{len(has_truth)} = {len(hit)/len(has_truth):.0%}  (정답 타석이 있는 장면 중 맞게 찾은 비율)")
    print(f"  연결 정밀도      {sum(1 for g in linked if g['grade']=='맞음')}/{len(linked)} = {prec:.0%}  (확정한 것 중 맞은 비율)")
    print(f"  틀린 연결        {len(wrong)}개")
    for kind in ("전광판 있음", "타자 줄 없음", "전광판 없음", "타석 없음"):
        sub = [g for g in graded if g["kind"] == kind]
        if sub:
            c = Counter(g["grade"] for g in sub)
            print(f"   - {kind:<6} {len(sub):>2}장: " + ", ".join(f"{k} {v}" for k, v in c.most_common()))
    return {"name": name, "n": n, "correct": len(correct), "recall": len(hit) / len(has_truth),
            "precision": prec, "wrong": len(wrong)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("game")
    ap.add_argument("readings")
    ap.add_argument("truth")
    ap.add_argument("--carry", type=float, default=10, help="이어받기 허용 시간(초)")
    args = ap.parse_args()

    rows = json.load(open(args.game, encoding="utf-8"))["rows"]
    pas = match.build_plate_appearances(rows)
    readings = json.load(open(args.readings, encoding="utf-8"))
    truth = load_truth(args.truth)

    runs = {
        "그대로 믿기 (strict)": predict(readings, pas, "strict"),
        "기록 대조 (soft)": predict(readings, pas, "soft"),
        f"기록 대조 + {int(args.carry)}초 이어받기": predict(readings, pas, "soft", args.carry),
    }
    graded_all = {}
    for name, pred in runs.items():
        graded_all[name] = grade(truth, pred)
        summarize(name, graded_all[name])

    # 장면별 상세 (soft 기준)
    out = []
    for i, r in enumerate(truth):
        row = {"time_sec": r["time"], "구분": r["kind"],
               "정답": "확인 불가" if r["truth"] is None else f'{r["truth"][0]}회{"초" if r["truth"][1]=="top" else "말"} {r["truth"][2]}'}
        for name, g in graded_all.items():
            p = g[i]["pred"]
            row[name] = ("확인 불가" if p is None else f'{p[0]}회{"초" if p[1]=="top" else "말"} {p[2]}') + f' [{g[i]["grade"]}]'
        out.append(row)
    path = "score_detail.csv"
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"\n장면별 상세: {path}")


if __name__ == "__main__":
    main()