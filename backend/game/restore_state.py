"""B2 주자·아웃·점수 복원 v1.

B1이 정리한 문자중계(선택된 행 순서)를 한 줄씩 따라가며
각 행의 직전/직후 상태(아웃 수, 1·2·3루 주자, 점수)를 계산한다.

- 입력 원본은 수정하지 않는다. 결과는 --out 폴더에 따로 저장한다.
- 네이버 원본의 currentGameState(행 직후 상태)와 행마다 대조해 차이를 기록한다.
- 경기 끝 계산 점수를 경기 메타데이터의 최종 점수와 비교한다.

사용 예:
    .venv/bin/python backend/game/restore_state.py \
        --data data/raw/b1/kbo_2026_b1_handoff_v1/kbo_2026_b1_handoff_v1/data \
        --out data/raw/b2_state_v1 --limit 50
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

VERSION = "b2-state-v1"

# 타자가 아웃되는 결과
BATTER_OUT_TYPES = {
    "flyout", "groundout", "lineout", "strikeout", "sacrifice_fly",
    "sacrifice_bunt", "double_play", "batted_ball_out", "dropped_third_strike",
    "bunt_out", "triple_play",
}
# 타자가 출루하는 결과와 도착 루
BATTER_REACH_TYPES = {
    "single": 1, "double": 2, "triple": 3, "home_run": 4,
    "walk": 1, "intentional_walk": 1, "hit_by_pitch": 1,
    "reach_unspecified": 1, "reached_on_error": 1, "fielders_choice": 1,
}
RUNNER_OUT_TYPES = {"runner_out", "caught_stealing", "pickoff_out"}

RUNNER_RE = re.compile(r"^\s*([123])루주자\s*([^:]+?)\s*:\s*(.*)$")
BATTER_RUNNER_RE = re.compile(r"^\s*타자주자\s*([^:]+?)\s*:\s*(.*)$")
BATTER_RE = re.compile(r"^\s*([^:]+?)\s*:\s*(.*)$")
DEST_RE = re.compile(r"([123])루까지")


class State:
    def __init__(self) -> None:
        self.outs = 0
        self.bases: dict[int, list[str]] = {1: [], 2: [], 3: []}
        self.score = {"away": 0, "home": 0}

    def snapshot(self) -> dict:
        return {
            "outs": self.outs,
            "runners": {str(b): (self.bases[b][0] if self.bases[b] else None) for b in (1, 2, 3)},
            "runner_count": {str(b): len(self.bases[b]) for b in (1, 2, 3)},
            "score": dict(self.score),
        }

    def occupied(self) -> tuple[bool, bool, bool]:
        return tuple(bool(self.bases[b]) for b in (1, 2, 3))

    def remove_runner(self, base: int, name: str | None) -> str | None:
        occ = self.bases[base]
        if not occ:
            return None
        if name and name in occ:
            occ.remove(name)
            return name
        return occ.pop(0)

    def find_runner(self, name: str) -> int | None:
        for b in (1, 2, 3):
            if name in self.bases[b]:
                return b
        return None


def batting_side(play: dict) -> str:
    return "away" if play.get("inning_half") == "top" else "home"


def apply_play(st: State, play: dict, notes: list[str]) -> None:
    et = play["event_type"]
    desc = play.get("description") or ""
    side = batting_side(play)

    if et == "inning_start":
        st.outs = 0
        st.bases = {1: [], 2: [], 3: []}
        return

    m = RUNNER_RE.match(desc)
    bm = BATTER_RUNNER_RE.match(desc) if not m else None
    if m or bm:
        if m:
            base, name, rest = int(m.group(1)), m.group(2), m.group(3)
        else:
            name, rest = bm.group(1), bm.group(2)
            base = st.find_runner(name)
            if base is None:
                notes.append("batter_runner_not_found")
                return
        if et == "substitution":  # 대주자 교체: 자리만 이름 바꿈
            nm = re.search(r"대주자\s*(\S+)", rest)
            if nm and st.bases[base]:
                occ = st.bases[base]
                idx = occ.index(name) if name in occ else 0
                occ[idx] = nm.group(1)
            return
        if base is None or not st.bases[base]:
            notes.append(f"runner_missing_on_{base}")
        # 판단 순서: 홈인 → "N루까지"(진루) → 아웃. "진루실패아웃"처럼
        # '진루'가 들어간 아웃 문장이 있어 '진루' 단어만으로 판단하지 않는다.
        d = DEST_RE.search(rest)
        if "홈인" in rest:
            st.remove_runner(base, name)
            st.score[side] += 1
        elif d:
            who = st.remove_runner(base, name) or name
            st.bases[int(d.group(1))].append(who)
        elif "아웃" in rest:
            st.remove_runner(base, name)
            st.outs += 1
        else:
            notes.append("runner_text_unparsed")
        return

    if et in RUNNER_OUT_TYPES:
        notes.append("runner_out_without_base")
        st.outs += 1
        return

    bmatch = BATTER_RE.match(desc)
    batter = bmatch.group(1) if bmatch else (play.get("batter") or "?")
    rest = bmatch.group(2) if bmatch else desc

    if et in BATTER_REACH_TYPES:
        dest = BATTER_REACH_TYPES[et]
        if dest == 4:
            st.score[side] += 1
        else:
            st.bases[dest].append(batter)
        return

    if et in BATTER_OUT_TYPES:
        # "희생플라이 (중견수 실책)"처럼 아웃 유형인데 '아웃' 없이 실책으로 산 경우도 출루.
        reached = ("출루" in rest) or ("아웃" not in rest) or (
            et == "dropped_third_strike" and ("포일" in rest or "폭투" in rest)
        )
        if reached:
            st.bases[1].append(batter)
        else:
            st.outs += 1
        return
    # 그 밖(교체, 안내, 투구, 판독 등)은 상태를 바꾸지 않는다.


def naver_state(play: dict) -> dict | None:
    raw = (play.get("source_record") or {}).get("raw") or {}
    gs = raw.get("currentGameState")
    if not gs:
        return None
    try:
        return {
            "outs": int(gs["out"]),
            "occupied": tuple(str(gs[f"base{b}"]) not in ("0", "", "None") for b in (1, 2, 3)),
            "score": {"away": int(gs["awayScore"]), "home": int(gs["homeScore"])},
        }
    except (KeyError, ValueError, TypeError):
        return None


def restore_game(data: Path, game_id: str) -> dict:
    sel = json.loads((data / "b1_selection_v1" / "games" / f"{game_id}.json").read_text(encoding="utf-8"))
    g = json.loads((data / "b1_normalized_v11" / "games" / game_id / "normalized_game.json").read_text(encoding="utf-8"))
    by_id = {p["play_id"]: p for p in g["plays"]}
    meta = g["metadata_raw"]

    st = State()
    rows = []
    mismatch = Counter()
    first_mismatch = None
    half_outs = {}
    for pid in sel["ordered_play_ids"]:
        p = by_id[pid]
        before = st.snapshot()
        notes: list[str] = []
        apply_play(st, p, notes)
        after = st.snapshot()
        key = (p.get("inning"), p.get("inning_half"))
        if p["event_type"] != "inning_start":
            half_outs[key] = st.outs

        check = {}
        nv = naver_state(p)
        # 한 플레이가 여러 줄로 나뉘어 네이버 상태가 중간에 앞서 갈 수 있어,
        # 플레이 사이(다음 타자 등장 줄)에서만 대조한다.
        if nv and p["event_type"] == "batter_announcement":
            check = {
                "outs": nv["outs"] == st.outs or (nv["outs"] == 3 and st.outs >= 3),
                "bases": nv["occupied"] == st.occupied() or st.outs >= 3,
                "score": nv["score"] == st.score,
            }
            for k, ok in check.items():
                if not ok:
                    mismatch[k] += 1
                    if first_mismatch is None:
                        first_mismatch = {
                            "play_id": pid, "inning": p.get("inning"), "half": p.get("inning_half"),
                            "description": p.get("description"), "field": k,
                            "ours": {"outs": st.outs, "occupied": st.occupied(), "score": dict(st.score)},
                            "naver": nv,
                        }
        if any(len(st.bases[b]) > 1 for b in (1, 2, 3)):
            notes.append("base_shared_temporarily")
        rows.append({
            "play_id": pid, "event_type": p["event_type"], "inning": p.get("inning"),
            "inning_half": p.get("inning_half"), "description": p.get("description"),
            "state_before": before, "state_after": after,
            "naver_match": check or None, "notes": notes,
        })

    final_expected = {"away": meta.get("awayTeamScore"), "home": meta.get("homeTeamScore")}
    # 마지막 반이닝(끝내기·경기 종료)은 3아웃이 아니어도 된다.
    halves = list(half_outs.items())
    bad_halves = [f"{k[0]}{k[1]}:{v}" for k, v in halves[:-1] if v != 3]
    return {
        "summary": {
            "game_id": game_id,
            "away": meta.get("awayTeamName"), "home": meta.get("homeTeamName"),
            "final_ours": dict(st.score), "final_expected": final_expected,
            "final_score_match": st.score == final_expected,
            "half_innings": len(halves), "half_innings_not_3_outs": bad_halves,
            "naver_mismatch_rows": dict(mismatch),
            "first_mismatch": first_mismatch,
        },
        "rows": rows,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--game", action="append", help="특정 경기 ID만 (여러 번 가능)")
    args = ap.parse_args()

    games = args.game or sorted(
        f.stem for f in (args.data / "b1_selection_v1" / "games").glob("*.json")
    )[: args.limit]
    (args.out / "games").mkdir(parents=True, exist_ok=True)
    summaries = []
    for gid in games:
        res = restore_game(args.data, gid)
        res["version"] = VERSION
        (args.out / "games" / f"{gid}.json").write_text(
            json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        summaries.append(res["summary"])

    with (args.out / "summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["game_id", "away", "home", "ours_away", "ours_home", "exp_away", "exp_home",
                    "final_score_match", "half_innings_not_3_outs", "mismatch_outs",
                    "mismatch_bases", "mismatch_score", "first_mismatch"])
        for s in summaries:
            fm = s["first_mismatch"]
            w.writerow([s["game_id"], s["away"], s["home"], s["final_ours"]["away"], s["final_ours"]["home"],
                        s["final_expected"]["away"], s["final_expected"]["home"], s["final_score_match"],
                        " ".join(s["half_innings_not_3_outs"]),
                        s["naver_mismatch_rows"].get("outs", 0), s["naver_mismatch_rows"].get("bases", 0),
                        s["naver_mismatch_rows"].get("score", 0),
                        f'{fm["inning"]}{fm["half"]} {fm["field"]}: {fm["description"]}' if fm else ""])
    ok = sum(s["final_score_match"] for s in summaries)
    report = {"version": VERSION, "games": len(summaries), "final_score_match": ok}
    (args.out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
