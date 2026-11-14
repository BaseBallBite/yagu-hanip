"""B12 영상매칭: 하이라이트 장면 표를 SQLite에 넣고 재생 시간으로 조회한다.

장면 표는 AI 쪽(ai/highlight)이 하이라이트 영상을 미리 분석해 만든 JSON이다.
"영상 몇 초~몇 초는 몇 회 몇 사, 주자·점수가 어떤 상황인지"가 들어 있다. 여기서는 AI를 부르지 않는다.

    입력  ai/highlight/output/scenes_<경기ID>.json   장면 표
          ai/highlight/games.csv                     경기별 용도 (demo / eval)
    출력  data/db/highlights.sqlite                  (git에 안 올라감. 없으면 API가 처음 요청 때 만든다)

평가용(eval) 경기는 넣지 않는다. 시연·화면 테스트에 쓰면 평가가 오염된다.

    .venv/bin/python -m backend.highlight.store build
    .venv/bin/python -m backend.highlight.store scene YQD3hMI2LPo 757.3

표
  highlights      영상 1행: video_id, game_id, 날짜, 원정/홈 팀, 장면 수, 영상 길이
  highlight_scene 장면 1행: video_id, 순번, start_sec, end_sec, status, 장면 JSON 통째로
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCENE_DIR = ROOT / "ai/highlight/output"
GAMES_CSV = ROOT / "ai/highlight/games.csv"
DB_PATH = Path(os.environ.get("YAGU_HIGHLIGHT_DB", ROOT / "data/db/highlights.sqlite"))
VERSION = "b12-highlight-v1"

UNKNOWN = "확인 불가"

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE highlights (
    video_id TEXT PRIMARY KEY,
    game_id TEXT NOT NULL,
    game_date TEXT NOT NULL,
    away TEXT NOT NULL,
    home TEXT NOT NULL,
    scene_count INTEGER NOT NULL,
    duration_sec REAL NOT NULL
);
CREATE TABLE highlight_scene (
    video_id TEXT NOT NULL REFERENCES highlights(video_id),
    idx INTEGER NOT NULL,          -- 영상 안 장면 순번 (0부터)
    game_id TEXT NOT NULL,
    start_sec REAL NOT NULL,
    end_sec REAL NOT NULL,
    status TEXT NOT NULL,          -- 확정 / 추정 / 확인 불가
    data_json TEXT NOT NULL,       -- 장면 JSON 통째로 (화면이 그대로 씀)
    PRIMARY KEY (video_id, idx)
);
CREATE INDEX idx_scene ON highlight_scene(video_id, start_sec);
"""


def demo_game_ids(games_csv: Path = GAMES_CSV) -> list[str]:
    """games.csv 에서 용도에 demo 가 들어간 경기만 (eval+demo 포함)."""
    with open(games_csv, encoding="utf-8") as f:
        return [r["game_id"] for r in csv.DictReader(f) if "demo" in r["purpose"].split("+")]


def _game_date(game_id: str) -> str:
    return f"{game_id[:4]}-{game_id[4:6]}-{game_id[6:8]}"


def load_scene_file(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    scenes = d["scenes"]
    if not scenes:
        raise ValueError(f"{path.name}: 장면이 없음")
    for i, s in enumerate(scenes):
        if s["start"] >= s["end"]:
            raise ValueError(f"{path.name}: {i}번 장면 start({s['start']}) >= end({s['end']})")
        if i and scenes[i - 1]["end"] > s["start"]:
            raise ValueError(f"{path.name}: {i - 1}·{i}번 장면 구간이 겹침")
    return d


def build(db_path: Path = DB_PATH, game_ids: list[str] | None = None,
          scene_dir: Path = SCENE_DIR) -> dict:
    """DB를 새로 만든다 (기존 파일은 덮어씀). game_ids 를 안 주면 games.csv 의 demo 경기."""
    ids = game_ids if game_ids is not None else demo_game_ids()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = db_path.with_suffix(".building")
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    con.executescript(SCHEMA)
    n_scenes = 0
    for gid in ids:
        d = load_scene_file(scene_dir / f"scenes_{gid}.json")
        scenes = d["scenes"]
        con.execute("INSERT INTO highlights VALUES (?,?,?,?,?,?,?)",
                    (d["video_id"], d["game_id"], _game_date(d["game_id"]), d["away"], d["home"],
                     len(scenes), scenes[-1]["end"]))
        con.executemany(
            "INSERT INTO highlight_scene VALUES (?,?,?,?,?,?,?)",
            [(d["video_id"], i, d["game_id"], s["start"], s["end"], s["status"],
              json.dumps(s, ensure_ascii=False)) for i, s in enumerate(scenes)],
        )
        n_scenes += len(scenes)
    info = {"version": VERSION, "videos": len(ids), "scenes": n_scenes,
            "built_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    con.executemany("INSERT INTO meta VALUES (?,?)", [(k, str(v)) for k, v in info.items()])
    con.commit()
    con.close()
    os.replace(tmp, db_path)
    return info


# ---------- 조회 ----------

def connect(db_path: Path = DB_PATH, build_if_missing: bool = True) -> sqlite3.Connection:
    """장면 표는 git에 있어서 금방 만들 수 있다. DB가 없으면 바로 만든다."""
    if not db_path.exists():
        if not build_if_missing:
            raise FileNotFoundError(f"하이라이트 DB가 없습니다: {db_path}")
        build(db_path)
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def list_highlights(con) -> list[dict]:
    return [dict(r) for r in con.execute("SELECT * FROM highlights ORDER BY game_date, game_id")]


def get_highlight(con, video_id: str) -> dict | None:
    r = con.execute("SELECT * FROM highlights WHERE video_id = ?", (video_id,)).fetchone()
    return None if r is None else dict(r)


def list_scenes(con, video_id: str) -> list[dict]:
    return [json.loads(r["data_json"]) for r in con.execute(
        "SELECT data_json FROM highlight_scene WHERE video_id = ? ORDER BY idx", (video_id,))]


def scene_at(con, video_id: str, t: float) -> dict:
    """start ≤ t < end 인 장면. 없으면(영상 끝 넘어감 등) {"status": "확인 불가"}."""
    r = con.execute(
        "SELECT data_json, end_sec FROM highlight_scene WHERE video_id = ? AND start_sec <= ? "
        "ORDER BY start_sec DESC LIMIT 1", (video_id, t)).fetchone()
    if r is None or t >= r["end_sec"]:
        return {"status": UNKNOWN}
    return json.loads(r["data_json"])


def main() -> None:
    ap = argparse.ArgumentParser(description="B12 하이라이트 장면 표 (SQLite)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="DB 새로 만들기 (demo 경기만)")
    s = sub.add_parser("scene", help="재생 시간으로 장면 조회")
    s.add_argument("video_id")
    s.add_argument("t", type=float)
    args = ap.parse_args()
    if args.cmd == "build":
        print(json.dumps(build(), ensure_ascii=False))
    else:
        print(json.dumps(scene_at(connect(), args.video_id, args.t), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
