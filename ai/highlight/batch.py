"""
여러 경기 하이라이트를 한 번에 처리: 영상 받기 → 전광판 읽기(v2) → 장면 표 → (평가용이면) 빈 정답표

games.csv 예시 (첫 줄은 그대로)
  game_id,url,purpose
  20260329XXXX,https://youtu.be/AAAA,eval
  20260405XXXX,https://youtu.be/BBBB,demo
  20260412XXXX,https://youtu.be/CCCC,eval+demo

purpose
  eval : 평가용 → 빈 정답표(eval/정답표_<경기ID>.csv)도 만들어줌
  demo : 시연용 → 장면 표만
  eval+demo : 둘 다

사용법
  export GEMINI_API_KEY="..."
  python batch.py games.csv

결과
  highlight_<경기ID>.mp4              영상 (깃에 안 올라감)
  frames/<경기ID>/                     캡처 (깃에 안 올라감)
  readings_<경기ID>.json               전광판 읽기 결과 (깃에 안 올라감)
  output/scenes_<경기ID>.json          장면 표 → 백엔드·프론트에 넘길 파일
  eval/정답표_<경기ID>.csv             평가용일 때만. 사람이 채울 빈 표

중간에 끊겨도 다시 실행하면 이어서 함 (이미 읽은 프레임, 이미 만든 장면 표는 건너뜀)
"""
import argparse
import csv
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scoreboard_read as sr  # noqa: E402
import scene_table  # noqa: E402

GAMES_DIR = os.path.join(HERE, "..", "..", "data", "raw", "b2_state_v2_all", "games")


def save_json(obj, path):
    """중간에 Ctrl+C로 끊겨도 파일이 깨지지 않게, 임시 파일에 다 쓴 다음 바꿔치기함."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def video_id_of(url):
    m = re.search(r"(?:youtu\.be/|v=|shorts/)([\w-]{11})", url)
    return m.group(1) if m else None


def read_game(client, game_id, url, game_path, every, prompt, suffix=""):
    summ = json.load(open(game_path, encoding="utf-8"))["summary"]
    away, home = summ["away"], summ["home"]

    video = sr.download(url, out_base=os.path.join(HERE, f"highlight_{game_id}"))
    frames = sr.grab_frames(video, every, out_dir=os.path.join(HERE, "frames", game_id))

    out = os.path.join(HERE, f"readings_{game_id}{suffix}.json")
    done = {}
    if os.path.exists(out):
        done = {r["frame"]: r for r in json.load(open(out, encoding="utf-8")) if r.get("raw") is not None}

    results = []
    for i, f in enumerate(frames, 1):
        if f["frame"] in done:
            results.append(done[f["frame"]])
            continue
        raw = sr.read_frame(client, f["frame"], sr.PROMPTS[prompt])
        results.append({**f, **sr.to_reading(raw, away, home), "raw": raw, "prompt": prompt})
        if i % 20 == 0 or i == len(frames):
            save_json(results, out)
            print(f"  {i}/{len(frames)}장 읽음")
        time.sleep(1)
    save_json(results, out)
    return out


def make_truth_template(game_id, duration_sec, every_sec):
    """평가용 빈 정답표. 시스템 결과를 보고 고르면 치우치니까, 일정 간격으로 고름."""
    os.makedirs(os.path.join(HERE, "eval"), exist_ok=True)
    path = os.path.join(HERE, "eval", f"정답표_{game_id}.csv")
    if os.path.exists(path):
        print(f"  정답표 이미 있음 → 건너뜀: {path}")
        return path
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["영상시간", "time_sec", "정답_회", "정답_초말", "정답_타자", "비고"])
        t = every_sec
        while t < duration_sec:
            w.writerow([f"{int(t)//60}:{int(t)%60:02d}", float(t), "", "", "", ""])
            t += every_sec
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("games_csv")
    ap.add_argument("--every", type=float, default=5, help="캡처 간격(초)")
    ap.add_argument("--prompt", default="v2", choices=list(sr.PROMPTS))
    ap.add_argument("--carry", type=float, default=0, help="장면 표 추정 처리(초). 0이면 안 씀")
    ap.add_argument("--eval-every", type=float, default=30, help="빈 정답표 간격(초)")
    ap.add_argument("--order", action="store_true", help="장면 표에 순서 규칙 적용")
    ap.add_argument("--suffix", default="", help="결과 파일 이름 뒤에 붙일 말 (예: _v3). 기존 결과를 덮어쓰지 않게")
    args = ap.parse_args()

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY 환경변수가 없음")
    from google import genai
    client = genai.Client(api_key=key)

    games = list(csv.DictReader(open(args.games_csv, encoding="utf-8-sig")))
    os.makedirs(os.path.join(HERE, "output"), exist_ok=True)

    for g in games:
        gid, url, purpose = g["game_id"].strip(), g["url"].strip(), g.get("purpose", "demo").strip()
        print(f"\n===== {gid} ({purpose}) =====")
        game_path = os.path.join(GAMES_DIR, f"{gid}.json")
        if not os.path.exists(game_path):
            print(f"  경기 상태 파일 없음 → 건너뜀: {game_path}")
            continue
        vid = video_id_of(url)
        if not vid:
            print(f"  유튜브 링크에서 영상 ID를 못 찾음 → 건너뜀: {url}")
            continue

        scenes_path = os.path.join(HERE, "output", f"scenes_{gid}{args.suffix}.json")
        readings = read_game(client, gid, url, game_path, args.every, args.prompt, args.suffix)

        table = scene_table.build(game_path, readings, vid, args.every, args.carry, args.order)
        save_json(table, scenes_path)
        n = len(table["scenes"])
        ok = sum(1 for s in table["scenes"] if s["status"] == "확정")
        print(f"  장면 표: {n}개 구간 (확정 {ok}) → {scenes_path}")

        if "eval" in purpose:
            dur = max(r["time_sec"] for r in json.load(open(readings, encoding="utf-8"))) + args.every
            p = make_truth_template(gid, dur, args.eval_every)
            print(f"  빈 정답표: {p}")

    print("\n끝. output/ 폴더의 장면 표를 커밋하면 됨")


if __name__ == "__main__":
    main()