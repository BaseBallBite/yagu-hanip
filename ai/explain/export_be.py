"""
해설 생성 결과 → 백엔드용 JSON

문장마다 근거 ID(cited_ids)와 그 근거의 실제 문장(cited_text)을 붙임.
  R번호  → 문자중계 원문 (테스트셋 raw_relay, 1부터 셈)
  F번호  → 정리된 경기 사실 (테스트셋 facts)
  카드 id → 카드 제목 + 한 줄 설명
  UNKNOWN → 기록에 근거 없음

사용법 (ai/explain 안에서)
  python export_be.py --testset data/testset_highlight.jsonl \
      --generations outputs/highlight_v2/generations.jsonl --cards ../../cards \
      --display B3 --scenes ../highlight/output/scenes_20261007OBLG02026.json \
      --out outputs/highlight_v2/be_highlight_20261007OBLG02026.json
"""
import argparse
import json

UNKNOWN_TEXT = "기록에 근거 없음 (확인할 수 없는 내용)"


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def card_text(card):
    title = card.get("title", "")
    one = (card.get("one_liner") or "").strip()
    return f"[{title}] {one}".strip()


def build_pool(item, cards):
    pool = {f"R{i + 1}": t for i, t in enumerate(item.get("raw_relay", []))}
    pool.update({f["id"]: f["text"] for f in item.get("facts", [])})
    for cid in item.get("card_ids", []):
        if cid in cards:
            pool[cid] = card_text(cards[cid])
    return pool


def convert_sentences(sents, pool):
    out = []
    for s in sents:
        ids = s.get("evidence", []) or []
        out.append({
            "text": s["text"],
            "cited_ids": ids,
            "cited_text": [{"id": i, "text": UNKNOWN_TEXT if i == "UNKNOWN" else pool.get(i, "(근거를 찾을 수 없음)")}
                           for i in ids],
            **({"verdict": s["verdict"]} if "verdict" in s else {}),
        })
    return out


def find_scene(scenes_path, play_id):
    if not scenes_path:
        return None
    d = json.load(open(scenes_path, encoding="utf-8"))
    hits = [s for s in d["scenes"] if s.get("play_id") == play_id]
    if not hits:
        return {"video_id": d.get("video_id"), "segments": []}
    return {"video_id": d.get("video_id"),
            "segments": [{"start": s["start"], "end": s["end"], "status": s["status"]} for s in hits]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--testset", required=True)
    ap.add_argument("--generations", required=True)
    ap.add_argument("--cards", required=True, help="카드 폴더 (예: ../../cards)")
    ap.add_argument("--display", default="B3", help="화면에 기본으로 보여줄 조건")
    ap.add_argument("--scenes", default=None, help="하이라이트 장면 표 (있으면 영상 구간도 붙임)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from prompts import load_cards
    cards = load_cards(args.cards)
    items = {x["qid"]: x for x in load_jsonl(args.testset)}
    gens = load_jsonl(args.generations)

    by_play = {}
    for qid, item in items.items():
        pool = build_pool(item, cards)
        answers = {}
        for g in gens:
            if g["qid"] != qid:
                continue
            answers[g["condition"]] = {
                "sentences": convert_sentences(g["sentences"], pool),
                "dropped": convert_sentences(g.get("dropped", []), pool),
                "verifier": (g.get("meta") or {}).get("from"),
            }
        q = {"qid": qid, "question": item["question"], "tags": item.get("tags", []),
             "display_condition": args.display, "answers": answers}
        pid = item["play_id"]
        if pid not in by_play:
            by_play[pid] = {"game_id": item["game_id"], "play_id": pid,
                            "play_id_short": pid.split(":")[-1][:8],
                            "scene": find_scene(args.scenes, pid), "questions": []}
        by_play[pid]["questions"].append(q)

    result = list(by_play.values())
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result if len(result) > 1 else result[0], f, ensure_ascii=False, indent=1)

    for p in result:
        print(f'{p["game_id"]} {p["play_id_short"]}  질문 {len(p["questions"])}개'
              + (f'  영상 구간 {len(p["scene"]["segments"])}개' if p.get("scene") else ""))
        for q in p["questions"]:
            a = q["answers"].get(args.display, {})
            print(f'  {q["qid"]} [{args.display}] 문장 {len(a.get("sentences", []))}개 / 삭제 {len(a.get("dropped", []))}개  {q["question"]}')
    print(f"저장: {args.out}")


if __name__ == "__main__":
    main()