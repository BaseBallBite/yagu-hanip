"""서비스 검증용 상태 규칙 대조 (규칙 v2와 KLUE 사이에 들어감).

문장 속 아웃카운트, 주자 위치와 이름, 이닝, 점수, 투구 순서를 서비스 F/R 값과 직접 비교함.
  bad         값 하나라도 F/R과 다름 -> 삭제
  ok          비교한 값이 모두 맞음
  state_only  ok 이면서 상태·점수 말고 다른 주장이 없어 보임 -> KLUE 없이 유지
  skip        비교할 값이 없음 -> 기존대로 KLUE

KLUE가 맞는 상태 문장을 지우는 문제(p_support 0.0001~0.003) 때문에 넣음. KLUE는 학습 때 서비스 F 모양
("플레이 후 2사, 1루 (1루 강승호), 점수 두산 0-0 LG")과 상태 변화 서술을 본 적이 없음.
근거·말투를 학습 모양으로 바꿔 넣는 방법도 시험했지만 점수만 말하는 문장을 새로 떨어뜨려서 쓰지 않음.

한계: 허용어 목록과 규칙 문구는 실제 생성 문장 41개와 사람 채점 731문장을 보며 다듬은 것이라 새 문장으로 계속 확인 필요.
"""
import collections, re

try:
    from . import state_rule_check as S
except ImportError:  # ai/explain 폴더에서 스크립트로 실행할 때
    import state_rule_check as S

# ---------------- 서비스 F 읽기 ----------------
SCORE = r"(점수 \S+ \d+\s*[-:]\s*\d+ \S+)"
OUTMAP = {"0아웃": "무사", "1아웃": "1사", "2아웃": "2사"}


def _score(s):
    m = re.match(r"점수 (\S+) (\d+)\s*[-:]\s*(\d+) (\S+)", s)
    return f"점수 {m.group(1)} {m.group(2)} : {m.group(3)} {m.group(4)}" if m else s


def _names(s):
    """'(1루 강승호, 2루 김민석)' -> {1: '강승호', 2: '김민석'}"""
    m = re.search(r"\((.*?)\)", s)
    return {int(b): n for b, n in re.findall(r"([123])루\s+(\S+?)(?=,|$)", m.group(1))} if m else {}


def _bases(s):
    s = re.sub(r"\s*\(.*?\)", "", s).strip(" ,")
    if not s or s.startswith("주자 없음") or s == "없음":
        return "주자 없음"
    return s.replace(",", "·").replace("주자 ", "").strip()


def parse_service_line(t):
    """서비스 F/R 한 줄 -> (학습 형식 줄 목록, 정보 dict)."""
    t = t.strip()
    m = re.match(r"^(?:이번 플레이:|기록:)\s*(.+)$", t)
    if m:
        body = m.group(1).strip()
        rm = re.match(r"^([123])루주자\s+(\S+)\s*:\s*(.+)$", body)
        if rm:
            return [f"{rm.group(1)}루주자 {rm.group(2)}: {rm.group(3)}"], {}
        bm = re.match(r"^(\S+)\s*:\s*(.+)$", body)
        if bm:
            return [body], {"batter": (bm.group(1), bm.group(2))}
        return [body], {}
    m = re.match(r"^이 플레이로 득점:\s*(\S+)\s+(\d+)점$", t)
    if m:
        return [f"{m.group(1)} {m.group(2)}점 득점"], {}
    m = re.match(r"^이 타석 투구 수 (\d+)개", t)
    if m:
        return [f"투구 {m.group(1)}구"], {"pitch_total": int(m.group(1))}
    m = re.match(r"^플레이 후:?\s*(무사|[12]사|[0-3]아웃),?\s*(.*?)(?:,\s*" + SCORE + r")?$", t)
    if m:
        o = OUTMAP.get(m.group(1), m.group(1))
        first = "아웃카운트 3아웃, 이닝 종료" if o == "3아웃" else f"아웃카운트 {o}, 주자 {_bases(m.group(2))}".replace("주자 주자", "주자")
        info = {"post_names": _names(m.group(2)), "post_bases_any": _bases(m.group(2))}
        return [first] + ([_score(m.group(3))] if m.group(3) else []), info
    m = re.match(r"^(\d+회[초말]),?\s*(무사|[12]사),?\s*(.*?)(?:,\s*" + SCORE + r")?$", t)
    if m:
        return ([f"{m.group(1)} {m.group(2)} {_bases(m.group(3))}"] + ([_score(m.group(4))] if m.group(4) else []),
                {"pre_names": _names(m.group(3))})
    return [t], {}


