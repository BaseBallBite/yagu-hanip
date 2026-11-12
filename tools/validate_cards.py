#!/usr/bin/env python3
"""야알못 카드 검사기.

사용법:
  pip install pyyaml
  python3 tools/validate_cards.py cards/            # 검사
  python3 tools/validate_cards.py cards/ --strict   # related가 없는 카드를 가리키면 오류로 처리(최종 점검용)

오류(ERROR)가 하나라도 있으면 종료 코드 1. 경고(WARN)는 고치면 좋은 것.
"""
import argparse, re, sys
from pathlib import Path

import yaml

KINDS = {"term", "rule"}
CATEGORIES = {
    "term": {"투구·구종", "타격", "주루", "수비", "기록·통계", "경기 운영"},
    "rule": {"기본 규칙", "타격 규칙", "주루 규칙", "수비 규칙", "특수 상황"},
}
REQUIRED = ["id", "kind", "title", "category", "one_liner", "easy", "source", "aliases", "review_status"]
REVIEW = {"draft", "reviewed"}
ID_RE = re.compile(r"^(term|rule)\.[a-z0-9_]+$")
ONE_LINER_MAX = 60
QUOTE_MAX = 40


def sentences(text):
    return [s for s in re.split(r"(?<=[.?!요다])\s+", text.strip()) if s]


def load_event_types(path):
    if not path.exists():
        return None
    return {l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cards_dir")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    cards_dir = Path(args.cards_dir)
    event_types = load_event_types(Path(__file__).with_name("event_types.txt"))
    errors, warns = [], []
    cards = {}

    for f in sorted(cards_dir.rglob("*.yaml")):
        if f.name.startswith("_"):
            continue
        err = lambda m: errors.append(f"{f.name}: {m}")
        warn = lambda m: warns.append(f"{f.name}: {m}")
        try:
            c = yaml.safe_load(f.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            err(f"YAML 문법 오류 → {e}")
            continue
        if not isinstance(c, dict):
            err("내용이 비어 있거나 형식이 아님")
            continue

        for k in REQUIRED:
            if c.get(k) in (None, "", []) and k != "aliases":
                err(f"필수 칸 '{k}'이(가) 비어 있음")
            elif k not in c:
                err(f"필수 칸 '{k}'이(가) 없음")

        cid = c.get("id", "")
        if not ID_RE.match(str(cid)):
            err(f"id '{cid}' 형식이 틀림 (term.영어_소문자 또는 rule.영어_소문자)")
        if f.stem != cid:
            err(f"파일 이름은 '{cid}.yaml' 이어야 함")
        if cid in cards:
            err(f"id '{cid}' 중복")
        kind = c.get("kind")
        if kind not in KINDS:
            err(f"kind는 term 또는 rule (지금: {kind})")
        elif not str(cid).startswith(kind + "."):
            err(f"id 앞부분이 kind({kind})와 다름")
        if kind in CATEGORIES and c.get("category") not in CATEGORIES[kind]:
            err(f"category '{c.get('category')}'는 {kind} 목록에 없음: {sorted(CATEGORIES[kind])}")

        ol = str(c.get("one_liner", ""))
        if len(ol) > ONE_LINER_MAX:
            err(f"one_liner가 {len(ol)}자 (최대 {ONE_LINER_MAX}자)")
        n = len(sentences(str(c.get("easy", ""))))
        if c.get("easy") and not 2 <= n <= 4:
            warn(f"easy가 {n}문장 (2~4문장 권장)")
        if c.get("quote") and len(str(c["quote"])) > QUOTE_MAX:
            err(f"quote가 {len(str(c['quote']))}자 (원문 인용은 최대 {QUOTE_MAX}자)")

        src = c.get("source") or []
        if not isinstance(src, list):
            err("source는 목록(- 로 시작)이어야 함")
            src = []
        if kind == "rule" and not any(isinstance(s, dict) and s.get("ref") for s in src):
            err("규칙 카드는 source에 규칙집 조항(ref)이 1개 이상 있어야 함")
        if any(isinstance(s, dict) and "확인 필요" in str(s.get("ref", "")) for s in src):
            (err if c.get("review_status") == "reviewed" else warn)("source에 '확인 필요'인 조항 번호가 남아 있음")
        if kind == "rule" and not c.get("when"):
            warn("규칙 카드는 when(적용 조건)을 적으면 AI 검증에 쓸 수 있음")
        if not c.get("example"):
            warn("example(가상 예시 상황)이 없음")

        if c.get("review_status") not in REVIEW:
            err(f"review_status는 draft 또는 reviewed (지금: {c.get('review_status')})")
        if c.get("review_status") == "reviewed" and not c.get("reviewer"):
            err("reviewed인데 reviewer(검수한 사람)가 비어 있음")

        for et in c.get("event_types") or []:
            if event_types is not None and et not in event_types:
                warn(f"event_type '{et}'이(가) tools/event_types.txt에 없음")

        cards[cid] = c

    # 카드 사이 검사
    alias_owner = {}
    for cid, c in cards.items():
        words = [c.get("title", "")] + list(c.get("aliases") or [])
        for w in words:
            key = str(w).replace(" ", "")
            if not key:
                continue
            if key in alias_owner and alias_owner[key] != cid:
                errors.append(f"{cid}.yaml: 밑줄 단어 '{w}'가 {alias_owner[key]}와 겹침 (한 단어는 한 카드에만)")
            alias_owner.setdefault(key, cid)
        for r in c.get("related") or []:
            if r == cid:
                errors.append(f"{cid}.yaml: related에 자기 자신이 있음")
            elif r not in cards:
                (errors if args.strict else warns).append(f"{cid}.yaml: related '{r}' 카드가 아직 없음")

    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    terms = sum(1 for c in cards.values() if c.get("kind") == "term")
    reviewed = sum(1 for c in cards.values() if c.get("review_status") == "reviewed")
    print(f"\n카드 {len(cards)}개 (용어 {terms}, 규칙 {len(cards) - terms}) · 검수 완료 {reviewed}개 · 오류 {len(errors)} · 경고 {len(warns)}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
