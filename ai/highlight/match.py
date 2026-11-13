"""
하이라이트 장면 ↔ 문자중계 매칭 + 앞 흐름 복원 (기능 B)

입력
  1) b2-state-v1 형식의 경기 상태 파일 (rows: state_before / state_after 포함)
  2) 전광판 읽기 결과 (Gemini 출력, 못 읽은 칸은 null)

출력
  status: "확정" | "확인 불가"
  match:  매칭된 타석 정보
  restore: 그 장면 직전까지의 흐름 (해설 코드에 F로 넘길 사실 목록)

사용법
  python match.py <경기상태.json> <전광판읽기.json>
  전광판읽기.json 은 dict 하나 또는 dict 리스트
"""
import json
import re
import sys

PLAY_SKIP = {"pitch", "batter_announcement", "inning_start", "substitution",
             "pitcher_disengagement", "mound_visit", "video_review"}
PITCH_BALL = {"볼"}
PITCH_STRIKE = {"스트라이크", "헛스윙"}
PITCH_FOUL = {"파울", "번트파울"}

HALF_KO = {"top": "초", "bottom": "말"}
BASE_KO = {"1": "1루", "2": "2루", "3": "3루"}


# ---------------------------------------------------------------- 타임라인 정리

def is_settled(state):
    """한 베이스에 주자가 2명 잡혀 있는 중간 상태(base_shared_temporarily)는 매칭에서 뺌."""
    return all(c <= 1 for c in state["runner_count"].values())


def bases_of(state):
    return [state["runner_count"][b] > 0 for b in ("1", "2", "3")]


def build_plate_appearances(rows):
    """타석 단위로 묶고, 타석 안의 '전광판에 보일 수 있는 순간'을 모두 뽑음."""
    pas, cur = [], None
    origin, batter_result = {}, {}   # 주자 이름 -> 출루 기록
    half_key = None

    for i, r in enumerate(rows):
        key = (r["inning"], r["inning_half"])
        if key != half_key:
            origin, batter_result, half_key = {}, {}, key

        et, desc = r["event_type"], r["description"]
        sb, sa = r["state_before"], r["state_after"]

        if et == "batter_announcement":
            batter = re.sub(r"^(\d+번타자|대타)\s*", "", desc).strip()
            cur = {"pa_id": len(pas), "inning": r["inning"], "half": r["inning_half"],
                   "batter": batter, "start_row": i, "rows": [], "moments": [],
                   "balls": 0, "strikes": 0,
                   "origin_at_start": dict(origin), "naver_ok": r["naver_match"]}
            pas.append(cur)

        if cur is not None and key == (cur["inning"], cur["half"]):
            cur["rows"].append(i)
            if et == "pitch" or et not in PLAY_SKIP:
                if is_settled(sb):
                    cur["moments"].append({"row": i, "side": "before", "state": sb,
                                           "balls": cur["balls"], "strikes": cur["strikes"]})
            if et == "pitch":
                kind = re.sub(r"^\d+구\s*", "", desc)
                if kind in PITCH_BALL:
                    cur["balls"] = min(cur["balls"] + 1, 3)
                elif kind in PITCH_STRIKE:
                    cur["strikes"] = min(cur["strikes"] + 1, 2)
                elif kind in PITCH_FOUL:
                    cur["strikes"] = min(cur["strikes"] + 1, 2)

        # 출루 이력 추적 (대주자는 원래 주자의 출루 이력을 이어받음)
        m = re.match(r"^\d루주자\s*(\S+)\s*:\s*대주자\s*(\S+)", desc)
        if et == "substitution" and m:
            old, new = m.group(1), m.group(2)
            if old in origin:
                origin[new] = {**origin[old], "pinch_for": old}
        # 타자 본인 결과("최정 : 볼넷")를 기억해둠. 한 베이스 겹침 때문에 이름이
        # 베이스에 늦게 나타나도, 출루 이유는 이 기록으로 붙임
        mb = re.match(r"^(\S+)\s*:", desc)
        if et not in PLAY_SKIP and mb and not re.match(r"^\d루주자", desc):
            batter_result[mb.group(1)] = {"row": i, "desc": desc}
        before_names = {v for v in sb["runners"].values() if v}
        for b, name in sa["runners"].items():
            if name and name not in before_names and name not in origin:
                origin[name] = batter_result.get(name, {"row": i, "desc": desc})

    # 타석이 끝난 직후 상태는 보통 다음 타석 시작 상태와 같음 → 다음 타석으로 합침.
    # 이닝 마지막 타석(3아웃, 끝내기)만 '직후' 순간을 따로 추가함
    for k, pa in enumerate(pas):
        nxt = pas[k + 1] if k + 1 < len(pas) else None
        if nxt and (nxt["inning"], nxt["half"]) == (pa["inning"], pa["half"]):
            continue
        last = rows[pa["rows"][-1]]
        if is_settled(last["state_after"]):
            pa["moments"].append({"row": pa["rows"][-1], "side": "after",
                                  "state": last["state_after"], "balls": None, "strikes": None})
    return pas


