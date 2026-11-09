"""사용량 리포트 + 전체 실험 비용 추정 + 유료 전환 판단.

  python estimate_cost.py                       # 로그 없으면 기본 가정으로 계산
  python estimate_cost.py --free-rpd 250 --days-left 10
  python estimate_cost.py --video-krw 18 --video-calls 30

먼저 generate.py --limit 3 으로 실제 호출을 몇 번 해두면, 그 로그의 평균 토큰으로 계산함.
"""
import argparse
import json
import math
from collections import Counter, defaultdict

import config

# 로그가 없을 때 쓰는 문항당 토큰 가정 (입력, 출력+thinking)
DEFAULT_TOKENS = {"B0": (2500, 400), "B1": (3000, 400), "B2": (4000, 450)}


def read_log():
    if not config.USAGE_LOG.exists():
        return []
    return [json.loads(l) for l in open(config.USAGE_LOG, encoding="utf-8") if l.strip()]


def report(rows):
    st = Counter(r["status"] for r in rows)
    real = [r for r in rows if r["status"] == "ok" and not r.get("cache_hit")]
    cost = sum(r.get("cost_usd", 0) for r in real)
    print("── 지금까지 사용량 ──")
    print(f"실제 호출 성공 {len(real)}회, 캐시 히트 {sum(1 for r in rows if r.get('cache_hit'))}회")
    print("재시도/오류:", {k: v for k, v in st.items() if k != "ok"} or "없음")
    print(f"누적 비용(유료 단가 환산): ${cost:.4f} ≈ {cost * config.KRW_PER_USD:,.0f}원\n")
    per = defaultdict(list)
    for r in real:
        per[r["condition"]].append((r["prompt_tokens"], r["output_tokens"] + r.get("thoughts_tokens", 0)))
    return {c: (sum(a for a, _ in v) / len(v), sum(b for _, b in v) / len(v)) for c, v in per.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-questions", type=int, default=30)
    ap.add_argument("--rerun-factor", type=float, default=3.0,
                    help="프롬프트 수정 등으로 전체를 몇 번 다시 돌릴지 (여유분)")
    ap.add_argument("--video-calls", type=int, default=30, help="하이라이트 연결용 영상 호출 수")
    ap.add_argument("--video-krw", type=float, default=18.0, help="영상 1분·프레임 5장 호출 1회 실측 비용")
    ap.add_argument("--free-rpd", type=int, default=0, help="AI Studio에 뜨는 무료 하루 요청 한도 (모델별)")
    ap.add_argument("--days-left", type=int, default=7, help="생성 끝내야 하는 날까지 남은 날")
    ap.add_argument("--model", default=config.MODEL)
    args = ap.parse_args()

    measured = report(read_log())
    p = config.PRICES.get(args.model, {"in": 0, "out": 0})
    print(f"── 전체 실험 추정 ({args.model}: 입력 ${p['in']}/1M, 출력 ${p['out']}/1M) ──")
    total_usd, llm_calls = 0.0, 0
    for c in ["B0", "B1", "B2"]:  # B3는 B2 재사용, R은 LLM 없음
        tin, tout = measured.get(c, DEFAULT_TOKENS[c])
        src = "실측" if c in measured else "가정"
        one = tin / 1e6 * p["in"] + tout / 1e6 * p["out"]
        n = args.n_questions
        total_usd += one * n
        llm_calls += n
        print(f"{c}: 입력 {tin:,.0f} / 출력 {tout:,.0f} 토큰({src}) → 1회 {one * config.KRW_PER_USD:.1f}원 × {n}")
    text_krw = total_usd * config.KRW_PER_USD
    video_krw = args.video_calls * args.video_krw
    once = text_krw + video_krw
    total = once * args.rerun_factor
    total_calls = math.ceil((llm_calls + args.video_calls) * args.rerun_factor)
    print(f"\n해설 생성 1회분: {text_krw:,.0f}원  (호출 {llm_calls}회)")
    print(f"영상 연결 1회분: {video_krw:,.0f}원  (호출 {args.video_calls}회 × {args.video_krw:g}원)")
    print(f"재실행 여유 ×{args.rerun_factor:g} 포함 총: {total:,.0f}원, 총 호출 약 {total_calls}회")

    print("\n── 유료 전환 판단 ──")
    if args.free_rpd:
        days = math.ceil(total_calls / args.free_rpd)
        print(f"무료 한도 {args.free_rpd}회/일이면 {days}일 걸림 (남은 기간 {args.days_left}일)")
        if days > args.days_left:
            print("→ 무료로는 기간 안에 못 끝냄. 유료 전환 권장.")
        else:
            print("→ 기간상으론 무료로 가능. 503(과부하)이 잦으면 그때 전환해도 늦지 않음.")
    else:
        print("--free-rpd 를 넣으면 무료로 며칠 걸리는지 계산함 (AI Studio > Usage/Rate limit 에서 확인)")
    print(f"참고: 총 예상 {total:,.0f}원이라 유료로 가도 부담은 작음. "
          "Cloud 결제에 예산 알림을 걸어두고, 실험 중엔 모델을 바꾸지 말 것.")


if __name__ == "__main__":
    main()
