"""테스트셋 형식 검사. API 안 쓰고 돈도 안 나감. 생성 돌리기 전에 먼저 실행.

  python check_testset.py data/testset.jsonl --cards ../../cards
"""
import argparse
import json
import sys
from collections import Counter

from prompts import load_cards

REQUIRED = ["qid", "type", "question", "raw_relay", "card_ids", "players"]
TYPES = {"규칙", "상황", "기술"}
TAGS = {"복합상황", "지연·누락기록", "모호한규칙"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("testset")
    ap.add_argument("--cards", default="../../cards")
    args = ap.parse_args()

    cards = load_cards(args.cards)
    errors, warns, items = [], [], []
    for n, line in enumerate(open(args.testset, encoding="utf-8"), 1):
        if not line.strip():
            continue
        try:
            items.append((n, json.loads(line)))
        except json.JSONDecodeError as e:
            errors.append(f"{n}번째 줄: JSON 형식 오류 ({e.msg}). 따옴표·쉼표·괄호 확인")

    qids = Counter(it.get("qid") for _, it in items)
    for n, it in items:
        q = it.get("qid", f"{n}번째 줄")
        for k in REQUIRED:
            if k not in it or it[k] in ("", [], None):
                errors.append(f"{q}: '{k}' 칸이 비어 있음")
        if qids[it.get("qid")] > 1:
            errors.append(f"{q}: qid 중복")
        if it.get("type") and it["type"] not in TYPES:
            errors.append(f"{q}: type은 {sorted(TYPES)} 중 하나여야 함 (지금: {it['type']})")
        for t in it.get("tags", []):
            if t not in TAGS:
                warns.append(f"{q}: 모르는 태그 '{t}' (정해둔 태그: {sorted(TAGS)})")
        for cid in it.get("card_ids", []):
            if cid not in cards:
                errors.append(f"{q}: 카드 '{cid}'가 cards 폴더에 없음")
            elif cards[cid].get("review_status") != "reviewed":
                warns.append(f"{q}: 카드 '{cid}' 아직 검수 전(draft)")
        fids = [f.get("id") for f in it.get("facts", []) if isinstance(f, dict)]
        if len(fids) != len(set(fids)):
            errors.append(f"{q}: facts 안에 같은 id가 두 번 있음")
        if not it.get("facts"):
            warns.append(f"{q}: facts가 비어 있음 → B1·B2가 B0과 거의 같아짐")

    types = Counter(it.get("type") for _, it in items)
    tags = Counter(t for _, it in items for t in it.get("tags", []))
    games = Counter(it.get("game_id") for _, it in items)
    print(f"문항 {len(items)}개 | 유형 {dict(types)} | 태그 {dict(tags)} | 경기 {len(games)}개")
    for w in warns:
        print("[주의]", w)
    for e in errors:
        print("[오류]", e)
    if errors:
        sys.exit(f"\n오류 {len(errors)}개. 고친 다음 다시 검사할 것")
    print("\n형식 통과. generate.py 돌려도 됨")


if __name__ == "__main__":
    main()
