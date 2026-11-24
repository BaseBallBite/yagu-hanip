"""상태·점수 규칙 대조.

문장에서 이닝, 아웃카운트+주자 상태, 주자 출발·도착 베이스, 득점 'N점', 점수 'A:B', 'N구째' 투구 결과를
파싱해서 F(정리된 기록)와 R(문자중계 투구 줄)의 구조값과 직접 대조함.

판정
  bad   파싱한 값 중 하나라도 F/R과 안 맞음 -> 삭제 후보
  ok    파싱한 값이 있고 모두 맞음
  skip  파싱한 값이 없음 -> 판정하지 않고 기존 경로(KLUE)로 넘김
state_only  ok 이면서 문장 주장이 상태·점수뿐으로 보임 -> KLUE를 건너뛰고 유지해도 되는 후보

플레이 전/후 구분
  아웃카운트+주자 표현 뒤에 '상황/에서/이라' 등이 오면 플레이 전, '가 되/이닝 종료' 등이 오면 플레이 후,
  둘 다 아니면 전~후 어느 쪽이든 허용. 플레이 전은 [전, 후-1] 아웃, 플레이 후는 [전+1, 후] 아웃까지 허용
  (삼중살처럼 중간 상태를 말하는 문장 때문).

기존 verifier.py는 건드리지 않음. 입력 F 형식은 testset.jsonl 형식("4회초 1사 1·2루", "아웃카운트 2사, 주자 1루",
"점수 NC 4 : 2 KIA", "NC 2점 득점")과 서비스 형식("플레이 후: 2사 1,2루")을 둘 다 받음.
"""
import re

TAG = re.compile(r"\[[^\[\]]+\]")
OUTW = {"무사": 0, "노아웃": 0, "원아웃": 1, "투아웃": 2, "쓰리아웃": 3}
OUT_RE = re.compile(r"(무사|노\s?아웃|원\s?아웃|투\s?아웃|쓰리\s?아웃|(?<![\d.])([0-3])\s?(?:사(?!구)|아웃(?!\s?카운트)))")
BASES_RE = re.compile(r"\s*(?:주자\s*)?(만루|주자\s*없|[123](?:\s*[·,、]\s*[123])*\s*루(?:\s*[와과]\s*[123]\s*루)?)")
POST_AFTER = re.compile(r"^\s*(?:상황|상태)?\s*(?:이|가|을|를|로|으로|이\s?돼|가\s?돼)?\s*(?:되|됐|돼|바뀌|만들|이어지|채워|변했|변해|늘어|이\s*되)")
PRE_AFTER = re.compile(r"^\s*(?:상황|에서|인\s|이던|였던|이었던|이라|라서|때|의\s|기회|찬스|위기)")
POST_BEFORE = re.compile(r"(이후|결과|그\s?결과|되면서|되며|됐고|되었고|플레이\s?후|끝에)")
HYPO_AFTER = re.compile(r"^\s*(?:이?나\s|이거나|또는|이면|면\s|일\s?때|라면|에는\s)")
HYPO_BEFORE = re.compile(r"(?:나|또는|거나)\s*$")
RESULT_WORDS = ["헛스윙", "스트라이크", "파울", "볼", "타격"]
COMPAT = {"스트라이크": {"스트라이크", "헛스윙"}, "헛스윙": {"헛스윙"}, "파울": {"파울"}, "볼": {"볼"}, "타격": {"타격"}}


def _outs(tok):
    t = re.sub(r"\s", "", tok)
    if t in OUTW:
        return OUTW[t]
    return int(re.match(r"\d", t).group(0))


def _bases(tok):
    t = re.sub(r"\s", "", tok or "")
    if not t:
        return None
    if "만루" in t:
        return frozenset({1, 2, 3})
    if "없" in t:
        return frozenset()
    return frozenset(int(x) for x in re.findall(r"[123]", t))


