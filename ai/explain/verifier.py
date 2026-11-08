"""B3 검증기 (규칙 기반). 루브릭 5번 결정대로 근거 표시 + 숫자 + 선수 이름 대조.

문장마다:
  1) 근거 표시가 있는지
  2) 붙인 ID가 실제 입력에 있는 ID인지
  3) 문장 속 숫자가 인용한 근거 텍스트에 있는지
  4) 문장 속 선수 이름이 인용한 근거 텍스트에 있는지
하나라도 걸리면 그 문장을 뺌. LLM 판정기나 NLI는 범위 밖.
"""
import re

_COUNT_WORDS = {
    "노아웃": "0아웃", "무사": "0아웃", "원아웃": "1아웃", "투아웃": "2아웃",
    "1사": "1아웃", "2사": "2아웃", "1死": "1아웃", "2死": "2아웃",
}


def _norm(s):
    for k, v in _COUNT_WORDS.items():
        s = s.replace(k, v)
    return s


def _numbers(s):
    return re.findall(r"\d+(?:\.\d+)?", _norm(s))


def _has_number(evidence_text, n):
    return re.search(rf"(?<![\d.]){re.escape(n)}(?![\d])", evidence_text) is not None


def verify_sentence(sent, pool, players):
    text, ev = sent.get("text", ""), sent.get("evidence", []) or []
    nums = _numbers(text)
    names = [p for p in players if p and p in text]

    if not ev:
        return False, "근거 표시 없음"
    if ev == ["UNKNOWN"]:
        if nums or names:
            return False, "UNKNOWN인데 숫자/이름을 말함"
        return True, "확인불가 문장"
    bad = [e for e in ev if e != "UNKNOWN" and e not in pool]
    if bad:
        return False, f"입력에 없는 근거 ID {bad}"

    cited = _norm(" ".join(pool[e] for e in ev if e in pool))
    miss_n = [n for n in nums if not _has_number(cited, n)]
    if miss_n:
        return False, f"숫자 {miss_n}가 인용 근거에 없음"
    miss_p = [p for p in names if p not in cited]
    if miss_p:
        return False, f"선수 {miss_p}가 인용 근거에 없음"
    return True, "통과"


def verify(output, pool, players):
    kept, dropped = [], []
    for s in output.get("sentences", []):
        ok, why = verify_sentence(s, pool, players)
        (kept if ok else dropped).append({**s, "verdict": why})
    return {"sentences": kept, "dropped": dropped}
