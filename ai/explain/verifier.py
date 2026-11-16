"""B3 검증기 (규칙 기반). 루브릭 5번 결정대로 근거 표시 + 숫자 + 선수 이름 대조.

문장마다:
  1) 근거 표시가 있는지
  2) 붙인 ID가 실제 입력에 있는 ID인지
  3) 문장 속 숫자가 인용한 근거 텍스트에 있는지
  4) 문장 속 선수 이름이 인용한 근거 텍스트에 있는지
하나라도 걸리면 그 문장을 뺌. LLM 판정기나 NLI는 범위 밖.

버전
  v1 (기본): 위 규칙 그대로. 본 평가(채점 시트)는 v1로 고정.
  v2: v1에서 발견한 오류 2개 수정 (하이라이트 시연 H03에서 발견)
    - "기록에 없어 알 수 없습니다" 같은 '모름' 문장을 UNKNOWN이라고 지우던 문제 → 남김
    - "3루수", "1루" 같은 위치 이름의 숫자를 '숫자 주장'으로 보던 문제 → 숫자 검사에서 뺌
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


def _numbers(s, version="v1"):
    s = _norm(s)
    if version == "v2":
        # 위치 이름(1루, 2루, 3루, 1루수, 3루수, 1루주자 ...)의 숫자는 주장이 아니라 이름이라 뺌
        s = re.sub(r"[123](?=루)", "", s)
    return re.findall(r"\d+(?:\.\d+)?", s)


# v2: 기록에 없어서 모른다고 말하는 문장 (정직한 답이라 지우면 안 됨)
_NOINFO = re.compile(r"알\s*수\s*없|확인할\s*수\s*없|확인되지\s*않|기록에\s*없|기록되어\s*있지\s*않|"
                     r"나와\s*있지\s*않|나와\s*있지않|기록이\s*없|정보가\s*없")


def is_noinfo(text):
    return bool(_NOINFO.search(text))


def _has_number(evidence_text, n):
    return re.search(rf"(?<![\d.]){re.escape(n)}(?![\d])", evidence_text) is not None


def verify_sentence(sent, pool, players, version="v1"):
    text, ev = sent.get("text", ""), sent.get("evidence", []) or []
    nums = _numbers(text, version)
    names = [p for p in players if p and p in text]

    if not ev:
        return False, "근거 표시 없음"
    if ev == ["UNKNOWN"]:
        if version == "v2" and is_noinfo(text) and not nums:
            # 모름 문장은 남기되, 숫자를 말하거나 이번 기록에 없는 선수를 말하면 여전히 뺌
            # ("알 수 없는 이유로 3점을 냈다" 같은 끼워넣기 방지)
            all_text = " ".join(pool.values())
            if all(p in all_text for p in names):
                return True, "모름 문장(유지)"
        if version == "v2" and not is_noinfo(text):
            # 근거 없이 사실을 말하는 문장은 숫자·이름이 없어도 뺌
            return False, "근거 없는 주장(UNKNOWN)"
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


def verify(output, pool, players, version="v1"):
    kept, dropped = [], []
    for s in output.get("sentences", []):
        ok, why = verify_sentence(s, pool, players, version)
        (kept if ok else dropped).append({**s, "verdict": why})
    return {"sentences": kept, "dropped": dropped}