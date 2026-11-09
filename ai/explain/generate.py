"""해설 생성 실행 스크립트.

예)
  python generate.py --dry-run --limit 2            # API 안 쓰고 파이프라인만 확인
  python generate.py --limit 3                      # 3문항만 실제 호출 → usage로 단가 측정
  python generate.py                                # 전체 (R, B0, B1, B2, B3)
  python generate.py --conditions B2,B3 --qids Q01,Q07

중간에 끊겨도 다시 돌리면 캐시된 건 건너뛰고 이어서 함 (캐시 히트는 비용 0).
"""
import argparse
import json
import sys
from collections import Counter

import config
from gemini_client import DailyQuotaExceeded, GeminiRunner
from prompts import (SYSTEM_PROMPT, Commentary, build_rule_baseline,
                     build_user_prompt, evidence_pool, load_cards)
from verifier import verify

ALL_CONDITIONS = ["R", "B0", "B1", "B2", "B3"]


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--testset", default=str(config.ROOT / "data/testset_sample.jsonl"))
    ap.add_argument("--cards", default=str(config.ROOT / "data/cards_sample.json"),
                    help="카드 폴더(예: ../cards) 또는 json 파일")
    ap.add_argument("--conditions", default=",".join(ALL_CONDITIONS))
    ap.add_argument("--qids", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--model", default=config.MODEL)
    ap.add_argument("--run-name", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    items = load_jsonl(args.testset)
    if args.qids:
        want = set(args.qids.split(","))
        items = [x for x in items if x["qid"] in want]
    if args.limit:
        items = items[: args.limit]
    cards = load_cards(args.cards)
    used = {cid for it in items for cid in it.get("card_ids", [])}
    missing = sorted(used - set(cards))
    if missing:
        sys.exit(f"[오류] 테스트셋에 있는데 카드 폴더에 없는 카드: {missing}")
    drafts = sorted(c for c in used if cards[c].get("review_status") == "draft")
    if drafts:
        print(f"[주의] 검수 전(draft) 카드 {len(drafts)}장 사용 중: {drafts}")
    conds = [c.strip() for c in args.conditions.split(",") if c.strip()]
    # B3는 B2 출력을 재사용하므로 B3만 요청해도 B2는 생성(또는 캐시에서 읽음)함
    llm_conds = [c for c in ["B0", "B1", "B2"] if c in conds or (c == "B2" and "B3" in conds)]
    runner = GeminiRunner(model=args.model, dry_run=args.dry_run) if llm_conds else None
    run_name = args.run_name or (f"{args.model}_{config.PROMPT_VERSION}" + ("_dry" if args.dry_run else ""))
    out_dir = config.OUT_DIR / run_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "generations.jsonl"

    rows, stats = [], Counter()
    run_cost, stopped = 0.0, False
    try:
        for item in items:
            qid = item["qid"]
            players = item.get("players", [])
            b2_out = None

            if "R" in conds:
                out = build_rule_baseline(item, cards)
                rows.append({"qid": qid, "condition": "R", **out, "meta": {"model": "none"}})

            for cond in llm_conds:
                user = build_user_prompt(item, cards, cond)
                out, meta = runner.generate(SYSTEM_PROMPT, user, Commentary, {"qid": qid, "condition": cond})
                stats["calls"] += 0 if meta["cache_hit"] else 1
                stats["cache_hits"] += 1 if meta["cache_hit"] else 0
                run_cost += 0 if meta["cache_hit"] else meta["cost_usd"]
                if cond == "B2":
                    b2_out = (out, meta)
                if cond in conds:
                    rows.append({"qid": qid, "condition": cond, **out, "meta": meta})

            if "B3" in conds:
                out, meta = b2_out
                pool = evidence_pool(item, cards, "B2")
                v = verify(out, pool, players)
                rows.append({"qid": qid, "condition": "B3", **v,
                             "meta": {**meta, "from": "B2+verifier"}})
            print(f"{qid} 완료")
    except DailyQuotaExceeded as e:
        stopped = True
        print(f"\n[중단] 하루 한도 소진: {e}\n지금까지 결과는 저장됨. 한국시간 오후 4~5시(태평양 자정) 이후 같은 명령으로 이어서 돌리면 됨.")

    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    per_cond = Counter()
    for r in rows:
        per_cond[r["condition"]] += len(r["sentences"])
    print("\n── 요약 ──")
    print(f"저장: {out_path}")
    print(f"새 호출 {stats['calls']}회 / 캐시 {stats['cache_hits']}회")
    print(f"이번 실행 비용: ${run_cost:.4f} ≈ {run_cost * config.KRW_PER_USD:.0f}원 (유료 단가 기준)")
    print("조건별 남은 문장 수:", dict(per_cond))
    sys.exit(2 if stopped else 0)


if __name__ == "__main__":
    main()
