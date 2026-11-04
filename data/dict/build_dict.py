#!/usr/bin/env python3
# cards/*.yaml 을 읽어서 dict.json, dict.csv 를 만드는 스크립트
# 사용법: python3 build_dict.py <카드 폴더> <출력 폴더>
# 밑줄(_)로 시작하는 파일(_template.yaml)은 건너뜀
import csv, json, sys
from pathlib import Path
import yaml

REQUIRED = ["id", "kind", "title", "category", "one_liner", "easy", "review_status"]
KIND_KO = {"rule": "규칙", "term": "용어"}


def load_cards(src):
    cards, errors = [], []
    for f in sorted(src.rglob("*.yaml")):  # rule/, term/ 하위 폴더까지 읽음
        if f.name.startswith("_"):
            continue
        try:
            c = yaml.safe_load(f.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"{f.name}: 파싱 실패 ({e})")
            continue
        if not isinstance(c, dict):
            errors.append(f"{f.name}: 내용이 비었거나 형식이 다름")
            continue
        miss = [k for k in REQUIRED if not c.get(k)]
        if miss:
            errors.append(f"{f.name}: 필수 칸 없음 {miss}")
            continue
        if c["id"] != f.stem:
            errors.append(f"{f.name}: id({c['id']})와 파일 이름이 다름")
            continue
        if c["kind"] not in KIND_KO:
            errors.append(f"{f.name}: kind 값이 rule/term 이 아님")
            continue
        if f.parent.name in KIND_KO and f.parent.name != c["kind"]:
            errors.append(f"{f.name}: {f.parent.name}/ 폴더에 있는데 kind 가 {c['kind']}")
            continue
        for k in ("easy", "example", "one_liner"):
            if isinstance(c.get(k), str):
                c[k] = c[k].strip()
        cards.append(c)
    return cards, errors


def warnings_for(cards):
    ids = {c["id"] for c in cards}
    out = []
    for c in cards:
        if len(c["one_liner"]) > 60:
            out.append(f"{c['id']}: one_liner 60자 넘음({len(c['one_liner'])}자)")
        if not c.get("source"):
            out.append(f"{c['id']}: source 없음")
        for r in c.get("related") or []:
            if r not in ids:
                out.append(f"{c['id']}: related 에 없는 카드 {r}")
    return out


def build_json(cards):
    alias_index = {}  # 공백 뺀 표기 -> 카드 id, 긴 표기부터 맞추도록 길이순 정렬
    for c in cards:
        for w in [c["title"], *(c.get("aliases") or [])]:
            alias_index.setdefault(str(w).replace(" ", ""), c["id"])
    event_index = {}
    for c in cards:
        for et in c.get("event_types") or []:
            event_index.setdefault(et, []).append(c["id"])
    return {
        "cards": {c["id"]: c for c in cards},
        "alias_index": dict(sorted(alias_index.items(), key=lambda kv: -len(kv[0]))),
        "event_index": event_index,
    }


def fmt_source(src):
    parts = []
    for s in src or []:
        if isinstance(s, dict):
            p = " ".join(str(s[k]) for k in ("name", "ref") if s.get(k))
            if s.get("note"):
                p += f" ({s['note']})"
            if s.get("url"):
                p += f" {s['url']}"
            parts.append(p.strip())
        else:
            parts.append(str(s))
    return " / ".join(parts)


def fmt_when(w):
    if not w:
        return ""
    if isinstance(w, dict):
        out = []
        for k, v in w.items():
            v = ", ".join(map(str, v)) if isinstance(v, list) else str(v)
            out.append(f"{k}: {v}")
        return " / ".join(out)
    return str(w)


def build_csv(cards, dst):
    titles = {c["id"]: c["title"] for c in cards}
    head = ["카드 ID", "구분", "제목", "카테고리", "한 줄 설명", "쉬운 설명", "예시",
            "적용 조건", "출처", "인용", "관련 카드", "경기 이벤트", "별칭"]
    with open(dst, "w", encoding="utf-8-sig", newline="") as f:  # BOM 포함, 엑셀에서 한글 안 깨짐
        w = csv.writer(f)
        w.writerow(head)
        for c in cards:
            w.writerow([
                c["id"], KIND_KO[c["kind"]], c["title"], c["category"], c["one_liner"],
                c.get("easy", ""), c.get("example", "") or "", fmt_when(c.get("when")),
                fmt_source(c.get("source")), c.get("quote", "") or "",
                ", ".join(titles.get(r, r) for r in c.get("related") or []),
                ", ".join(c.get("event_types") or []),
                ", ".join(map(str, c.get("aliases") or [])),
            ])


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    cards, errors = load_cards(src)
    cards.sort(key=lambda c: (c["kind"], c["id"]))
    d = build_json(cards)
    (out / "dict.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    build_csv(cards, out / "dict.csv")
    n = {k: sum(c["kind"] == k for c in cards) for k in KIND_KO}
    print(f"카드 {len(cards)}장 (rule {n['rule']}, term {n['term']}), "
          f"별칭 {len(d['alias_index'])}개, 이벤트 {len(d['event_index'])}종")
    for e in errors:
        print("오류:", e)
    for wmsg in warnings_for(cards):
        print("경고:", wmsg)


if __name__ == "__main__":
    main()
