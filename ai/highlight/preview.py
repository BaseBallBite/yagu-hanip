"""
시연 리허설용: 장면 표에서 보여주기 좋은 장면을 골라 상황 카드처럼 출력

사용법
  python preview.py output/scenes_20261007OBLG02026.json          # 추천 장면만
  python preview.py output/scenes_20261007OBLG02026.json --all    # 확정·추정 전부 한 줄씩
  python preview.py output/scenes_20261007OBLG02026.json --at 7:35  # 특정 시간 카드

추천 기준
  만루, 주자 2명 이상, 이번 이닝 앞선 득점 있음, 9회 이후, 마지막 확정 장면
"""
import argparse
import json

HALF = {"초": "초", "말": "말", "top": "초", "bottom": "말"}


def mmss(t):
    t = int(t)
    return f"{t // 60}:{t % 60:02d}"


def parse_time(s):
    if ":" in s:
        m, sec = s.split(":")
        return int(m) * 60 + int(sec)
    return float(s)


def bases_text(b):
    names = [f"{i + 1}루" for i, on in enumerate(b) if on]
    if len(names) == 3:
        return "만루"
    return "·".join(names) if names else "주자 없음"


def card(s, away, home):
    sit = s["situation"]
    head = f'{s["inning"]}회{HALF.get(s["half"], s["half"])} · {sit["outs"]}사 · {bases_text(sit["bases"])} · {away} {sit["score_away"]} : {sit["score_home"]} {home}'
    tag = " [추정]" if s["status"] == "추정" else ""
    lines = [f'┌ {mmss(s["start"])}~{mmss(s["end"])}{tag}  (신뢰도 {s.get("confidence", "-")})',
             f"│ 📍 {head}"]
    if s.get("prev_play"):
        lines.append(f'│ ⚡ 방금: {s["prev_play"]}')
    lines.append(f'│ 타자 {s["batter"]}')
    for r in s["restore"][1:]:
        if r.startswith(("타자:", "이 타석 결과", "타석 후")):
            continue
        lines.append(f"│   {r}")
    if s.get("result"):
        lines.append(f'│ ▶ 이 타석: {s["result"]}')
    if s["status"] == "추정":
        lines.append("│ ※ 전광판이 확인되지 않아 앞 장면을 기준으로 추정한 정보입니다")
    lines.append("└" + "─" * 40)
    return "\n".join(lines)


def interesting(s):
    if s["status"] != "확정":
        return 0
    sit = s["situation"]
    score = 0
    on = sum(sit["bases"])
    score += 3 if on == 3 else (1 if on == 2 else 0)
    score += 2 if any(r.startswith("이번 이닝 앞선 득점") for r in s["restore"]) else 0
    score += 2 if s["inning"] >= 9 else 0
    score += 1 if s.get("confidence") == "높음" else 0
    return score


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--at", default=None, help="이 시간(예: 7:35)의 장면 카드")
    ap.add_argument("--top", type=int, default=6)
    args = ap.parse_args()

    d = json.load(open(args.scenes, encoding="utf-8"))
    away, home, sc = d.get("away", "원정"), d.get("home", "홈"), d["scenes"]
    print(f'{away} vs {home}  (영상 https://youtu.be/{d["video_id"]})\n')

    if args.at:
        t = parse_time(args.at)
        hit = [s for s in sc if s["start"] <= t < s["end"]]
        if not hit:
            print("그 시간 장면 없음")
        elif hit[0]["status"] == "확인 불가":
            print(f"{mmss(hit[0]['start'])}~{mmss(hit[0]['end'])} 확인 불가 → 카드 안 띄움")
        else:
            print(card(hit[0], away, home))
        return

    if args.all:
        for s in sc:
            if s["status"] == "확인 불가":
                continue
            print(f'{mmss(s["start"]):>6}  {s["status"]:<3} {s["inning"]}회{HALF.get(s["half"], s["half"])} '
                  f'{s["batter"]:<6} {bases_text(s["situation"]["bases"])}')
        return

    picks = sorted([s for s in sc if interesting(s) > 0], key=lambda s: -interesting(s))[:args.top - 1]
    last = [s for s in sc if s["status"] == "확정"][-1:]
    for s in sorted({id(x): x for x in picks + last}.values(), key=lambda s: s["start"]):
        print(card(s, away, home))
        print()
    print("→ 위 시간대를 영상에서 틀어서, 카드 내용(이닝·아웃·주자·점수·타자)이 화면과 맞는지 확인")


if __name__ == "__main__":
    main()