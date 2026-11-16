"""B4 저장소: B1 v2 정규화 · B2 상태 · B3 투구 · F 를 SQLite 한 파일에 적재하고 조회한다.

DB 파일은 용량이 커서 git에 올리지 않는다(data/db/). 각자 아래 명령으로 만든다.

    .venv/bin/python -m backend.game.store build            # 720경기 전체 (몇 분)
    .venv/bin/python -m backend.game.store build --limit 5  # 빠른 확인용
    .venv/bin/python -m backend.game.store plays 20260328HTSK02026 --limit 3

표
  games   경기 1행: 날짜, 원정/홈 팀, 최종 점수, B2 점수 일치 여부
  plays   플레이 1행 (game_id, seq 로 조회): 이닝, 유형, 원문, 타자/투수, 상태 전/후, 유형 태그, F 목록
  pitches 투구 1행 (B3): 구종, 구속, 결과, 존 위치, 궤적, 시각화 가능 여부,
          던지기 전/후 볼·스트라이크 카운트 (count.py 규칙, 네이버 원본과 99.99% 일치)

플레이 순번(seq)은 facts.py 와 같다: B2 상태 rows 순서, 1부터.
사전 카드는 여기 넣지 않는다 (data/dict/dict.json 을 B7 API가 그대로 읽는다).
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import time
from pathlib import Path

from backend.game.count import compute_counts
from backend.game.facts import B1_DIR, B2_DIR, ROOT, build_facts, load_game
from backend.game.facts import _players as players  # F와 같은 규칙으로 빈 타자·투수 이름을 채움

DB_PATH = Path(os.environ.get("YAGU_DB", ROOT / "data/db/yagu.sqlite"))
VERSION = "b4-store-v3"  # v2: 투구별 볼·스트라이크 카운트, v3: 유형 태그 60개 기준

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE games (
    game_id TEXT PRIMARY KEY,
    game_date TEXT NOT NULL,
    start_time TEXT,
    away TEXT NOT NULL,
    home TEXT NOT NULL,
    away_code TEXT,
    home_code TEXT,
    away_score INTEGER,
    home_score INTEGER,
    status TEXT,
    final_score_match INTEGER,
    play_count INTEGER NOT NULL
);
CREATE TABLE plays (
    game_id TEXT NOT NULL REFERENCES games(game_id),
    seq INTEGER NOT NULL,
    play_id TEXT NOT NULL UNIQUE,
    inning INTEGER,
    half TEXT,
    event_type TEXT NOT NULL,
    description TEXT,
    batter TEXT,
    pitcher TEXT,
    state_before TEXT,
    state_after TEXT,
    type_tags TEXT NOT NULL,
    facts TEXT NOT NULL,
    PRIMARY KEY (game_id, seq)
);
CREATE INDEX plays_event ON plays(game_id, event_type);
CREATE TABLE pitches (
    play_id TEXT PRIMARY KEY REFERENCES plays(play_id),
    game_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    plate_appearance_id TEXT,
    pitch_number INTEGER,
    pitch_type TEXT,
    pitch_type_raw TEXT,
    speed REAL,
    result_text TEXT,
    result_code TEXT,
    is_physical_pitch INTEGER,
    visualization_status TEXT,
    zone TEXT,
    trajectory TEXT,
    supplement_source TEXT,  -- 네이버 원본 누락·오류를 다른 출처로 보완한 경우 그 출처
    balls_before INTEGER,
    strikes_before INTEGER,
    balls_after INTEGER,
    strikes_after INTEGER
);
CREATE INDEX pitches_game ON pitches(game_id, seq);
"""


def _j(v) -> str | None:
    return None if v is None else json.dumps(v, ensure_ascii=False)


def _game_ids(limit: int | None = None) -> list[str]:
    ids = sorted(p.stem for p in B2_DIR.glob("*.json"))
    return ids[:limit] if limit else ids