# ---------------------------------------------------------------- 매칭

def moment_matches(reading, pa, mom):
    """전광판에서 읽은 칸 중 null이 아닌 것만 비교. 하나라도 다르면 탈락."""
    st = mom["state"]
    checks = [
        ("inning", pa["inning"]),
        ("half", pa["half"]),
        ("outs", st["outs"]),
        ("score_away", st["score"]["away"]),
        ("score_home", st["score"]["home"]),
    ]
    for field, truth in checks:
        v = reading.get(field)
        if v is not None and v != truth:
            return False
    if reading.get("bases") is not None and [bool(x) for x in reading["bases"]] != bases_of(st):
        return False
    for field in ("balls", "strikes"):
        v = reading.get(field)
        if v is not None and mom[field] is not None and v != mom[field]:
            return False
    return True


def soft_score(reading, mom):
    """아웃·주자·카운트는 Gemini가 자주 틀리게 읽음 → 탈락시키지 않고 점수로만 반영."""
    st, s = mom["state"], 0
    if reading.get("outs") is not None:
        s += 2 if reading["outs"] == st["outs"] else -3
    if reading.get("bases") is not None:
        diff = sum(bool(a) != b for a, b in zip(reading["bases"], bases_of(st)))
        s += 2 if diff == 0 else -diff
    for f in ("balls", "strikes"):
        if reading.get(f) is not None and mom[f] is not None:
            s += 1 if reading[f] == mom[f] else 0
    return s


def match_scene(reading, pas, mode="soft"):
    """
    mode="strict": 읽은 칸이 하나라도 기록과 다르면 탈락 (Gemini 결과를 그대로 믿는 방식)
    mode="soft"  : 이닝·초말·점수·타자 이름만 꼭 맞아야 하고, 아웃·주자는 점수로 비교
    """
    # 최소 단서: 이닝 + 초/말 + 점수 둘 다. 없으면 후보가 너무 많아서 바로 확인 불가
    need = ["inning", "half", "score_away", "score_home"]
    missing = [f for f in need if reading.get(f) is None]
    if missing:
        return {"status": "확인 불가", "reason": f"필수 단서 못 읽음: {missing}", "candidates": []}
    if mode == "soft":
        return _match_soft(reading, pas)

    hits = {}
    for pa in pas:
        for mom in pa["moments"]:
            if moment_matches(reading, pa, mom):
                hits.setdefault(pa["pa_id"], []).append(mom)

    cand = list(hits)
    # 타자 이름으로 좁히기
    if len(cand) > 1 and reading.get("batter"):
        named = [p for p in cand if pas[p]["batter"] == reading["batter"]]
        if named:
            cand = named

    if len(cand) == 1:
        pa = pas[cand[0]]
        return {"status": "확정", "pa_id": pa["pa_id"], "matched_side": sorted({m["side"] for m in hits[pa["pa_id"]]}),
                "reason": "조건에 맞는 타석이 하나뿐임", "candidates": cand}
    if not cand:
        return {"status": "확인 불가", "reason": "기록에 이런 상황이 없음 (전광판 오인식 가능성)", "candidates": []}
    return {"status": "확인 불가", "reason": f"후보 타석 {len(cand)}개라 하나로 못 좁힘", "candidates": cand}


