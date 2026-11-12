"""B3 플레이 사실(F) 생성.

경기 ID + 플레이 순번을 넣으면 해설 AI가 근거로 쓸 F 목록과 플레이 유형 태그를 돌려준다.
F 형식은 ai/explain 의 facts 입력과 같다: [{"id": "F1", "text": "..."}]

원칙
- 기록에 있는 것만 쓴다. 해설처럼 쓰지 않는다.
- 값이 없으면 "기록 없음"이라고 적고 추정하지 않는다.
- 유형 태그는 tools/event_types.txt 에 있는 이름만 쓴다.

플레이 순번: B1 선택 결과(ordered_play_ids) 순서 = B2 상태 rows 순서, 1부터 센다.

입력 (저장소 루트 기준 기본 경로)
  B1 v2 정규화: data/raw/b1_v2/B1_corrected_v2/data/b1_normalized_v11/games/<id>/normalized_game.json
  B2 상태    : data/raw/b3_v2/b2_state/games/<id>.json
  B3 투구    : data/raw/b3_v2/games/<id>.json
  보완 값    : data/supplements/pitch_supplements.json (네이버 원본 누락분, 출처 기록. 빈 칸만 채움)

사용 예:
    .venv/bin/python -m backend.game.facts 20260328HTSK02026 11
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

VERSION = "b3-facts-v1"

ROOT = Path(__file__).resolve().parents[2]
B1_DIR = ROOT / "data/raw/b1_v2/B1_corrected_v2/data/b1_normalized_v11/games"
B2_DIR = ROOT / "data/raw/b3_v2/b2_state/games"
B3_DIR = ROOT / "data/raw/b3_v2/games"
# 네이버 원본에 없는 투구 정보를 다른 출처로 보완한 값 (git에 있음, 항목마다 출처 기록)
SUPPLEMENT_PATH = ROOT / "data/supplements/pitch_supplements.json"
SUPPLEMENT_FIELDS = ("pitch_type", "pitch_type_raw", "speed_reported")

NO_RECORD = "기록 없음"

# 타석 결과 (타자가 주인공인 플레이)
BATTER_RESULTS = {
    "single", "double", "triple", "home_run", "walk", "intentional_walk", "hit_by_pitch",
    "strikeout", "dropped_third_strike", "flyout", "groundout", "lineout", "double_play",
    "triple_play", "sacrifice_fly", "sacrifice_bunt", "bunt_out", "reached_on_error",
    "fielders_choice", "reach_unspecified", "batted_ball_out",
}
# 타석 결과 뒤에 붙어 나오는 주자 줄 (같은 플레이의 일부로 묶음)
RUNNER_FOLLOW = {"runner_advance", "run_scored", "runner_out"}

# B1 event_type → 유형 태그 (tools/event_types.txt)
EVENT_TAG = {
    "strikeout": "STRIKEOUT",
    "dropped_third_strike": "DROPPED_THIRD_STRIKE",
    "sacrifice_fly": "SAC_FLY",
    "sacrifice_bunt": "SAC_BUNT",
    "double_play": "DOUBLE_PLAY",
    "hit_by_pitch": "HIT_BY_PITCH",
    "walk": "WALK",
    "intentional_walk": "INTENTIONAL_WALK",
    "video_review": "VIDEO_REVIEW",
    "single": "SINGLE",
    "double": "DOUBLE",
    "triple": "TRIPLE",
    "home_run": "HOME_RUN",
    "groundout": "GROUNDOUT",
    "flyout": "FLYOUT",
    "lineout": "LINEOUT",
    "reached_on_error": "ERROR",
    "fielders_choice": "FIELDERS_CHOICE",
    "steal": "STOLEN_BASE",
    "caught_stealing": "CAUGHT_STEALING",
    "pickoff_out": "PICKOFF",
}
# B1 event_tags → 유형 태그
B1_TAG = {
    "wild_pitch": "WILD_PITCH",
    "passed_ball": "PASSED_BALL",
    "balk": "BALK",
    "error": "ERROR",
}
# 원문에 나오는 말 → 유형 태그 (event_type 으로 따로 안 나뉘는 규칙)
TEXT_TAG = [
    ("인필드 플라이", "INFIELD_FLY"),
    ("인필드플라이", "INFIELD_FLY"),
    ("포스아웃", "FORCE_OUT"),
    ("태그업", "TAG_UP"),
    ("주루방해", "OBSTRUCTION"),
    ("수비방해", "INTERFERENCE"),
    ("타격방해", "INTERFERENCE"),
]


@dataclass
class Game:
    game_id: str
    away: str
    home: str
    rows: list[dict]                       # B2 상태 rows (플레이 순서)
    plays: dict[str, dict]                 # play_id → B1 플레이
    pitches: dict[str, dict] = field(default_factory=dict)  # play_id → B3 투구
    names: dict[str, str] = field(default_factory=dict)     # player_id → 이름 (같은 경기 안)


@lru_cache(maxsize=1)
def _supplements(path: Path = SUPPLEMENT_PATH) -> dict[str, dict]:
    if not path.exists():
        return {}
    return {s["play_id"]: s for s in json.loads(path.read_text(encoding="utf-8"))["pitches"]}


def _apply_supplement(p: dict) -> dict:
    """보완 값을 덧입힌다.
    - 기본: 원본의 빈 칸만 채운다.
    - override: true 인 항목은 원본 값을 바꾼다 (원본 값은 supplement_replaced 에 남김).
    결과(볼/스트라이크/타격)가 원본과 다르면 같은 공이라고 볼 수 없으니 쓰지 않는다.
    """
    s = _supplements().get(p["play_id"])
    if not s or s.get("result_text", p.get("result_text")) != p.get("result_text"):
        return p
    if s.get("override"):
        changed = {k: s[k] for k in SUPPLEMENT_FIELDS if s.get(k) is not None and p.get(k) != s[k]}
        replaced = {k: p.get(k) for k in changed}
        return p | changed | {"supplement_source": s["source"], "supplement_replaced": replaced}
    filled = {k: s[k] for k in SUPPLEMENT_FIELDS if s.get(k) is not None and p.get(k) in (None, "")}
    return p | filled | {"supplement_source": s["source"]} if filled else p


@lru_cache(maxsize=32)
def load_game(game_id: str, b1_dir: Path = B1_DIR, b2_dir: Path = B2_DIR,
              b3_dir: Path = B3_DIR) -> Game:
    b1 = json.loads((b1_dir / game_id / "normalized_game.json").read_text(encoding="utf-8"))
    b2 = json.loads((b2_dir / f"{game_id}.json").read_text(encoding="utf-8"))
    b3_path = b3_dir / f"{game_id}.json"
    pitches = {}
    if b3_path.exists():
        b3 = json.loads(b3_path.read_text(encoding="utf-8"))
        pitches = {p["play_id"]: _apply_supplement(p) for p in b3.get("pitches", [])}
    summary = b2.get("summary", {})
    # 원본 일부 줄은 선수 ID만 있고 이름이 비어 있다. 같은 경기에서 같은 ID의 이름을 쓴다.
    names = {}
    for p in b1["plays"]:
        for role in ("batter", "pitcher"):
            person = p.get(role) or {}
            if person.get("player_id") and person.get("name"):
                names.setdefault(person["player_id"], person["name"])
    return Game(
        game_id=game_id,
        away=summary.get("away") or b1["metadata_raw"].get("awayTeamName", "원정"),
        home=summary.get("home") or b1["metadata_raw"].get("homeTeamName", "홈"),
        rows=b2["rows"],
        plays={p["play_id"]: p for p in b1["plays"]},
        pitches=pitches,
        names=names,
    )


# ---------- 문장 조각 ----------

def _half(h: str | None) -> str:
    return {"top": "초", "bottom": "말"}.get(h or "", "")


def _outs(n: int | None) -> str:
    if n is None:
        return f"아웃 {NO_RECORD}"
    return {0: "무사", 1: "1사", 2: "2사"}.get(n, f"{n}아웃")


def _bases(state: dict | None) -> str:
    """주자 상황. 이름이 있으면 같이 적는다: '1,3루 (1루 김호령, 3루 카스트로)'."""
    if not state or state.get("runners") is None:
        return f"주자 {NO_RECORD}"
    runners = state["runners"]
    occ = [b for b in ("1", "2", "3") if runners.get(b) or (state.get("runner_count") or {}).get(b)]
    if not occ:
        return "주자 없음"
    head = "만루" if len(occ) == 3 else ",".join(occ) + "루"
    names = [f"{b}루 {runners[b]}" for b in occ if runners.get(b)]
    return f"{head} ({', '.join(names)})" if names else head


def _score(game: Game, state: dict | None) -> str:
    s = (state or {}).get("score")
    if not s or s.get("away") is None or s.get("home") is None:
        return f"점수 {NO_RECORD}"
    return f"점수 {game.away} {s['away']}-{s['home']} {game.home}"


def _situation(game: Game, row: dict, state: dict | None) -> str:
    inning = row.get("inning")
    when = f"{inning}회{_half(row.get('inning_half'))}" if inning else f"이닝 {NO_RECORD}"
    return f"{when}, {_outs((state or {}).get('outs'))}, {_bases(state)}, {_score(game, state)}"


@lru_cache(maxsize=1)
def _all_names(b1_dir: Path = B1_DIR) -> dict[str, str]:
    """전체 경기의 player_id → 이름. 경기 안에서 못 찾을 때만 한 번 만든다 (수십 초)."""
    names: dict[str, str] = {}
    for path in sorted(b1_dir.glob("*/normalized_game.json")):
        for p in json.loads(path.read_text(encoding="utf-8"))["plays"]:
            for role in ("batter", "pitcher"):
                person = p.get(role) or {}
                if person.get("player_id") and person.get("name"):
                    names.setdefault(person["player_id"], person["name"])
    return names


def _name(game: Game, person: dict | None) -> str | None:
    person = person or {}
    pid = person.get("player_id") or ""
    return (person.get("name") or game.names.get(pid)
            or (_all_names().get(pid) if pid else None) or None)


def _pitch_text(p: dict) -> str:
    result = p.get("result_text") or NO_RECORD
    # 피치클락 위반·파울 플라이 포구 실책은 공을 던진 게 아니다 (B3 is_physical_pitch=False).
    # 구종·구속이 "빠진" 게 아니므로 기록 없음 대신 실제 투구가 아니라고 적는다.
    if p.get("is_physical_pitch") is False or "피치클락" in result:
        return f"{result} (실제 투구 아님)"
    num = f"{p.get('pitch_number')}구" if p.get("pitch_number") else "투구"
    speed = p.get("speed_reported", p.get("speed_value"))
    manual = p.get("pitch_record_kind") == "manual_reconstructed_pitch"
    if manual and not p.get("pitch_type_raw") and speed is None:
        return f"{num} 결과 {result} (원본 누락으로 수동 복원, 구종·구속 원본 없음)"
    parts = [num, p.get("pitch_type_raw") or f"구종 {NO_RECORD}",
             f"{speed:g}km/h" if isinstance(speed, (int, float)) else f"구속 {NO_RECORD}",
             f"결과 {result}"]
    if p.get("supplement_source"):
        where = p["supplement_source"].split(" http")[0]
        old = p.get("supplement_replaced")
        if old is not None:
            was = []
            if "pitch_type_raw" in old:
                was.append(f"구종 {old['pitch_type_raw'] or '없음'}")
            if "speed_reported" in old:
                was.append(f"{old['speed_reported']:g}km/h" if isinstance(old["speed_reported"], (int, float))
                           else "구속 없음")
            parts.append(f"(네이버 값 {'·'.join(was)}를 {where} 값으로 수정)")
        else:
            parts.append(f"(네이버 원본 누락, {where}로 보완)")
    return " ".join(parts)


def _players(game: Game, idx: int) -> tuple[str | None, str | None]:
    """idx 줄의 타자·투수 이름. 원본 칸이 비어 있으면 같은 기록 안에서 찾는다.
    - 타자: 같은 타석의 'N번타자 이름' 줄, 또는 결과 줄 '이름 : …'
    - 투수: 같은 반이닝에서 뒤 줄의 투수 (그 사이에 투수 교체가 없을 때만)
    """
    rows = game.rows
    row = rows[idx]
    play = game.plays.get(row["play_id"], {})
    batter, pitcher = _name(game, play.get("batter")), _name(game, play.get("pitcher"))
    same_half = lambda r: (r.get("inning"), r.get("inning_half")) == (row.get("inning"), row.get("inning_half"))
    if not batter:
        if row["event_type"] in BATTER_RESULTS and " : " in (row.get("description") or ""):
            batter = row["description"].split(" : ")[0].strip()
        else:
            for r in reversed(rows[:idx + 1]):
                if not same_half(r) or r["event_type"] == "inning_start":
                    break
                m = re.match(r"\d+번타자 (\S+)", r.get("description") or "")
                if r["event_type"] == "batter_announcement" and m:
                    batter = m.group(1)
                    break
    if not pitcher:
        for r in rows[idx + 1:]:
            if not same_half(r) or (r["event_type"] == "substitution"
                                    and (r.get("description") or "").startswith("투수")):
                break
            pitcher = _name(game, game.plays.get(r["play_id"], {}).get("pitcher"))
            if pitcher:
                break
    return batter, pitcher


def _runs(before: dict | None, after: dict | None) -> tuple[int, int] | None:
    try:
        b, a = before["score"], after["score"]
        return a["away"] - b["away"], a["home"] - b["home"]
    except (TypeError, KeyError):
        return None


# ---------- 플레이 묶기 ----------

def _group(game: Game, idx: int) -> tuple[list[dict], list[dict]]:
    """idx 플레이와, 그 결과로 같이 일어난 주자 줄들. 그리고 이 타석의 투구 줄들."""
    rows = game.rows
    row = rows[idx]
    group = [row]
    if row["event_type"] in BATTER_RESULTS:
        j = idx + 1
        while j < len(rows) and rows[j]["event_type"] in RUNNER_FOLLOW:
            group.append(rows[j])
            j += 1
    pitch_rows = []
    if row["event_type"] in BATTER_RESULTS:
        j = idx - 1
        while j >= 0 and rows[j]["event_type"] not in ("batter_announcement", "inning_start"):
            if rows[j]["event_type"] == "pitch":
                pitch_rows.append(rows[j])
            j -= 1
        pitch_rows.reverse()
    return group, pitch_rows


def _tags(game: Game, group: list[dict]) -> list[str]:
    tags: list[str] = []

    def add(t: str | None) -> None:
        if t and t not in tags:
            tags.append(t)

    for r in group:
        p = game.plays.get(r["play_id"], {})
        et = r["event_type"]
        add(EVENT_TAG.get(et))
        if et == "substitution" and (r.get("description") or "").startswith("투수"):
            add("PITCHING_CHANGE")
        for t in p.get("event_tags") or []:
            add(B1_TAG.get(t))
        text = r.get("description") or ""
        for word, t in TEXT_TAG:
            if word in text:
                add(t)
    return tags


# ---------- 공개 함수 ----------

def build_facts(game_id: str, seq: int, game: Game | None = None) -> dict:
    """경기 ID + 플레이 순번(1부터) → F 목록과 유형 태그."""
    game = game or load_game(game_id)
    if not 1 <= seq <= len(game.rows):
        raise IndexError(f"{game_id}: 플레이 순번은 1~{len(game.rows)} (받은 값 {seq})")
    idx = seq - 1
    row = game.rows[idx]
    play = game.plays.get(row["play_id"], {})
    et = row["event_type"]
    group, pitch_rows = _group(game, idx)
    before = row.get("state_before")
    after = group[-1].get("state_after")

    lines: list[str] = [_situation(game, row, before)]

    batter, pitcher = _players(game, idx)
    if et in BATTER_RESULTS or et == "pitch":
        lines.append(f"타자 {batter or NO_RECORD}, 투수 {pitcher or NO_RECORD}")

    if et == "pitch":
        p = game.pitches.get(row["play_id"]) or play.get("pitch")
        lines.append(_pitch_text(p) if p else f"투구 정보 {NO_RECORD}")
    else:
        lines.append(f"기록: {row.get('description') or NO_RECORD}")
        for r in group[1:]:
            lines.append(f"주자 기록: {r.get('description') or NO_RECORD}")

    if et in BATTER_RESULTS:
        ps = [game.pitches.get(r["play_id"]) for r in pitch_rows]
        ps = [p for p in ps if p]
        if ps:
            lines.append(f"이 타석 투구 수 {len(ps)}개, 마지막 공: {_pitch_text(ps[-1])}")
        elif pitch_rows:
            lines.append(f"이 타석 투구 {len(pitch_rows)}개, 투구 세부 {NO_RECORD}")

    if et == "substitution":
        lines.append(f"교체 사유 {NO_RECORD}")

    if after != before:  # 투구처럼 상황이 그대로면 같은 줄을 두 번 쓰지 않는다
        lines.append(f"플레이 후 {_outs((after or {}).get('outs'))}, {_bases(after)}, {_score(game, after)}")
        runs = _runs(before, after)
        if runs and any(runs):
            scored = [f"{team} {n}점" for team, n in zip((game.away, game.home), runs) if n]
            lines.append(f"이 플레이로 득점: {', '.join(scored)}")

    return {
        "version": VERSION,
        "game_id": game_id,
        "seq": seq,
        "play_id": row["play_id"],
        "event_type": et,
        "type_tags": _tags(game, group),
        "facts": [{"id": f"F{i}", "text": t} for i, t in enumerate(lines, 1)],
    }


def build_game_facts(game_id: str) -> list[dict]:
    """한 경기 전체 플레이의 F. B4(DB 적재)에서 쓴다."""
    game = load_game(game_id)
    return [build_facts(game_id, s, game) for s in range(1, len(game.rows) + 1)]


def main() -> None:
    ap = argparse.ArgumentParser(description="플레이 사실(F) 생성")
    ap.add_argument("game_id")
    ap.add_argument("seq", type=int, nargs="?", help="플레이 순번 (생략하면 경기 전체)")
    args = ap.parse_args()
    out = build_facts(args.game_id, args.seq) if args.seq else build_game_facts(args.game_id)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
