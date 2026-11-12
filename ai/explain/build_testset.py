"""BE 상태 복원 결과(backend/game/restore_state.py 출력)로 테스트셋을 반자동으로 만듦.

사람이 하는 일: 장면 고르기(play_id), 질문 쓰기, 카드 id 고르기 → data/picks.csv
자동으로 채우는 것: raw_relay(앞뒤 문자중계), facts(이닝·아웃·주자·점수 전/후), players

1) 장면 찾기: 경기 하나의 행을 play_id와 상태랑 같이 보여줌
   python build_testset.py list --restored ../../data/raw/b2_state_v2_all --game 경기ID --inning 7

2) picks.csv 채우기 (data/picks_template.csv 복사). 엑셀·구글시트로 편집해도 됨

3) 테스트셋 생성 → 형식 검사
   python build_testset.py build --restored ../../data/raw/b2_state_v2_all --picks data/picks.csv --out data/testset.jsonl
   python check_testset.py data/testset.jsonl --cards ../../cards
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

HALF = {"top": "초", "bottom": "말"}
NAME_PATTERNS = [
    re.compile(r"^\s*[123]루주자\s*([^:]+?)\s*:"),
    re.compile(r"^\s*타자주자\s*([^:]+?)\s*:"),
    re.compile(r"^\s*\d+번타자\s*(\S+)"),
    re.compile(r"대주자\s*(\S+)"),
    re.compile(r"대타\s*([가-힣A-Za-z]{2,10})"),
    re.compile(r"^\s*([가-힣A-Za-z]{2,10})\s*:"),
    re.compile(r"투수\s+([가-힣A-Za-z]{2,10})\s*:\s*투수\s+([가-힣A-Za-z]{2,10})"),  # 투수 A : 투수 B (으)로 교체
]
NOT_NAMES = {"아웃", "세이프", "땅볼", "루수", "유격수", "투수", "포수", "타자", "주자", "투수판", "대타", "대주자"}
RUNNER_LINE = re.compile(r"^\s*(?:[123]루주자|타자주자)")


PITCH_RE = re.compile(r"^\s*\d+구")
BENIGN_NOTES = {"base_shared_temporarily"}   # 한 플레이가 여러 줄로 나뉠 때 생기는 정상 상태


def short_id(pid):
    return pid.rsplit(":", 1)[-1][:8]


def find_row(rows, ref):
    """play_id 전체 또는 앞 8글자(짧은 id)로 행 찾기."""
    ref = ref.strip()
    hits = [i for i, r in enumerate(rows) if r["play_id"] == ref or short_id(r["play_id"]).startswith(ref)]
    if len(hits) > 1:
        raise ValueError(f"짧은 id '{ref}'에 해당하는 행이 {len(hits)}개. 글자를 더 길게 쓸 것")
    return hits[0] if hits else None


def is_pitch(row):
    return bool(PITCH_RE.match(row.get("description") or ""))


def real_notes(row):
    return [n for n in row.get("notes") or [] if n not in BENIGN_NOTES]


def load_game(restored, gid):
    f = Path(restored) / "games" / f"{gid}.json"
    if not f.exists():
        sys.exit(f"[오류] {f} 없음. restore_state.py를 --game {gid} 로 먼저 돌렸는지 확인")
    return json.loads(f.read_text(encoding="utf-8"))


def outs_text(n):
    return {0: "무사", 1: "1사", 2: "2사"}.get(n, f"{n}아웃")


def state_text(s):
    r = s["runners"]
    occ = [b for b in ("1", "2", "3") if r.get(b)]
    if not occ:
        base = "주자 없음"
    elif len(occ) == 3:
        base = "만루 (" + ", ".join(f"{b}루 {r[b]}" for b in occ) + ")"
    else:
        base = ",".join(occ) + "루 (" + ", ".join(f"{b}루 {r[b]}" for b in occ) + ")"
    return f"{outs_text(s['outs'])} {base}"


def score_text(s, away, home):
    return f"점수 {away} {s['score']['away']} : {s['score']['home']} {home}"


def collect_players(rows):
    names = set()
    for row in rows:
        d = row.get("description") or ""
        for pat in NAME_PATTERNS:
            for m in pat.finditer(d):
                for n in m.groups():
                    n = (n or "").strip()
                    if 2 <= len(n) <= 10 and n not in NOT_NAMES and not re.search(r"\d|교체|공격|루주자|루수", n):
                        names.add(n)
        for key in ("state_before", "state_after"):
            for v in (row.get(key) or {}).get("runners", {}).values():
                if v:
                    names.add(v)
    return sorted(names)


def cmd_list(args):
    g = load_game(args.restored, args.game)
    s = g["summary"]
    print(f"{s['game_id']}  {s['away']}(원정) vs {s['home']}(홈)  최종점수 일치: {s.get('final_score_match')}")
    for row in g["rows"]:
        if args.inning and row.get("inning") != args.inning:
            continue
        flag = ""
        nm = row.get("naver_match")
        if nm and not all(nm.values()):
            flag = "  ⚠네이버 상태 불일치"
        if real_notes(row):
            flag += f"  ⚠{','.join(real_notes(row))}"
        if args.no_pitches and is_pitch(row):
            continue
        sb = row["state_before"]
        st = f"{state_text(sb)} | {sb['score']['away']}:{sb['score']['home']}"
        print(f"{short_id(row['play_id'])}  {row.get('inning')}{HALF.get(row.get('inning_half'), '')}  [{st}]  "
              f"{row.get('description')}{flag}")


def build_item(pick, g, before_n, after_n):
    rows = g["rows"]
    s = g["summary"]
    idx = find_row(rows, pick["play_id"])
    if idx is None:
        raise ValueError(f"{pick['qid']}: play_id {pick['play_id']}가 {s['game_id']}에 없음")
    tgt = rows[idx]
    half = (tgt.get("inning"), tgt.get("inning_half"))
    same = lambda r: (r.get("inning"), r.get("inning_half")) == half

    # 앞쪽: 같은 반이닝에서 투구 줄이 아닌 줄 before_n개. 투구 줄은 지금 타석 것만 남김
    in_current_pa, n, before = True, 0, []
    for r in reversed(rows[:idx]):
        if not same(r):
            break
        if is_pitch(r):
            if in_current_pa:
                before.append(r)
            continue
        if n >= before_n:
            break
        before.append(r)
        n += 1
        if r["event_type"] == "batter_announcement":
            in_current_pa = False
    # 뒤쪽: 같은 플레이의 이어지는 주자 줄(진루·홈인·아웃)은 전부, 그다음 투구 줄 빼고 after_n개
    after_rows, j = [], idx + 1
    while j < len(rows) and same(rows[j]) and RUNNER_LINE.match(rows[j].get("description") or ""):
        after_rows.append(rows[j])
        j += 1
    cont_end = j            # 이어지는 주자 줄이 끝나는 위치
    n = 0
    while j < len(rows) and same(rows[j]) and n < after_n:
        if not is_pitch(rows[j]):
            after_rows.append(rows[j])
            n += 1
        j += 1
    window = list(reversed(before)) + [tgt] + after_rows

    # 플레이가 여러 줄로 나뉘므로 '플레이 후'는 바로 이어지는 주자 줄까지 반영한 상태로 잡음
    after = rows[cont_end - 1]["state_after"]

    inning = f"{tgt.get('inning')}회{HALF.get(tgt.get('inning_half'), '')}"
    before = tgt["state_before"]
    facts = [
        {"id": "F1", "text": f"{inning}, {state_text(before)}, {score_text(before, s['away'], s['home'])}"},
        {"id": "F2", "text": f"이번 플레이: {tgt.get('description')}"},
        {"id": "F3", "text": f"플레이 후: {state_text(after)}, {score_text(after, s['away'], s['home'])}"},
    ]
    for extra in filter(None, (pick.get("extra_facts") or "").split("|")):
        facts.append({"id": f"F{len(facts) + 1}", "text": extra.strip()})

    warn = []
    for r in window:
        nm = r.get("naver_match")
        if nm and not all(nm.values()):
            warn.append(f"{short_id(r['play_id'])} 네이버 상태와 불일치")
        if real_notes(r):
            warn.append(f"{short_id(r['play_id'])} {','.join(real_notes(r))}")

    split = lambda v: [x.strip() for x in (v or "").split("|") if x.strip()]
    item = {
        "qid": pick["qid"], "type": pick["type"], "tags": split(pick.get("tags")),
        "game_id": s["game_id"], "play_id": tgt["play_id"],
        "question": pick["question"].strip(),
        "raw_relay": [r["description"] for r in window if (r.get("description") or "").strip()],
        "facts": facts, "card_ids": split(pick.get("card_ids")),
        "players": collect_players(rows),
    }
    return item, warn


def cmd_build(args):
    with open(args.picks, encoding="utf-8-sig") as f:
        picks = [p for p in csv.DictReader(f) if (p.get("qid") or "").strip()]
    games, items, n_warn = {}, [], 0
    for p in picks:
        gid = p["game_id"].strip()
        games.setdefault(gid, load_game(args.restored, gid))
        item, warn = build_item(p, games[gid], args.before, args.after)
        items.append(item)
        for w in warn:
            n_warn += 1
            print(f"[주의] {p['qid']}: {w} → F가 틀렸을 수 있음. 직접 확인하거나 다른 장면으로")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(f"\n{len(items)}문항 → {args.out} (주의 {n_warn}건)")
    print(f"다음: python check_testset.py {args.out} --cards ../../cards")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("list", help="경기 행 목록 보기 (play_id 찾기)")
    a.add_argument("--restored", required=True)
    a.add_argument("--game", required=True)
    a.add_argument("--inning", type=int, default=0)
    a.add_argument("--no-pitches", action="store_true", help="'1구 볼' 같은 투구 줄 숨기기")
    b = sub.add_parser("build", help="picks.csv → testset.jsonl")
    b.add_argument("--restored", required=True)
    b.add_argument("--picks", required=True)
    b.add_argument("--out", default="data/testset.jsonl")
    b.add_argument("--before", type=int, default=6, help="장면 앞 문자중계 줄 수 (투구 줄 제외, 같은 반이닝 안)")
    b.add_argument("--after", type=int, default=1, help="이어지는 주자 줄 다음에 더 붙일 문자중계 줄 수 (투구 줄 제외)")
    args = ap.parse_args()
    cmd_list(args) if args.cmd == "list" else cmd_build(args)


if __name__ == "__main__":
    main()
