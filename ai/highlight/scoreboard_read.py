"""
하이라이트 영상 → 전광판 읽기 → (선택) 문자중계 매칭

test_local.py 를 고친 버전. 바뀐 점:
  - API 키를 코드에 안 적음 (환경변수 GEMINI_API_KEY 만 사용)
  - 전광판에서 주자(1·2·3루), 타자 이름, 볼·스트라이크, 리플레이 여부까지 읽음
  - 못 읽은 칸은 null 로 받음 (지어내지 않게)
  - 프레임마다 '영상 몇 초'인지 같이 저장 → 정답 표와 맞춰보기 쉬움
  - 결과를 JSON 파일로 저장 → match.py 에 바로 넣을 수 있음
  - --game 을 주면 매칭까지 한 번에 돌림

사용 예
  export GEMINI_API_KEY="새로 발급받은 키"
  # 영상 파일이 이미 있을 때
  python scoreboard_read.py --video highlight.mp4 --every 5 --out readings.json \
      --game 20260328HTSK02026.json
  # 유튜브에서 받을 때 (yt-dlp 필요)
  python scoreboard_read.py --url "https://youtu.be/XXXX" --every 5 --out readings.json
"""
import argparse
import json
import os
import subprocess
import sys
import time

MODEL = "gemini-3.8-flash"

PROMPT_V1 = """너는 KBO 야구 중계 화면의 전광판(스코어보드 그래픽)을 읽는 역할이다.
화면에 실제로 보이는 것만 읽어라. 보이지 않거나 확실하지 않은 칸은 반드시 null 로 둬라. 추측 금지.

- teams: 전광판에 적힌 두 팀 이름(약칭 그대로)과 점수. 전광판에 위/왼쪽에 있는 팀을 먼저.
- inning: 이닝 숫자 (예: 5)
- half: 초면 "top", 말이면 "bottom" (▲ = 초, ▼ = 말)
- outs: 아웃 수 0~2 (아웃 표시 불이 몇 개 켜졌는지)
- bases: [1루, 2루, 3루] 에 주자가 있으면 true. 다이아몬드 그림이 안 보이면 null
- balls, strikes: 볼·스트라이크 카운트
- batter: 화면에 타자 이름 자막이 있으면 그 이름, 없으면 null
- is_scoreboard_visible: 전광판 그래픽이 화면에 있으면 true
- is_replay: 리플레이/느린 화면으로 보이면 true
"""

# v2: v1 오류 분석 결과 반영 (타자 줄을 못 읽음, 다이아몬드 루 위치를 헷갈림)
PROMPT_V2 = """너는 KBO 야구 중계 화면의 전광판(스코어보드 그래픽)을 읽는 역할이다.
화면에 실제로 보이는 것만 읽어라. 보이지 않거나 확실하지 않은 칸은 반드시 null 로 둬라. 추측 금지.

[전광판 구조] 보통 화면 왼쪽 위에 있는 작은 박스다.
- 왼쪽 팀 칸: 원정팀 이름과 점수 / 오른쪽 팀 칸: 홈팀 이름과 점수
- 가운데 위: 작은 마름모 3개 = 베이스. 위치로 루를 판단한다.
    오른쪽 아래 마름모 = 1루, 맨 위 마름모 = 2루, 왼쪽 아래 마름모 = 3루
    노란색(색칠된) 마름모 = 주자 있음, 흰색/빈 마름모 = 주자 없음
- 가운데: 숫자와 화살표 = 이닝. ▲ 는 초(top), ▼ 는 말(bottom)
- 그 아래 "숫자-숫자" = 볼-스트라이크 카운트 (앞이 볼, 뒤가 스트라이크)
- 카운트 옆 작은 동그라미 2개 = 아웃. 빨간색으로 켜진 동그라미 개수가 아웃 수 (0~2)
- 아래 줄 "P 이름" = 투수. 이건 타자가 아니다
- 아래 줄 "숫자. 이름  N타수 N안타" 형태 = 현재 타자. 앞의 숫자(타순)는 빼고 이름만 batter 에 넣어라
- 타자 줄이 없으면 batter 는 null

[읽을 항목]
- is_scoreboard_visible: 위 전광판 박스가 화면에 있으면 true (점수만 나오는 큰 자막은 false)
- teams: [왼쪽 팀, 오른쪽 팀] 순서로 이름(약칭 그대로)과 점수
- inning, half, outs, bases([1루, 2루, 3루]), balls, strikes, batter
- is_replay: 리플레이/느린 화면으로 보이면 true
"""