# ---------------- F/R 파싱 ----------------
def parse_facts(facts, raw_relay=()):
    """facts: [{"id","text"}] 또는 {id: text}. raw_relay: R 원문 줄 목록(R1부터)."""
    if isinstance(facts, dict):
        facts = [{"id": k, "text": v} for k, v in facts.items() if k.startswith("F")]
    st = {"inning": None, "pre": None, "post": None, "runs": 0, "runs_team": None, "score": None,
          "runners": [], "batter": None, "pitches": {}, "names": set(), "side_moves": False}
    for f in facts:
        t = f["text"].strip()
        m = re.match(r"^(\d+)회\s*(초|말)\s+(무사|[0-3]사)\s*(.*)$", t)
        if m and st["pre"] is None:
            st["inning"] = (int(m.group(1)), m.group(2))
            st["pre"] = (_outs(m.group(3)), _bases(m.group(4)) if m.group(4) else None)
            continue
        m = re.match(r"^(?:아웃카운트|플레이\s?후:?)\s*(무사|[0-3]사|3아웃)\s*,?\s*(?:주자\s*)?(.*)$", t)
        if m:
            o = 3 if "3" in m.group(1) and "아웃" in m.group(1) else _outs(m.group(1))
            rest = m.group(2)
            b = None if ("이닝" in rest or o == 3) else _bases(re.sub(r"[^\d·,만루없]", "", rest) or ("없" if "없" in rest else ""))
            st["post"] = (o, b)
            continue
        m = re.match(r"^(\S+)\s+(\d+)점\s*득점", t)
        if m:
            st["runs"] += int(m.group(2)); st["runs_team"] = m.group(1)
            continue
        m = re.match(r"^점수\s+(\S+)\s+(\d+)\s*:\s*(\d+)\s+(\S+)", t)
        if m:
            st["score"] = (m.group(1), int(m.group(2)), int(m.group(3)), m.group(4))
            continue
        m = re.match(r"^([123])루주자\s+(\S+?)\s*:\s*(.*)$", t)
        if m:
            what = m.group(3)
            d = re.search(r"([123])루까지", what)
            dest = 4 if "홈인" in what else ("out" if "아웃" in what else (int(d.group(1)) if d else None))
            st["runners"].append({"from": int(m.group(1)), "name": m.group(2), "dest": dest, "what": what})
            st["names"].add(m.group(2))
            if re.search(r"보크|도루|폭투|포일|견제", what):
                st["side_moves"] = True
            continue
        m = re.match(r"^\d+번타자\s+(\S+?)\s*:\s*(.*)$", t)
        if m:
            st["batter"] = (m.group(1), m.group(2)); st["names"].add(m.group(1))
    for line in raw_relay:
        m = re.match(r"^(\d+)구\s*(\S+)", line.strip())
        if m:
            w = m.group(2)
            st["pitches"][int(m.group(1))] = next((x for x in RESULT_WORDS if w.startswith(x)), w)
    return st


# ---------------- 개별 검사 ----------------
def _allowed_outs(st, mode):
    pre, post = st["pre"][0], st["post"][0] if st["post"] else st["pre"][0]
    if mode == "pre":
        return set(range(pre, max(pre, post - 1) + 1)) if post > pre else {pre}
    if mode == "post":
        return set(range(pre + 1, post + 1)) if post > pre else {post}
    return set(range(pre, post + 1))


def check_state(body, st):
    res = []
    if st["pre"] is None:
        return res
    for m in OUT_RE.finditer(body):
        o = _outs(m.group(1))
        after = body[m.end():]
        # '무사나 1사에', '1사 또는 2사면' 같은 규칙 설명(가정)은 이 플레이 상태가 아니라서 판정 안 함
        if HYPO_AFTER.match(after) or HYPO_BEFORE.search(body[max(0, m.start() - 6):m.start()]):
            continue
        bm = BASES_RE.match(after)
        b = _bases(bm.group(1)) if bm else None
        rest = after[bm.end():] if bm else after
        if o == 3 or POST_AFTER.match(rest) or re.match(r"^\s*,?\s*이닝\s?종료", rest):
            mode = "post"
        elif PRE_AFTER.match(rest) and not POST_BEFORE.search(body[:m.start()]):
            mode = "pre"
        else:
            mode = "any"
        ok_outs = _allowed_outs(st, mode)
        span = m.group(0) + (bm.group(0) if bm else "")
        if o not in ok_outs:
            res.append(("outs", False, f"{span.strip()}({mode}) F:{st['pre'][0]}->{st['post'][0] if st['post'] else '?'}"))
            continue
        res.append(("outs", True, span.strip()))
        if b is None:
            continue
        cand = set()
        if mode in ("pre", "any") and o == st["pre"][0] and st["pre"][1] is not None:
            cand.add(st["pre"][1])
        if mode in ("post", "any") and st["post"] and o == st["post"][0] and st["post"][1] is not None:
            cand.add(st["post"][1])
        if not cand:
            continue  # 중간 상태라 주자 비교 안 함
        if b in cand:
            res.append(("bases", True, span.strip()))
        elif st["side_moves"]:
            res.append(("bases", None, span.strip()))  # 보크·도루 등 중간 이동이 있어 판정 보류
        else:
            res.append(("bases", False, f"{span.strip()}({mode}) F:{sorted(next(iter(cand)))}"))
    return res


