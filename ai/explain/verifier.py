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

# ---- 서비스용: 규칙 v2 + KLUE 검증 모델 ----
# KLUE 모델은 (문장, 인용 근거)가 지지/모순/근거밖인지 배운 모델이라 '모름' 문장은 학습한 적이 없음.
# 모름 문장은 내용 주장이 없어서 근거와 대조할 게 없으므로 모델에 넣지 않고 규칙으로만 판단함.
UNKNOWN_MAX_LEN = 60   # 모름 문장에 다른 주장을 끼워 넣는 것을 막기 위한 길이 상한(글자)


def check_unknown(sent, pool, players):
    """evidence가 ["UNKNOWN"]뿐인 문장 판정. 반환: (통과 여부, 이유)"""
    text = sent.get("text", "")
    if not is_noinfo(text):
        return False, "근거 없는 주장(UNKNOWN)"
    # v2 숫자 검사는 '2루타'의 2를 위치 숫자로 보고 빼므로, 모름 문장에서는 숫자를 하나도 허용하지 않음
    if re.search(r"\d", text):
        return False, "모름 문장인데 숫자를 말함"
    all_text = " ".join(pool.values())
    miss = [p for p in players if p and p in text and p not in all_text]
    if miss:
        return False, f"모름 문장에 기록에 없는 선수 {miss}"
    if len(text) > UNKNOWN_MAX_LEN:
        return False, "모름 문장이 너무 김(다른 주장 섞임 의심)"
    return True, "모름 문장(유지)"


def _state_facts(pool):
    """pool에서 상태 규칙 대조에 쓸 F 목록과 R 줄(번호순)을 꺼냄."""
    def num(k):
        return int(k[1:])
    facts = [{"id": k, "text": pool[k]} for k in sorted((k for k in pool if re.match(r"^F\d+$", k)), key=num)]
    relay = [pool[k] for k in sorted((k for k in pool if re.match(r"^R\d+$", k)), key=num)]
    return facts, relay


def _tagged(s):
    return s.get("text", "") + " " + "".join(f"[{e}]" if re.match(r"^[FR]\d+$", e) else f"[K:{e}]" for e in s.get("evidence", []))


def verify_service(output, pool, players, p_support, threshold=0.05, max_unknown=1, state_rule=True):
    """서비스 B3. 문장 순서는 그대로 유지함.
    - evidence가 ["UNKNOWN"]뿐: check_unknown 규칙만 적용, 모델 안 씀. 해설 하나에 max_unknown개까지
    - evidence에 UNKNOWN과 실제 ID가 섞임: UNKNOWN을 빼고 일반 문장으로 처리
    - 일반 문장: 규칙 v2 통과 → (state_rule) 상태 규칙 대조 → 인용 근거만 붙여서 모델 P(지지) >= threshold 이면 유지
      상태 규칙 대조(service_state_check.py): 아웃카운트·주자·점수·이닝·투구 순서가 F/R과 다르면 삭제,
      모두 맞고 상태만 말하는 문장이면 모델 없이 유지, 그 밖은 모델로 넘김
    p_support: apply_model.load_model(모델 폴더)가 돌려주는 함수 [(문장, 근거)] -> [P(지지)]
    """
    if state_rule:
        try:
            from . import service_state_check as state
        except ImportError:  # ai/explain 폴더에서 스크립트로 실행할 때
            import service_state_check as state
        facts, relay = _state_facts(pool)
    res, normal, n_unknown = [], [], 0
    for i, s in enumerate(output.get("sentences", [])):
        ev = s.get("evidence") or []
        if ev == ["UNKNOWN"]:
            ok, why = check_unknown(s, pool, players)
            if ok and n_unknown >= max_unknown:
                ok, why = False, "모름 문장 중복"
            n_unknown += ok
            res.append({**s, "verdict": why, "ok": ok, "check": "unknown_rule", "p_support": None})
            continue
        if "UNKNOWN" in ev:
            s = {**s, "evidence": [e for e in ev if e != "UNKNOWN"]}
        ok, why = verify_sentence(s, pool, players, "v2")
        r = {**s, "verdict": why, "ok": ok, "check": "rule_v2", "p_support": None}
        res.append(r)
        if ok and state_rule:
            st = state.state_check(_tagged(s), facts, relay, players)
            if st["status"] == "bad":
                r["ok"], r["check"], r["verdict"] = False, "rule_v2+state", f"상태 규칙: {st['why']}"
                continue
            if st["status"] == "ok" and st["state_only"]:
                r["check"], r["verdict"] = "rule_v2+state", "상태 규칙 통과(모델 생략)"
                continue
        if ok:
            normal.append(r)
    if normal:
        probs = p_support([(r["text"], " / ".join(pool[e] for e in r["evidence"])) for r in normal])
        for r, p in zip(normal, probs):
            r["check"], r["p_support"] = "rule_v2+model", round(float(p), 4)
            if p < threshold:
                r["ok"], r["verdict"] = False, f"모델 P(지지) {p:.4f} < {threshold}"
    kept = [{k: v for k, v in r.items() if k != "ok"} for r in res if r["ok"]]
    dropped = [{k: v for k, v in r.items() if k != "ok"} for r in res if not r["ok"]]
    return {"sentences": kept, "dropped": dropped}
