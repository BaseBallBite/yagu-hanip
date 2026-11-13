"""투구별 볼·스트라이크 카운트 (B4).

B3 투구 결과를 타석(plate_appearance_id) 안에서 순서대로 세어 공마다 던지기 전/후 카운트를 만든다.

규칙
  볼(B), 피치클락 투수위반 볼                → 볼 +1
  스트라이크(T), 헛스윙(S), 번트헛스윙(V),
  피치클락 타자위반 스트라이크               → 스트라이크 +1
  파울(F)                                    → 2스트라이크 전이면 스트라이크 +1
  ○○ 파울 플라이 포구 실책                  → 그대로 (바로 앞 파울 공을 설명하는 별도 줄)
  번트파울(W)                                → 스트라이크 +1 (2스트라이크 번트파울은 삼진)
  타격(H)                                    → 그대로 (인플레이)

네이버 원본의 줄별 카운트(currentGameState)와 대조한 결과는 verify() 로 확인한다.
    .venv/bin/python -m backend.game.count verify
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from backend.game.facts import ROOT, Game, load_game

RAW_DIR = ROOT / "data/raw/season/data/games"  # be-kim 시즌 수집 원본 (inning_NN.json)

BALL = "ball"
STRIKE = "strike"
FOUL = "foul"
BUNT_FOUL = "bunt_foul"
IN_PLAY = "in_play"
NOTE = "note"  # 카운트를 바꾸지 않는 설명 줄

CODE_KIND = {"B": BALL, "T": STRIKE, "S": STRIKE, "V": STRIKE, "F": FOUL, "W": BUNT_FOUL, "H": IN_PLAY}
TEXT_KIND = {"볼": BALL, "스트라이크": STRIKE, "헛스윙": STRIKE, "번트헛스윙": STRIKE,
             "파울": FOUL, "번트파울": BUNT_FOUL, "타격": IN_PLAY}


def pitch_kind(p: dict) -> str | None:
    """투구 결과를 카운트 규칙의 종류로 바꾼다. 알 수 없으면 None."""
    code = p.get("result_code_raw") or p.get("result_code")
    if code in CODE_KIND:
        return CODE_KIND[code]
    text = (p.get("result_text") or "").strip()
    if text in TEXT_KIND:
        return TEXT_KIND[text]
    if text.endswith("볼"):          # 피치클락 투수위반 볼
        return BALL
    if text.endswith("스트라이크"):  # 피치클락 타자위반 스트라이크
        return STRIKE
    if "파울 플라이 포구 실책" in text:  # 앞 파울 공에 붙는 설명 줄, 새 공이 아님
        return NOTE
    return None


def apply(balls: int, strikes: int, kind: str | None) -> tuple[int, int]:
    if kind == BALL:
        return balls + 1, strikes
    if kind in (STRIKE, BUNT_FOUL):
        return balls, strikes + 1
    if kind == FOUL:
        return balls, min(strikes + 1, 2)
    return balls, strikes


def compute_counts(game: Game) -> dict[str, dict]:
    """play_id → {balls_before, strikes_before, balls_after, strikes_after}. 투구 줄만 들어 있다."""
    out: dict[str, dict] = {}
    current: dict[str, tuple[int, int]] = {}
    for row in game.rows:
        p = game.pitches.get(row["play_id"])
        if not p or not p.get("plate_appearance_id"):
            continue
        pa = p["plate_appearance_id"]
        b, s = current.get(pa, (0, 0))
        b2, s2 = apply(b, s, pitch_kind(p))
        current[pa] = (b2, s2)
        out[row["play_id"]] = {"balls_before": b, "strikes_before": s,
                               "balls_after": b2, "strikes_after": s2}
    return out


# ---------- 원본 대조 ----------

def _raw_counts(game_id: str, raw_dir: Path = RAW_DIR) -> dict[int, tuple[int, int]]:
    """원본 seqno → 그 줄 직후 (볼, 스트라이크)."""
    out = {}
    for f in sorted((raw_dir / game_id).glob("inning_*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for relay in d["result"]["textRelayData"]["textRelays"]:
            for o in relay.get("textOptions", []):
                st = o.get("currentGameState") or {}
                if o.get("seqno") is not None and "ball" in st:
                    out[int(o["seqno"])] = (int(st["ball"]), int(st["strike"]))
    return out


def verify(game_ids: list[str], show: int = 10) -> dict:
    """계산한 '던진 후' 카운트를 원본 줄의 카운트와 비교한다.
    타석을 끝낸 공(볼넷 4구, 삼진 3스트라이크)은 원본이 0-0 으로 되돌리기도 하므로 따로 센다."""
    stat = Counter()
    examples = []
    for gid in game_ids:
        game = load_game(gid)
        raw = _raw_counts(gid)
        if not raw:
            stat["no_raw_game"] += 1
            continue
        for pid, c in compute_counts(game).items():
            seq = (game.plays.get(pid) or {}).get("source_seqno")
            if seq is None or seq not in raw:
                stat["no_raw_row"] += 1
                continue
            mine = (c["balls_after"], c["strikes_after"])
            ending = mine[0] >= 4 or mine[1] >= 3
            if raw[seq] == mine:
                stat["match"] += 1
            elif ending:
                stat["ending_pitch_differs"] += 1
            else:
                stat["mismatch"] += 1
                if len(examples) < show:
                    p = game.pitches[pid]
                    examples.append({"game_id": gid, "play_id": pid, "seqno": seq,
                                     "result": p.get("result_text"), "mine": mine, "raw": raw[seq]})
        load_game.cache_clear()
    return {"stat": dict(stat), "examples": examples}


def main() -> None:
    from backend.game.store import _game_ids
    ap = argparse.ArgumentParser(description="투구별 볼·스트라이크 카운트")
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("verify", help="네이버 원본 카운트와 대조")
    v.add_argument("--limit", type=int)
    args = ap.parse_args()
    print(json.dumps(verify(_game_ids(args.limit)), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