# ---------------- 상태 읽기 ----------------
def parse_service_facts(facts, raw_relay=()):
    """facts: [{"id","text"}] (서비스 F 전체). raw_relay: R 원문 줄. 반환: state_rule_check 상태 + 이름 정보."""
    lines, info = [], {"pre_names": {}, "post_names": {}, "batter": None, "pitch_total": None}
    for f in facts:
        conv, inf = parse_service_line(f["text"])
        lines += conv
        for k, v in inf.items():
            info[k] = v
    st = S.parse_facts([{"id": f"F{i}", "text": t} for i, t in enumerate(lines, 1)], list(raw_relay))
    if info["batter"] and not st["batter"]:
        st["batter"] = info["batter"]; st["names"].add(info["batter"][0])
    st["pre_names"], st["post_names"] = info["pre_names"], info["post_names"]
    st["names"] |= set(info["pre_names"].values()) | set(info["post_names"].values())
    st["pitch_total"] = info["pitch_total"]
    return st


# ---------------- 추가 대조 (서비스 문장에서 자주 나오는 표현) ----------------
def check_named_bases(body, st, players=()):
    """'1루 강승호에서 2루 강승호로', '강승호 선수는 2루에 남은 채', '1루(문정빈)' 같은 주자 이름+베이스."""
    # 판정에서 빼는 것
    #  - '1루 주자 김상수', '1루주자 X'는 역할 이름이라 위치 주장으로 안 봄(출발 베이스는 state_rule_check의 runner_from 몫)
    #  - '2루수', '2루타'의 2는 베이스가 아님
    #  - '2루에서 포스아웃'은 아웃된 자리라 판정 안 함
    #  - 타석 단위 F에서는 한 주자가 여러 번 움직이므로, 주자 줄의 출발·도착 베이스도 허용
    res = []
    pre = {n: b for b, n in st["pre_names"].items()}
    post = {n: b for b, n in st["post_names"].items()}
    froms, dests = collections.defaultdict(set), collections.defaultdict(set)
    for r in st["runners"]:
        froms[r["name"]].add(r["from"])
        if isinstance(r["dest"], int) and r["dest"] in (1, 2, 3):
            dests[r["name"]].add(r["dest"])
    B = r"([123])\s*루(?!\s*수|\s*타|\s*주자)"
    OUTNEAR = re.compile(r"^\s*(?:에서\s*)?.{0,4}(?:포스\s*아웃|태그\s*아웃|아웃|견제사|도루\s*실패)")
    for n in sorted(set(pre) | set(post) | set(froms), key=len, reverse=True):
        e = re.escape(n)
        pats = [(rf"{B}\s+{e}(?:\s*선수)?\s*(에서|으로|로)", None),
                (rf"{B}\s*\(\s*{e}\s*\)()", None),
                (rf"{e}(?:\s*선수)?\s*(?:는|은|가|이)?\s*{B}\s*(에\s*남|에\s*있던|에\s*머물|에서\s*출발|로\s*(?:진루|이동|가)|까지\s*(?:진루|이동|가))", None)]
        for p, _ in pats:
            for m in re.finditer(p, body):
                b, tail = int(m.group(1)), (m.group(2) or "")
                if OUTNEAR.match(body[m.end(1):m.end(1) + 12].lstrip("루")):
                    continue
                if "에서" in tail or "있던" in tail:
                    cand, when = {pre.get(n)} | froms[n], "전"
                elif re.search(r"로|까지|남|머물", tail):
                    cand, when = {post.get(n)} | dests[n], "후"
                else:
                    cand, when = {pre.get(n), post.get(n)} | froms[n] | dests[n], "전후"
                cand.discard(None)
                if cand:
                    res.append(("named_base", b in cand, f"{n} {b}루({when})" + ("" if b in cand else f" F:{sorted(cand)}")))
        # 이름과 떨어진 도착 표현: '양석환 선수는 … 1루로 진루했습니다' (같은 절 안, 쉼표 전까지)
        if n in post:
            ok_set = {post[n]} | dests[n] | froms[n]
            for m in re.finditer(e, body):
                clause = re.split(r"[,.]", body[m.end():], maxsplit=1)[0]
                if any(x != n and x in clause for x in set(pre) | set(post) | set(froms)):
                    continue  # 다른 주자가 같은 절에 나오면 누구 얘기인지 불분명
                dm = re.search(r"([123])\s*루(?!\s*수|\s*타)\s*(?:로|으로|에|까지)\s*(?:다시\s*)?(진루|나가|나갔|출루|이동|도착|살아|걸어|남)", clause)
                if dm and not any(r[0] == "named_base" and r[2].startswith(n) for r in res):
                    b = int(dm.group(1))
                    res.append(("named_dest", b in ok_set, f"{n} {b}루 도착" + ("" if b in ok_set else f" F:{sorted(ok_set)}")))
    # F에 주자로 안 나오는 선수를 베이스에 보낸 문장: '박성한 선수가 1루에 나가' (박성한은 이 플레이 주자가 아님)
    known = set(pre) | set(post) | set(froms)
    for n in sorted(set(players) - known, key=len, reverse=True):
        m = re.search(rf"{re.escape(n)}(?:\s*선수)?\s*(?:가|이|는|은)\s*[^,.]{{0,6}}?([123])\s*루(?!\s*수|\s*타)\s*(?:로|으로|에|까지)\s*"
                      r"(?:다시\s*)?(진루|나가|나갔|출루|이동|도착|살아|걸어|남)", body)
        if m:
            res.append(("named_dest", False, f"{n} {m.group(1)}루: F에 이 선수가 주자로 없음"))
    return res


