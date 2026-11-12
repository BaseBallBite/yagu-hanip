"""
매칭 결과 → 장면 표 (백엔드·프론트에 넘길 파일)

5초마다 나온 전광판 읽기 결과를 "몇 초~몇 초는 이 타석" 구간으로 묶음.

사용법
  python scene_table.py <경기상태.json> <readings.json> --video-id _zk2lD3nCDM \
      --out scenes_20260328HTSK02026.json [--every 5] [--carry 10]

출력 형식
{
  "game_id": "20260328HTSK02026",
  "video_id": "_zk2lD3nCDM",
  "away": "KIA", "home": "SSG",
  "scenes": [
    {"start": 55, "end": 60, "status": "확정", "confidence": "높음",
     "inning": 1, "half": "초", "batter": "김호령",
     "situation": {"outs": 0, "bases": [false,false,false], "score_away": 0, "score_home": 0},
     "restore": ["1회초, 0사, 점수 원정 0 : 홈 0", ...]},
    {"start": 120, "end": 130, "status": "확인 불가"},
    {"start": 60, "end": 70, "status": "추정", ...}   # --carry 를 줬을 때만
  ]
}

status
  확정      : 전광판으로 타석을 찾음
  추정      : 전광판은 없지만 바로 앞 확정 장면과 이어진 것으로 봄 (--carry 를 줄 때만 생김)
  확인 불가 : 연결하지 못함 → 프론트는 상황 카드를 띄우지 않음
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import match  # noqa: E402

HALF_KO = {"top": "초", "bottom": "말"}
CONF_RANK = {"높음": 3, "보통": 2, "낮음": 1}


def frame_labels(readings, pas):
    """프레임마다 (시간, pa_id 또는 None, 신뢰도)"""
    out = []
    for rd in sorted(readings, key=lambda r: r["time_sec"]):
        res = match.match_scene(rd, pas)
        if res["status"] == "확정":
            out.append((float(rd["time_sec"]), res["pa_id"], res.get("confidence", "보통")))
        else:
            out.append((float(rd["time_sec"]), None, None))
    return out


def group(labels, every):
    """같은 타석이 연속되는 프레임을 하나의 구간으로 묶음."""
    segs = []
    for t, pa, conf in labels:
        if segs and segs[-1]["pa_id"] == pa and abs(segs[-1]["end"] - t) < every * 1.5:
            seg = segs[-1]
            seg["end"] = t + every
            if conf:
                seg["confs"].append(conf)
        else:
            segs.append({"start": t, "end": t + every, "pa_id": pa, "confs": [conf] if conf else []})
    return segs


def apply_carry(segs, carry):
    """확인 불가 구간이 바로 앞 확정 구간에 이어지고 carry 초 이하면 '추정'으로 바꿈."""
    if carry <= 0:
        return segs
    for i, seg in enumerate(segs):
        if seg["pa_id"] is not None or i == 0:
            continue
        prev = segs[i - 1]
        if prev["pa_id"] is not None and prev.get("status") != "추정" and seg["end"] - seg["start"] <= carry:
            seg["pa_id"] = prev["pa_id"]
            seg["status"] = "추정"
    return segs


def build(game_path, readings_path, video_id, every=5, carry=0):
    game = json.load(open(game_path, encoding="utf-8"))
    rows = game["rows"]
    pas = match.build_plate_appearances(rows)
    readings = json.load(open(readings_path, encoding="utf-8"))

    segs = apply_carry(group(frame_labels(readings, pas), every), carry)

    scenes, max_pa = [], -1
    for seg in segs:
        pa_id = seg["pa_id"]
        if pa_id is None:
            scenes.append({"start": seg["start"], "end": seg["end"], "status": "확인 불가"})
            continue
        pa = pas[pa_id]
        st = rows[pa["start_row"]]["state_before"]
        status = seg.get("status", "확정")
        if status == "추정":
            conf = "추정"
        else:
            # 구간 안에서 가장 높은 신뢰도를 대표로 씀
            conf = max(seg["confs"], key=lambda c: CONF_RANK.get(c, 0)) if seg["confs"] else "보통"
        scene = {
            "start": seg["start"], "end": seg["end"], "status": status, "confidence": conf,
            "inning": pa["inning"], "half": HALF_KO[pa["half"]], "batter": pa["batter"],
            "situation": {"outs": st["outs"], "bases": match.bases_of(st),
                          "score_away": st["score"]["away"], "score_home": st["score"]["home"]},
            "restore": match.restore(pa, rows),
        }
        # 하이라이트는 경기 순서대로 편집되므로, 앞 장면보다 이전 타석이면 의심 표시
        if pa_id < max_pa:
            scene["order_warning"] = True
        max_pa = max(max_pa, pa_id)
        scenes.append(scene)

    summ = game.get("summary", {})
    return {"game_id": summ.get("game_id"), "video_id": video_id,
            "away": summ.get("away"), "home": summ.get("home"),
            "frame_interval_sec": every, "carry_sec": carry, "scenes": scenes}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("game")
    ap.add_argument("readings")
    ap.add_argument("--video-id", required=True, help="유튜브 영상 ID (주소 끝부분)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--every", type=float, default=5)
    ap.add_argument("--carry", type=float, default=0, help="추정 처리할 최대 길이(초). 0이면 안 씀")
    args = ap.parse_args()

    table = build(args.game, args.readings, args.video_id, args.every, args.carry)
    out = args.out or f'scenes_{table["game_id"]}.json'
    json.dump(table, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    sc = table["scenes"]
    from collections import Counter
    c = Counter(s["status"] for s in sc)
    print(f"장면 {len(sc)}개: " + ", ".join(f"{k} {v}" for k, v in c.items()))
    warn = [s for s in sc if s.get("order_warning")]
    if warn:
        print(f"순서 역행 의심 {len(warn)}개: " + ", ".join(f'{int(s["start"])}s {s["batter"]}' for s in warn))
    print(f"저장: {out}")


if __name__ == "__main__":
    main()