def _match_soft(reading, pas):
    # 1) 꼭 맞아야 하는 것: 이닝, 초/말, 점수(그 순간의 점수), 타자 이름(읽었으면)
    best = {}
    for pa in pas:
        if (pa["inning"], pa["half"]) != (reading["inning"], reading["half"]):
            continue
        if reading.get("batter") and pa["batter"] != reading["batter"]:
            continue
        for mom in pa["moments"]:
            sc = mom["state"]["score"]
            if (sc["away"], sc["home"]) != (reading["score_away"], reading["score_home"]):
                continue
            s = soft_score(reading, mom)
            if pa["pa_id"] not in best or s > best[pa["pa_id"]]:
                best[pa["pa_id"]] = s

    if not best:
        return {"status": "확인 불가", "reason": "이닝·점수·타자가 맞는 타석이 없음 (전광판 오인식 가능성)",
                "candidates": []}

    ranked = sorted(best.items(), key=lambda x: -x[1])
    top_id, top_s = ranked[0]
    cand = [p for p, _ in ranked]

    # 2) 후보가 하나뿐이면 확정. 아웃·주자가 기록과 많이 다르면 신뢰도 '낮음'으로 표시
    if len(ranked) == 1:
        conf = "높음" if top_s > 0 else ("보통" if top_s == 0 else "낮음")
        why = "이닝·점수" + ("·타자" if reading.get("batter") else "") + "로 타석 하나로 좁혀짐"
        if conf == "낮음":
            why += " (단, 전광판 아웃/주자가 기록과 다름 → 사람 확인 권장)"
        return {"status": "확정", "pa_id": top_id, "confidence": conf, "reason": why, "candidates": cand}

    # 3) 후보가 여러 개면 아웃·주자 점수가 확실히 앞서는 타석만 확정
    margin = top_s - ranked[1][1]
    if margin >= 2 and top_s >= 2:
        return {"status": "확정", "pa_id": top_id, "confidence": "보통",
                "reason": f"후보 {len(ranked)}개 중 아웃·주자가 가장 잘 맞음 (점수 차 {margin})", "candidates": [top_id]}
    return {"status": "확인 불가", "reason": f"후보 타석 {len(ranked)}개가 비슷해서 못 좁힘", "candidates": cand}


def order_filter(labels, pas):
    """
    순서 규칙: 하이라이트는 경기 순서대로 편집되므로, 같은 반이닝 안에서
    바로 앞에 확정한 타석보다 '이전' 타석이 나오면 확정하지 않음 (None 으로 바꿈).
    labels: 시간순 [(time, pa_id 또는 None, ...), ...]
    """
    out, last = [], None
    for item in labels:
        t, pa_id = item[0], item[1]
        if pa_id is not None and last is not None:
            same_half = (pas[pa_id]["inning"], pas[pa_id]["half"]) == (pas[last]["inning"], pas[last]["half"])
            if same_half and pa_id < last:
                out.append((t, None) + tuple(item[2:]))
                continue
        if pa_id is not None:
            last = pa_id
        out.append(item)
    return out


# ---------------------------------------------------------------- 복원

def _clean(desc):
    desc = re.sub(r"\s*\([^)]*\)", "", desc)          # (우익수->포수) 같은 괄호 설명 제거
    return re.sub(r"\s+", " ", desc).strip()