# v3: 시연용 경기(MBC SPORTS+)에서 발견한 오류 반영
#  - 방송사마다 중계표 모양이 다름 (왼쪽 위 박스 / 화면 아래 가로 띠)
#  - 중계표에 타자 이름이 없는데 화면 속 선수를 보고 타자 이름을 지어냄
PROMPT_V3 = """너는 KBO 야구 중계 화면의 중계표(스코어보드 그래픽)를 읽는 역할이다.
화면에 글자나 그림으로 실제로 보이는 것만 읽어라. 보이지 않거나 확실하지 않은 칸은 반드시 null 로 둬라. 추측 금지.

[중계표 모양] 방송사마다 다르다. 둘 중 하나인 경우가 많다.
(A) 화면 왼쪽 위 박스: 팀 이름과 점수가 양옆에 있고, 가운데에 베이스 마름모와 이닝, 그 아래 카운트와 아웃,
    맨 아래 줄에 "P 이름"(투수)과 "숫자. 이름 N타수 N안타"(현재 타자)가 있다.
(B) 화면 아래 가로 띠: "4▼  NC 2 ◇ 0 LG  0-0 ●  P48" 처럼 이닝, 팀과 점수, 베이스 마름모, 카운트, 아웃 점,
    투구 수가 한 줄로 이어진다. 이 모양은 타자 이름이 없는 경우가 많다.

[공통 규칙]
- 이닝: 숫자 옆 ▲ 는 초(top), ▼ 는 말(bottom)
- 베이스 마름모 3개: 오른쪽 = 1루, 위 = 2루, 왼쪽 = 3루. 색칠된(노란색 등) 마름모 = 주자 있음
- "숫자-숫자" = 볼-스트라이크 카운트 (앞이 볼)
- 아웃: 켜진(빨간색 등) 점의 개수 (0~2)
- teams: 중계표에 적힌 순서대로 [먼저 나온 팀, 나중 팀] 이름(약칭 그대로)과 점수
- 점수만 크게 나오는 득점 자막, 경기 시작/종료 그래픽은 중계표가 아니다 (is_scoreboard_visible=false)

[타자 이름 — 가장 중요]
- batter 는 중계표 안에 "숫자. 이름" 처럼 현재 타자로 글자가 적혀 있을 때만 그 이름을 넣는다.
- 화면에 보이는 선수의 얼굴, 유니폼 이름, 등번호, "1루주자 OOO" 같은 주자 자막, 해설 자막으로 타자를 추측하지 마라.
- "P 이름" 은 투수다. 타자가 아니다.
- 중계표에 타자 줄이 없으면 batter 는 null, batter_in_scoreboard 는 false.
"""

PROMPTS = {"v1": PROMPT_V1, "v2": PROMPT_V2, "v3": PROMPT_V3}
PROMPT = PROMPT_V1

SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "is_scoreboard_visible": {"type": "BOOLEAN"},
        "is_replay": {"type": "BOOLEAN", "nullable": True},
        "teams": {
            "type": "ARRAY", "nullable": True,
            "items": {"type": "OBJECT", "properties": {
                "name": {"type": "STRING"},
                "score": {"type": "INTEGER", "nullable": True}},
                "required": ["name", "score"]},
        },
        "inning": {"type": "INTEGER", "nullable": True},
        "half": {"type": "STRING", "enum": ["top", "bottom"], "nullable": True},
        "outs": {"type": "INTEGER", "nullable": True},
        "bases": {"type": "ARRAY", "items": {"type": "BOOLEAN"}, "nullable": True},
        "balls": {"type": "INTEGER", "nullable": True},
        "strikes": {"type": "INTEGER", "nullable": True},
        "batter": {"type": "STRING", "nullable": True},
        "batter_in_scoreboard": {"type": "BOOLEAN", "nullable": True},
    },
    "required": ["is_scoreboard_visible", "teams", "inning", "half", "outs",
                 "bases", "balls", "strikes", "batter", "is_replay"],
}