ORD = re.compile(r"(\d+)\s*번째\s*(공|볼|스트라이크)")


def check_ordinal_pitches(body, st):
    """'7번째 공까지', '4번째 볼을 골라내' -> 투구 수, 볼 개수와 대조."""
    res = []
    total = st.get("pitch_total") or (max(st["pitches"]) if st["pitches"] else None)
    for m in ORD.finditer(body):
        n, kind = int(m.group(1)), m.group(2)
        if kind == "공":
            if total is None:
                continue
            last = re.match(r"\s*(?:까지|만에|째)|.{0,6}(?:끝에|마지막)", body[m.end():m.end() + 10])
            ok = n == total if last else n <= total
            res.append(("pitch_total", ok, f"{n}번째 공" + ("" if ok else f" F:{total}구")))
        else:
            seq = [st["pitches"][k] for k in sorted(st["pitches"])]
            if not seq:
                continue
            word = "볼" if kind == "볼" else "스트라이크"
            cnt = sum(1 for x in seq if x == word or (word == "스트라이크" and x == "헛스윙"))
            ok = n <= cnt
            res.append(("pitch_ord", ok, f"{n}번째 {kind} R:{cnt}개"))
    return res


# state_rule_check의 허용어에 서비스 문장(합니다체)에서 나온 연결 표현을 더함
EXTRA_FILLER = sorted("""
이 플레이가 나오기 전에는|나오기 전에는|이 플레이가|이 도루로|이 볼넷으로|이 타석에서|이 타석|타자였던|직접|나가면서|나가며|나가|
그대로 유지되었고|그대로 유지|유지되었고|유지되었어요|유지되었|유지|주자 위치는|위치는|바뀌었습니다|바뀌었어요|바뀌었|바뀌|
남은 채|남은|남아|공격이 끝났습니다|공격이 끝났어요|끝났습니다|끝났어요|끝났|끝|없이|에만|있던|있었|상황이었습니다|상황이었어요|
번째 공까지 승부한 끝에|번째 공까지|번째 볼을 골라내며|번째 볼을|골라내며|승부한 끝에|진루했습니다|진루했어요|진루|되면서|
습니다|었습니다|었|았|했|으로|(|)|번째|공까지|볼을|까지|
변함이 없었습니다|변함이 없습니다|변함이 없었|변함이 없|변함없이|변함없|변화 없이|여전히|계속|그대로|동일하게|전과 동일|
늘어났고|늘어났으며|늘어났습니다|늘어났|늘어나지 않아|늘어나지 않고|늘어나지|머물렀고|머물렀으며|머물렀습니다|머물렀|
진출했고|진출했습니다|진출했|진출|생겼으며|생겼고|생겼|득점하지 못해|득점하지 못하고|득점하지 못했|하여|하면서|이번 타석에서|공이|
없는 상태를 유지했습니다|없는 상태를 유지|없는 상태|없으며|없고|플레이 전후|플레이 전에는|플레이 전과|플레이 전|-|
변화가 없었습니다|변화가 없습니다|변화가 없었|변화가 없|변화 없|이어졌고|이어졌습니다|이어졌|증가 없이|증가|
출루하였으며|출루했으며|출루했고|출루했습니다|출루하며|출루|타자|채워지며|채워졌|더해
""".replace("\n", "").split("|"), key=len, reverse=True)
EXTRA_FILLER = [x for x in EXTRA_FILLER if x.strip()]