KOR_N = {"한": 1, "두": 2, "세": 3, "1": 1, "2": 2, "3": 3}
INC_RE = re.compile(r"(한|두|세|[123])\s*개의\s*아웃(?:카운트)?|아웃(?:카운트)?\s*(한|두|세|[123])\s*개(?:가|를)?\s*(?:늘|올라|추가|잡)")
RB_RE = re.compile(r"주자(?:는|가)\s*((?:[123]\s*루(?:\s*(?:와|과|,|·|및)\s*[123]\s*루)*)|만루|없)"
                   r"(?=\s*(?:에\s*(?:위치|있|남)|(?:가|이)?\s*(?:되|됐)|인?\s*상황|상태|는\s*상황))")


def check_extra(body, st):
    """아웃카운트 증가량('두 개의 아웃'), 아웃 표현과 떨어진 주자 상태('주자는 2루와 3루에')."""
    res = []
    if st["pre"] is None or st["post"] is None:
        return res
    for m in INC_RE.finditer(body):
        n = KOR_N[m.group(1) or m.group(2)]
        d = st["post"][0] - st["pre"][0]
        res.append(("out_inc", n == d, m.group(0) + ("" if n == d else f" F:+{d}")))
    for m in RB_RE.finditer(body):
        b = _bases(m.group(1))
        post = bool(re.search(r"되었|됐|되며|되면서|위치하게|결과|이후", body))
        cand = {st["post"][1]} if post else {st["pre"][1], st["post"][1]}
        cand.discard(None)
        if not cand:
            continue
        if b in cand:
            res.append(("bases", True, m.group(0)))
        elif not st["side_moves"]:
            res.append(("bases", False, f"{m.group(0)} F:{[sorted(c) for c in cand]}"))
    return res


def check_inning(body, st):
    res = []
    if not st["inning"]:
        return res
    for m in re.finditer(r"(\d+)회\s*(초|말)", body):
        ok = (int(m.group(1)), m.group(2)) == st["inning"]
        res.append(("inning", ok, m.group(0)))
    return res


DEST_RE = re.compile(r"(?:([123])\s*루\s*(?:까지|로|에)\s*(?:진루|들어|이동|안착|나가|가|뛰|향|살|도착)"
                     r"|(홈\s*(?:으로|을|인|에|까지|플레이트)|득점(?:했|하|에)|홈인))")
ORIGIN_RE = re.compile(r"([123])\s*루\s*주자\s*$")