# 전광판 약칭 → 문자중계 팀 이름. 필요하면 추가
TEAM_ALIAS = {
    "KIA": ["KIA", "기아", "KIA타이거즈", "타이거즈"],
    "SSG": ["SSG", "랜더스", "SSG랜더스"],
    "LG": ["LG", "엘지", "트윈스"],
    "두산": ["두산", "DOOSAN", "베어스"],
    "삼성": ["삼성", "SAMSUNG", "라이온즈"],
    "롯데": ["롯데", "LOTTE", "자이언츠"],
    "한화": ["한화", "HANWHA", "이글스"],
    "NC": ["NC", "다이노스"],
    "KT": ["KT", "위즈"],
    "키움": ["키움", "KIWOOM", "히어로즈"],
}


# ---------------------------------------------------------------- 영상

def download(url, out_base="highlight"):
    out = f"{out_base}.mp4"
    if not os.path.exists(out):
        subprocess.run(["yt-dlp", "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]",
                        "--merge-output-format", "mp4", "-o", out, url], check=True)
    return out


def grab_frames(video, every_sec, start_sec=0, end_sec=None, out_dir="frames"):
    import cv2
    os.makedirs(out_dir, exist_ok=True)
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps
    end_sec = min(end_sec or total, total)
    frames, t = [], float(start_sec)
    while t < end_sec:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            break
        path = os.path.join(out_dir, f"t{int(t):05d}.jpg")
        cv2.imwrite(path, frame)
        frames.append({"time_sec": round(t, 1), "frame": path})
        t += every_sec
    cap.release()
    print(f"프레임 {len(frames)}장 추출 (영상 {total:.0f}초, {every_sec}초 간격)")
    return frames


# ---------------------------------------------------------------- Gemini

def read_frame(client, path, prompt=None, max_retries=4):
    from google.genai import types
    from PIL import Image
    img = Image.open(path)
    config = types.GenerateContentConfig(
        response_mime_type="application/json", response_schema=SCHEMA, temperature=0.1,
        thinking_config=types.ThinkingConfig(thinking_level="low"))
    for attempt in range(max_retries):
        try:
            resp = client.models.generate_content(model=MODEL, contents=[img, prompt or PROMPT], config=config)
            return json.loads(resp.text)
        except Exception as e:
            msg = str(e)
            if "401" in msg or "403" in msg or "API key not valid" in msg:
                sys.exit("API 키가 틀렸거나 삭제된 키임. export GEMINI_API_KEY=\"새 키\" 로 다시 설정하고 실행하면 이어서 함")
            if "PerDay" in msg:
                sys.exit("하루 사용량 초과. 내일 다시 실행하면 이어서 함 (이미 읽은 프레임은 건너뜀)")
            if "429" in msg or "503" in msg:
                wait = 3 * (2 ** attempt)
                print(f"  서버 혼잡, {wait}초 후 재시도 ({attempt + 1}/{max_retries})")
                time.sleep(wait)
                continue
            print(f"  에러: {msg[:200]}")
            return None
    return None


# ---------------------------------------------------------------- match.py 형식으로 변환

def team_key(name):
    n = (name or "").replace(" ", "").upper()
    for key, aliases in TEAM_ALIAS.items():
        if any(a.upper() in n or n in a.upper() for a in aliases if n):
            return key
    return None


