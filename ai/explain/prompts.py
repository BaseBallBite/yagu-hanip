"""조건별 입력 구성 (B0~B2는 LLM 입력, R은 LLM 없이 템플릿).

B3는 따로 생성하지 않음. B2 출력에 검증기(verifier.py)만 적용함.
그래야 B2 vs B3 차이가 '검증기 효과'만으로 나옴.
"""
import json

from pydantic import BaseModel, Field

SYSTEM_PROMPT = """너는 야구 초보자에게 경기 장면을 설명하는 해설자다.

규칙:
1. 아래 [입력]에 있는 정보만 사용한다. 입력에 없는 기록, 통계, 선수 정보를 지어내지 않는다.
2. 3~4문장으로 답한다. 쉬운 말로, 야구 용어는 처음 나올 때 짧게 풀어준다.
3. 문장마다 그 문장의 근거가 된 입력 ID를 evidence에 적는다. (예: "R3", "F2", "rule.infield_fly")
4. 입력만으로 답할 수 없는 부분은 "기록에 없어 알 수 없습니다"처럼 말하고 evidence에 "UNKNOWN"만 적는다.
5. 근거 없이 추측한 문장은 쓰지 않는다.
"""

ALLOWED_INPUTS = {
    "B0": ("raw",),
    "B1": ("raw", "facts"),
    "B2": ("raw", "facts", "cards"),
}


class Sentence(BaseModel):
    text: str
    evidence: list[str] = Field(default_factory=list)


class Commentary(BaseModel):
    sentences: list[Sentence]


def raw_lines(item):
    raw = item.get("raw_relay", [])
    if isinstance(raw, str):
        raw = [l for l in raw.splitlines() if l.strip()]
    return [{"id": f"R{i}", "text": t.strip()} for i, t in enumerate(raw, 1)]


def fact_lines(item):
    facts = item.get("facts", [])
    if isinstance(facts, dict):  # {"이닝": "7회말", ...} 형태도 허용
        facts = [f"{k}: {v}" for k, v in facts.items()]
    out = []
    for i, f in enumerate(facts, 1):
        out.append(f if isinstance(f, dict) else {"id": f"F{i}", "text": str(f)})
    return out


def _render_card(c):
    """yaml 카드 → 모델에 넣을 한 덩어리 텍스트.
    example(가상 예시)과 more는 뺌: 가상 상황의 숫자·주자가 실제 경기 해설에 섞이는 걸 막으려고."""
    parts = [c.get("one_liner", "").strip(), " ".join(str(c.get("easy", "")).split())]
    when = c.get("when")
    if isinstance(when, dict) and when:
        conds = []
        for k, v in when.items():
            v = ", ".join(map(str, v)) if isinstance(v, list) else str(v)
            conds.append(f"{k}: {v}")
        parts.append("적용 조건 - " + " / ".join(conds))
    return " ".join(p for p in parts if p)


def load_cards(path):
    """카드 폴더(cards/, 하위 rule/·term/의 *.yaml) 또는 예전 json 파일을 읽어서
    {id: {"title", "text", "rule_ref", "review_status"}} 로 맞춤."""
    from pathlib import Path
    path = Path(path)
    if path.suffix == ".json":
        return json.load(open(path, encoding="utf-8"))
    import yaml
    cards = {}
    for f in sorted(path.rglob("*.yaml")):
        if f.name.startswith("_"):
            continue
        c = yaml.safe_load(open(f, encoding="utf-8")) or {}
        cid = c.get("id") or f.stem
        refs = [s.get("ref") for s in (c.get("source") or []) if isinstance(s, dict) and s.get("ref")]
        cards[cid] = {"title": c.get("title", cid), "text": _render_card(c),
                      "rule_ref": ", ".join(refs), "review_status": c.get("review_status", "")}
    return cards


def card_lines(item, cards):
    out = []
    for cid in item.get("card_ids", []):
        c = cards.get(cid)
        if c is None:
            raise KeyError(f"{item['qid']}: 카드 {cid} 가 cards 파일에 없음")
        ref = f" (출처: {c['rule_ref']})" if c.get("rule_ref") else ""
        out.append({"id": cid, "text": f"[{c['title']}]{ref} {c['text']}"})
    return out


def evidence_pool(item, cards, condition):
    """조건별로 모델이 볼 수 있는 근거 ID → 텍스트. 검증기도 이걸 씀."""
    allowed = ALLOWED_INPUTS.get(condition, ("raw", "facts", "cards"))
    pool = {}
    if "raw" in allowed:
        pool.update({x["id"]: x["text"] for x in raw_lines(item)})
    if "facts" in allowed:
        pool.update({x["id"]: x["text"] for x in fact_lines(item)})
    if "cards" in allowed:
        pool.update({x["id"]: x["text"] for x in card_lines(item, cards)})
    return pool


def build_user_prompt(item, cards, condition):
    allowed = ALLOWED_INPUTS[condition]
    parts = [f"[질문]\n{item['question']}", "[입력]"]
    if "raw" in allowed:
        parts.append("## 문자중계 원문\n" + "\n".join(f"{x['id']}: {x['text']}" for x in raw_lines(item)))
    if "facts" in allowed:
        parts.append("## 정리된 경기 기록 (F)\n" + "\n".join(f"{x['id']}: {x['text']}" for x in fact_lines(item)))
    if "cards" in allowed:
        parts.append("## 규칙/용어 카드 (K)\n" + "\n".join(f"{x['id']}: {x['text']}" for x in card_lines(item, cards)))
    return "\n\n".join(parts)


def build_rule_baseline(item, cards):
    """R 조건: LLM 없이 F를 템플릿에 채우고 카드 원문을 그대로 붙임."""
    sents = []
    facts = fact_lines(item)
    if facts:
        sents.append({"text": "상황: " + ", ".join(f["text"] for f in facts) + ".",
                      "evidence": [f["id"] for f in facts]})
    for c in card_lines(item, cards):
        sents.append({"text": c["text"], "evidence": [c["id"]]})
    if not sents:
        sents.append({"text": "기록에 없어 알 수 없습니다.", "evidence": ["UNKNOWN"]})
    return {"sentences": sents}