def check_runners(body, st, players=()):
    res = []
    rnames = {r["name"] for r in st["runners"]}
    if not rnames:
        return res
    allnames = sorted(set(players) | st["names"], key=len, reverse=True)
    hits = []
    for n in allnames:
        if len(n) < 2:
            continue
        for m in re.finditer(re.escape(n), body):
            if not any(a <= m.start() < b for a, b, _ in hits):
                hits.append((m.start(), m.end(), n))
    hits.sort()
    for k, (s, e, n) in enumerate(hits):
        if n not in rnames:
            continue
        lines = [r for r in st["runners"] if r["name"] == n]
        om = ORIGIN_RE.search(body[max(0, s - 8):s].rstrip())
        if om:
            org = int(om.group(1))
            if org not in {r["from"] for r in lines}:
                # 타자주자는 F에 '1루주자'로 나오기도 하므로 출발 베이스 불일치만으로는 보류
                res.append(("runner_from", False, f"{org}루주자 {n} F:{sorted({r['from'] for r in lines})}"))
                continue
            lines = [r for r in lines if r["from"] == org]
        seg_end = hits[k + 1][0] if k + 1 < len(hits) else len(body)
        seg = body[e:seg_end]
        seg = re.sub(r"[123]\s*루\s*주자\s*$", "", seg.rstrip())
        dm = DEST_RE.search(seg)
        if not dm:
            continue
        claim = int(dm.group(1)) if dm.group(1) else 4
        dests = {r["dest"] for r in lines if r["dest"] is not None}
        if not dests or "out" in dests and len(dests) == 1:
            if dests == {"out"}:
                res.append(("runner_dest", False, f"{n} {claim}루 주장, F: 아웃"))
            continue
        ok = claim in dests
        res.append(("runner_dest", ok, f"{n} {'홈' if claim == 4 else str(claim) + '루'}" + ("" if ok else f" F:{sorted(d for d in dests if d != 'out')}")))
    return res


RUN_RE = re.compile(r"(\d+)\s*점(?!\s*차|\s*째|대|수|을\s*내준|\s*홈런)")


def check_runs(body, st):
    res = []
    ms = [m for m in RUN_RE.finditer(body)]
    if not ms:
        return res
    if re.search(r"총|모두\s*\d|합쳐|합계|해서|누적|째", body):
        return res
    total = st["runs"]
    vals = [int(m.group(1)) for m in ms]
    score_nums = set()
    if st["score"]:
        score_nums = {st["score"][1], st["score"][2]}
    runners_in = len([r for r in st["runners"] if r["name"] in body])
    if st["score"] and len(vals) == 2 and sorted(vals) == sorted(st["score"][1:3]) \
            and not re.search(r"올렸|더\s|득점|냈|뽑|들어와|홈", body):
        res.append(("score_pts", True, "+".join(map(str, vals)))); return res  # 'NC가 5점, KIA가 3점' 같은 점수 상태
    if len(vals) >= 2:
        ok = sum(vals) == total
        res.append(("runs_sum", ok, f"{'+'.join(map(str, vals))}={sum(vals)} F:{total}"))
    elif re.search(r"각각|씩", body) and runners_in >= 2:
        ok = vals[0] * runners_in == total
        res.append(("runs_each", ok, f"{vals[0]}x{runners_in} F:{total}"))
    elif total > 0:
        ok = vals[0] <= total or vals[0] in score_nums
        res.append(("runs", ok, f"{vals[0]}점 F:{total}"))
    return res


def check_score(body, st):
    res = []
    if not st["score"]:
        return res
    t1, a, b, t2 = st["score"]
    pairs = {(a, b), (b, a)}
    if st["runs"] and st["runs_team"]:
        if st["runs_team"] == t1:
            pairs |= {(a - st["runs"], b), (b, a - st["runs"])}
        elif st["runs_team"] == t2:
            pairs |= {(a, b - st["runs"]), (b - st["runs"], a)}
    for m in re.finditer(r"(?<![\d.])(\d{1,2})\s*(?::|대)\s*(\d{1,2})(?![\d.])", body):
        x = (int(m.group(1)), int(m.group(2)))
        res.append(("score", x in pairs, m.group(0) + ("" if x in pairs else f" F:{a}:{b}")))
    return res


CLEAN_P = re.compile(r"스트라이크\s*낫\s*아웃|낫\s*아웃|스트라이크\s*존|볼\s*카운트|볼넷|볼\s*넷|파울\s*(?:라인|플라이|팁|지역)|타격\s*방해")


def check_pitches(body, st):
    res = []
    if not st["pitches"]:
        return res
    b = CLEAN_P.sub(" ", body)
    for m in re.finditer(r"(\d+)\s*구\s*째", b):
        n = int(m.group(1))
        if n not in st["pitches"]:
            continue
        clause = re.split(r"[,.]|받아|되었|됐|해서|하며|하고|했", b[m.end():], maxsplit=1)[0]
        words = []
        for w in RESULT_WORDS:
            words += [w] * len(re.findall(r"(?<![가-힣])" + w + (r"(?!넷)" if w == "볼" else ""), clause))
        if "헛스윙" in words and "스트라이크" in words:
            words.remove("스트라이크")  # '헛스윙 스트라이크'는 한 투구
        if not words:
            continue
        actual = st["pitches"][n]
        ok = len(words) == 1 and actual in COMPAT.get(words[0], {words[0]})
        res.append(("pitch", ok, f"{n}구째 {'+'.join(words)} R:{actual}"))
    return res