def build(db_path: Path = DB_PATH, limit: int | None = None,
          game_ids: list[str] | None = None) -> dict:
    """DB를 새로 만든다 (기존 파일은 덮어씀). 중간에 실패하면 이전 DB를 그대로 둔다.
    game_ids 를 주면 그 경기만 넣는다 (테스트용)."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = db_path.with_suffix(".building")
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    con.executescript(SCHEMA)
    started = time.time()
    n_plays = n_pitches = 0
    ids = game_ids or _game_ids(limit)
    for gid in ids:
        game = load_game(gid)
        b1 = json.loads((B1_DIR / gid / "normalized_game.json").read_text(encoding="utf-8"))
        meta = b1["metadata_raw"]
        summary = json.loads((B2_DIR / f"{gid}.json").read_text(encoding="utf-8")).get("summary", {})
        con.execute(
            "INSERT INTO games VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (gid, meta.get("gameDate"), meta.get("gameDateTime"), game.away, game.home,
             meta.get("awayTeamCode"), meta.get("homeTeamCode"),
             meta.get("awayTeamScore"), meta.get("homeTeamScore"), meta.get("statusInfo"),
             int(bool(summary.get("final_score_match"))), len(game.rows)),
        )
        play_rows, pitch_rows = [], []
        counts = compute_counts(game)
        for seq, row in enumerate(game.rows, 1):
            f = build_facts(gid, seq, game)
            batter, pitcher = players(game, seq - 1)
            play_rows.append((
                gid, seq, row["play_id"], row.get("inning"), row.get("inning_half"),
                row["event_type"], row.get("description"), batter, pitcher,
                _j(row.get("state_before")), _j(row.get("state_after")),
                _j(f["type_tags"]), _j(f["facts"]),
            ))
            p = game.pitches.get(row["play_id"])
            if p:
                c = counts.get(row["play_id"], {})
                pitch_rows.append((
                    row["play_id"], gid, seq, p.get("plate_appearance_id"), p.get("pitch_number"),
                    p.get("pitch_type"), p.get("pitch_type_raw"), p.get("speed_reported"),
                    p.get("result_text"), p.get("result_code_raw"),
                    None if p.get("is_physical_pitch") is None else int(p["is_physical_pitch"]),
                    p.get("visualization_status"), _j(p.get("zone")), _j(p.get("trajectory")),
                    p.get("supplement_source"),
                    c.get("balls_before"), c.get("strikes_before"),
                    c.get("balls_after"), c.get("strikes_after"),
                ))
        con.executemany("INSERT INTO plays VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", play_rows)
        con.executemany("INSERT INTO pitches VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", pitch_rows)
        n_plays += len(play_rows)
        n_pitches += len(pitch_rows)
        load_game.cache_clear()
    info = {"version": VERSION, "games": len(ids), "plays": n_plays, "pitches": n_pitches,
            "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "seconds": round(time.time() - started, 1)}
    con.executemany("INSERT INTO meta VALUES (?,?)", [(k, str(v)) for k, v in info.items()])
    con.commit()
    con.close()
    os.replace(tmp, db_path)
    return info


# ---------- 조회 ----------

def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(
            f"DB가 없습니다: {db_path}\n먼저 실행: .venv/bin/python -m backend.game.store build")
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def _play(r: sqlite3.Row, with_facts: bool = True) -> dict:
    d = {
        "seq": r["seq"], "play_id": r["play_id"], "inning": r["inning"], "half": r["half"],
        "event_type": r["event_type"], "description": r["description"],
        "batter": r["batter"], "pitcher": r["pitcher"],
        "state_before": json.loads(r["state_before"]) if r["state_before"] else None,
        "state_after": json.loads(r["state_after"]) if r["state_after"] else None,
        "type_tags": json.loads(r["type_tags"]),
    }
    if with_facts:
        d["facts"] = json.loads(r["facts"])
    return d


def _pitch(r: sqlite3.Row) -> dict:
    return {
        "plate_appearance_id": r["plate_appearance_id"],  # 같은 타석의 공끼리 묶을 때 사용
        "pitch_number": r["pitch_number"], "pitch_type": r["pitch_type"],
        "pitch_type_raw": r["pitch_type_raw"], "speed": r["speed"],
        "result_text": r["result_text"], "result_code": r["result_code"],
        "visualization_status": r["visualization_status"],
        "zone": json.loads(r["zone"]) if r["zone"] else None,
        "trajectory": json.loads(r["trajectory"]) if r["trajectory"] else None,
        "supplement_source": r["supplement_source"],
        # 볼·스트라이크 카운트: 이 공을 던지기 전 / 던진 후
        "count_before": {"balls": r["balls_before"], "strikes": r["strikes_before"]},
        "count_after": {"balls": r["balls_after"], "strikes": r["strikes_after"]},
    }


def list_games(con, date: str | None = None, team: str | None = None) -> list[dict]:
    sql, args = "SELECT * FROM games WHERE 1=1", []
    if date:
        sql += " AND game_date = ?"
        args.append(date)
    if team:
        sql += " AND (away = ? OR home = ?)"
        args += [team, team]
    return [dict(r) | {"final_score_match": bool(r["final_score_match"])}
            for r in con.execute(sql + " ORDER BY game_date, game_id", args)]


def get_game(con, game_id: str) -> dict | None:
    r = con.execute("SELECT * FROM games WHERE game_id = ?", (game_id,)).fetchone()
    return None if r is None else dict(r) | {"final_score_match": bool(r["final_score_match"])}


def list_plays(con, game_id: str, from_seq: int = 1, limit: int | None = None,
               event_types: list[str] | None = None, with_facts: bool = False,
               with_pitch: bool = False) -> list[dict]:
    """경기 ID로 플레이 목록 조회 (B4 완료 조건)."""
    sql = "SELECT * FROM plays WHERE game_id = ? AND seq >= ?"
    args: list = [game_id, from_seq]
    if event_types:
        sql += f" AND event_type IN ({','.join('?' * len(event_types))})"
        args += event_types
    sql += " ORDER BY seq"
    if limit:
        sql += " LIMIT ?"
        args.append(limit)
    plays = [_play(r, with_facts) for r in con.execute(sql, args)]
    if with_pitch and plays:
        ids = [p["play_id"] for p in plays]
        pitches = {}
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            for r in con.execute(f"SELECT * FROM pitches WHERE play_id IN ({','.join('?' * len(chunk))})", chunk):
                pitches[r["play_id"]] = _pitch(r)
        for p in plays:
            p["pitch"] = pitches.get(p["play_id"])
    return plays


def get_play(con, game_id: str, seq: int) -> dict | None:
    r = con.execute("SELECT * FROM plays WHERE game_id = ? AND seq = ?", (game_id, seq)).fetchone()
    if r is None:
        return None
    d = _play(r, True)
    pr = con.execute("SELECT * FROM pitches WHERE play_id = ?", (r["play_id"],)).fetchone()
    d["pitch"] = _pitch(pr) if pr else None
    return d


def main() -> None:
    ap = argparse.ArgumentParser(description="B4 저장소 (SQLite)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="DB 새로 만들기")
    b.add_argument("--limit", type=int, help="앞에서 N경기만 (빠른 확인용)")
    p = sub.add_parser("plays", help="경기 ID로 플레이 목록 조회")
    p.add_argument("game_id")
    p.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()
    if args.cmd == "build":
        print(json.dumps(build(limit=args.limit), ensure_ascii=False))
    else:
        con = connect()
        print(json.dumps(list_plays(con, args.game_id, limit=args.limit, with_facts=True),
                         ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