def state_check(sentence, facts, raw_relay=(), players=()):
    """반환: {"status": ok|bad|skip, "state_only", "checks", "why"}"""
    st = parse_service_facts(facts, raw_relay)
    body = re.sub(r"\s+", " ", S.TAG.sub(" ", sentence)).strip()
    # '0-2' 같은 하이픈 점수도 점수 대조(A:B)에 걸리게 바꿈
    sentence = re.sub(r"(?<![\d.])(\d{1,2})\s*-\s*(\d{1,2})(?![\d.])", r"\1:\2", sentence)
    body = re.sub(r"\s+", " ", S.TAG.sub(" ", sentence)).strip()
    base = S.check(sentence, st, players=list(players))
    checks = base["checks"] + check_named_bases(body, st, players) + check_ordinal_pitches(body, st)
    # 이름+베이스를 이 함수가 따로 봤으면 기존 'bases'(아웃 표현 뒤 주자) 판정은 그대로 둠
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
        for ph in EXTRA_FILLER + S.FILLER_PHRASES:
            rest = rest.replace(ph, " ")
        rest = re.sub(r"[\d\s,.·:\-]", "", rest)
        state_only = rest == ""
    return {"status": status, "state_only": state_only, "checks": checks,
            "why": "; ".join(f"{k}:{d}" for k, ok, d in bad)}


def decide(sentence, facts, raw_relay=(), players=(), p_support=None, cited_evidence=None, threshold=None):
    """한 문장 판정. sentence는 근거 표시([F1][R3][K:card])가 붙은 문장.
    p_support: [(문장, 근거)] -> [P(지지)]. 규칙으로 결론이 안 나면 (문장, cited_evidence)로 부름.
    반환: {"keep": True/False/None, "route": rule_bad|rule_state_only|klue, "p", "rule"}"""
    r = state_check(sentence, facts, raw_relay, players)
    if r["status"] == "bad":
        return {"keep": False, "route": "rule_bad", "p": None, "rule": r}
    if r["status"] == "ok" and r["state_only"]:
        return {"keep": True, "route": "rule_state_only", "p": None, "rule": r}
    if p_support is None or threshold is None:
        return {"keep": None, "route": "klue", "p": None, "rule": r}
    body = re.sub(r"\s+", " ", S.TAG.sub(" ", sentence)).strip()
    p = float(p_support([(body, cited_evidence)])[0])
    return {"keep": p >= threshold, "route": "klue", "p": round(p, 4), "rule": r}