# ---------------- 문장 판정 ----------------
# 상태·점수 말고 다른 주장이 없는지 보는 데 쓰는 말 목록. 긴 것부터 지우고 남는 글자가 없으면 state_only.
FILLER_PHRASES = sorted("""
이 안타로|이 플레이로|이 타격으로|이번 타석으로|그 결과|결과적으로|그래서|그리고|이렇게|결국|이때|이후|현재|당시|순식간에|한 번에
아웃카운트는|아웃카운트가|아웃카운트|아웃이|아웃|이닝이|이닝은|이닝|종료되었어요|종료됐어요|종료되었고|종료
위치하게|위치해|위치|올라가며|올라가|올라|늘어나|늘어|나오면서|나와|되었어요|되었고|되었|됐어요|됐고|되면서|되며|되어|돼요|되
상황이|상황에서|상황|상태예요|상태이고|상태|점수는|점수가|점수|공격|경기는|경기|주자는|주자가|주자|선수
이었어요|였어요|이에요|예요|이었고|였고|입니다|에서|으로|로|에|는|은|이|가|의|와|과|도|를|을|인|고|며
개의|개가|개|한|두|세|번|무사|만루|없음|회|초|말|사|루|점|대|:
""".replace("\n", "|").split("|"), key=len, reverse=True)
FILLER_PHRASES = [x.strip() for x in FILLER_PHRASES if x.strip()]


def check(sentence, item_or_facts, raw_relay=None, players=None, debug=False):
    """item_or_facts: testset 문항(dict, facts·raw_relay·players 포함) 또는 parse_facts() 결과."""
    if isinstance(item_or_facts, dict) and "facts" in item_or_facts:
        st = parse_facts(item_or_facts["facts"], item_or_facts.get("raw_relay", []))
        players = players if players is not None else item_or_facts.get("players", [])
    else:
        st = item_or_facts
    players = players or []
    body = re.sub(r"\s+", " ", TAG.sub(" ", sentence)).strip()
    tags = re.findall(r"(?:F|R)\d+|K:", sentence)
    if tags and all(t == "K:" for t in tags):
        # 카드만 인용한 문장은 규칙 설명이라 이 플레이의 상태와 대조하지 않음
        return {"status": "skip", "state_only": False, "checks": [], "why": ""}
    checks = (check_inning(body, st) + check_state(body, st) + check_runners(body, st, players)
              + check_runs(body, st) + check_score(body, st) + check_pitches(body, st) + check_extra(body, st))
    decided = [c for c in checks if c[1] is not None]
    bad = [c for c in decided if c[1] is False]
    status = "bad" if bad else ("ok" if decided else "skip")
    state_only = False
    if status == "ok":
        rest = body
        for n in sorted(set(players) | st["names"], key=len, reverse=True):
            rest = rest.replace(n, " ")
        if st["score"]:
            rest = rest.replace(st["score"][0], " ").replace(st["score"][3], " ")
        rest = re.sub(r"[\d\s,.·]", " ", rest)
        for ph in FILLER_PHRASES:
            rest = rest.replace(ph, " ")
        rest = re.sub(r"\s+", "", rest)
        state_only = len(rest) == 0
        if debug:
            print("residual:", rest)
    return {"status": status, "state_only": state_only, "checks": checks,
            "why": "; ".join(f"{k}:{d}" for k, ok, d in bad)}


if __name__ == "__main__":
    import json, sys
    # 사용: python state_rule_check.py testset.jsonl "<문항 id>" "<문장>"
    items = {json.loads(l)["id"]: json.loads(l) for l in open(sys.argv[1], encoding="utf-8")}
    print(json.dumps(check(sys.argv[3], items[sys.argv[2]]), ensure_ascii=False, indent=1))