def short_result(pa, rows):
    """타석 결과를 한 줄로: '김민석 : 우익수 앞 1루타 → 세베리노·안재석 홈인 (1:3 → 3:3)'"""
    plays = [rows[i] for i in pa["rows"] if rows[i]["event_type"] not in PLAY_SKIP | {"pitch"}]
    if not plays:
        return None
    main = next((r for r in plays if r["description"].startswith(pa["batter"])), None)
    if main is None:   # 타자 결과가 없는 타석 (폭투·도루 등) → 득점 기록이 있으면 그걸 대표로
        main = next((r for r in plays if r["event_type"] == "run_scored"), plays[0])
    text = _clean(main["description"])
    scored = []
    for r in plays:
        if r["event_type"] == "run_scored" and r is not main:
            m = re.match(r"^\d루주자\s*(\S+)", r["description"])
            if m:
                scored.append(m.group(1))
    if scored:
        text += " → " + "·".join(scored) + " 홈인"
    # 실책 정보는 괄호 안에 있어서 지워지므로 따로 살림: "(3루수 송구 실책->1루수)" → "3루수 송구 실책"
    errs = []
    for r in plays:
        for m in re.finditer(r"\(([^)]*실책[^)]*)\)", r["description"]):
            e = m.group(1).split("->")[0].strip()
            if e not in errs:
                errs.append(e)
    if errs:
        text += " [" + ", ".join(errs) + "]"
    b = rows[pa["rows"][0]]["state_before"]["score"]
    a = rows[pa["rows"][-1]]["state_after"]["score"]
    if (b["away"], b["home"]) != (a["away"], a["home"]):
        text += f' ({b["away"]}:{b["home"]} → {a["away"]}:{a["home"]})'
    return text


def prev_pa(pa, pas, rows):
    """같은 반이닝에서 바로 앞 타석 (플레이가 있었던 것만)"""
    for k in range(pa["pa_id"] - 1, -1, -1):
        q = pas[k]
        if (q["inning"], q["half"]) != (pa["inning"], pa["half"]):
            return None
        if short_result(q, rows):
            return q
    return None


def restore(pa, rows):
    start = rows[pa["start_row"]]["state_before"]
    half = f'{pa["inning"]}회{HALF_KO[pa["half"]]}'
    facts = []

    sc = start["score"]
    facts.append(f'{half}, {start["outs"]}사, 점수 원정 {sc["away"]} : 홈 {sc["home"]}')

    on_base = [(b, n) for b, n in start["runners"].items() if n]
    if on_base:
        for b, name in on_base:
            o = pa["origin_at_start"].get(name)
            how = o["desc"] if o else "출루 기록 없음"
            extra = f' (대주자, 원래 주자 {o["pinch_for"]})' if o and o.get("pinch_for") else ""
            facts.append(f'{BASE_KO[b]} 주자 {name}{extra} ← {how}')
    else:
        facts.append("주자 없음")

    # 이번 이닝에 이 타석 전까지 난 점수
    runs_before = [r["description"] for r in rows[:pa["start_row"]]
                   if r["inning"] == pa["inning"] and r["inning_half"] == pa["half"]
                   and r["event_type"] == "run_scored"]
    if runs_before:
        facts.append("이번 이닝 앞선 득점: " + " / ".join(runs_before))

    facts.append(f'타자: {pa["batter"]}')
    result = [rows[i]["description"] for i in pa["rows"] if rows[i]["event_type"] not in PLAY_SKIP | {"pitch"}]
    facts.append("이 타석 결과: " + (" / ".join(result) if result else "기록 없음"))

    end = rows[pa["rows"][-1]]["state_after"]
    es = end["score"]
    facts.append(f'타석 후: {end["outs"]}사, 점수 원정 {es["away"]} : 홈 {es["home"]}')
    return facts


# ---------------------------------------------------------------- 실행

def run(game_path, readings):
    game = json.load(open(game_path, encoding="utf-8"))
    rows = game["rows"]
    pas = build_plate_appearances(rows)
    out = []
    for rd in readings:
        res = match_scene(rd, pas)
        if res["status"] == "확정":
            res["restore"] = restore(pas[res["pa_id"]], rows)
        res["candidates"] = [
            {"pa_id": p, "inning": pas[p]["inning"], "half": pas[p]["half"], "batter": pas[p]["batter"]}
            for p in res["candidates"]]
        out.append({"reading": rd, **res})
    return out


if __name__ == "__main__":
    game_path, reading_path = sys.argv[1], sys.argv[2]
    readings = json.load(open(reading_path, encoding="utf-8"))
    if isinstance(readings, dict):
        readings = [readings]
    print(json.dumps(run(game_path, readings), ensure_ascii=False, indent=2))