def to_reading(raw, away, home):
    """Gemini 출력 → match.py 입력. 팀 이름으로 원정/홈 점수를 구분함."""
    r = {"inning": None, "half": None, "outs": None, "bases": None,
         "score_away": None, "score_home": None, "balls": None, "strikes": None,
         "batter": None, "is_replay": None}
    if not raw or not raw.get("is_scoreboard_visible"):
        return r
    for k in ("inning", "half", "outs", "balls", "strikes", "batter", "is_replay"):
        r[k] = raw.get(k)
    # v3: 중계표 안에 타자 줄이 없다고 답했으면 타자 이름은 버림 (화면 보고 지어낸 이름 방지)
    if raw.get("batter_in_scoreboard") is False:
        r["batter"] = None
    b = raw.get("bases")
    r["bases"] = b if isinstance(b, list) and len(b) == 3 else None
    for t in raw.get("teams") or []:
        key = team_key(t.get("name"))
        if key == away:
            r["score_away"] = t.get("score")
        elif key == home:
            r["score_home"] = t.get("score")
    # 범위 밖 값은 오인식으로 보고 버림
    if r["outs"] is not None and not 0 <= r["outs"] <= 2:
        r["outs"] = None
    if r["inning"] is not None and not 1 <= r["inning"] <= 12:
        r["inning"] = None
    return r


# ---------------------------------------------------------------- 실행

def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--video")
    src.add_argument("--url")
    ap.add_argument("--every", type=float, default=5, help="몇 초마다 프레임을 뽑을지")
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--out", default="readings.json")
    ap.add_argument("--game", help="경기 상태 파일(b2-state-v1). 주면 매칭까지 함")
    ap.add_argument("--prompt", choices=list(PROMPTS), default="v1", help="전광판 읽기 프롬프트 버전")
    ap.add_argument("--away", help="--game 없이 돌릴 때 원정팀 (예: KIA)")
    ap.add_argument("--home", help="--game 없이 돌릴 때 홈팀 (예: SSG)")
    args = ap.parse_args()

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY 환경변수가 없음. export GEMINI_API_KEY=... 먼저 실행")

    away, home = args.away, args.home
    if args.game:
        summ = json.load(open(args.game, encoding="utf-8"))["summary"]
        away, home = summ["away"], summ["home"]
    if not (away and home):
        sys.exit("--game 또는 --away/--home 이 필요함 (점수를 원정/홈으로 나누려고)")

    video = args.video or download(args.url)
    frames = grab_frames(video, args.every, args.start, args.end)

    # 이미 읽은 프레임은 다시 안 읽음 (중간에 끊겨도 이어서 가능)
    done = {}
    if os.path.exists(args.out):
        # 읽기에 실패했던 프레임(raw 가 비어 있음)은 다시 읽음
        done = {r["frame"]: r for r in json.load(open(args.out, encoding="utf-8"))
                if r.get("raw") is not None}

    from google import genai
    client = genai.Client(api_key=key)
    results = []
    for f in frames:
        if f["frame"] in done:
            results.append(done[f["frame"]])
            continue
        raw = read_frame(client, f["frame"], PROMPTS[args.prompt])
        rec = {**f, **to_reading(raw, away, home), "raw": raw, "prompt": args.prompt}
        results.append(rec)
        json.dump(results, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f'{f["time_sec"]:>6}s  {rec["inning"]}회 {rec["half"]}  {rec["outs"]}사  '
              f'주자 {rec["bases"]}  {away} {rec["score_away"]} : {home} {rec["score_home"]}  '
              f'타자 {rec["batter"]}  리플레이 {rec["is_replay"]}')
        time.sleep(1)

    json.dump(results, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n저장: {args.out}")

    if args.game:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import match
        matched = match.run(args.game, results)
        mout = args.out.replace(".json", "_matched.json")
        json.dump(matched, open(mout, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        n_ok = sum(1 for m in matched if m["status"] == "확정")
        print(f"매칭: {len(matched)}장 중 확정 {n_ok}장 → {mout}")
        for m in matched:
            rd = m["reading"]
            who = m["candidates"][0]["batter"] if m["status"] == "확정" else "-"
            conf = m.get("confidence", "")
            print(f'{rd["time_sec"]:>6}s  {m["status"]:<5}  {who:<6}  {conf:<2}  {m["reason"]}')


if __name__ == "__main__":
    main()