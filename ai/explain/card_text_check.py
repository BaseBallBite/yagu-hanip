"""카드만 인용한 설명 문장을 카드 본문과 직접 대조하는 규칙.

KLUE가 카드 정의를 거의 그대로 풀어 쓴 문장도 지우는 경우가 있어서 추가함
(BE1 3경기: "1루타는 ... 1루까지 ... 안타" p 0.0008, 카드에는 "1루까지 가면 단타"만 있음.
 볼넷 정의 문장은 거의 같은 문장 3개 중 하나만 p 0.0114로 삭제).

대상: 인용이 전부 카드 ID인 문장. F/R을 같이 인용한 문장은 건드리지 않음.
판정
  covered  카드 본문만으로 문장 내용이 다 설명됨 -> 모델 없이 유지
  None     판단 못 함 -> 지금처럼 모델로 넘김
이 규칙은 지우지 않음. 모델 삭제를 줄이기만 함.

covered 조건 (전부 만족)
  1. 선수 이름이 없음 (카드에는 이 경기 선수가 없음)
  2. 숫자·베이스·아웃 표현(4개, 1루, 2루타, 1사, 만루 등)이 카드의 한 구절 안에 같이 있음
     -> "2루타는 1루까지" 처럼 카드 단어를 섞어 바꾼 문장은 통과 못 함
  3. 카드에서 "X 없이"로 나온 X(실책, 수비 실수 등)를 문장이 부정 표현 없이 말하면 통과 못 함
  4. 문장 단어의 85% 이상이 카드 본문(별칭 포함)에 있음. 말하다·뜻하다·규칙 같은 정의 문형 단어는 셈에서 뺌
카드 별칭(cards/*/*.yaml의 aliases, 예: 안타 = 단타·1루타)은 카드 제목과 같은 말로 봄.
"""
import re
from pathlib import Path

CARD_ID = re.compile(r"^(rule|term)\.[a-z0-9_]+$")

# 정의 문형에 흔한 말. 내용 판단에 안 씀
FILLER = {"말합니다", "말해요", "말하며", "말하고", "뜻합니다", "뜻해요", "뜻하며", "뜻하고", "의미합니다", "의미해요",
          "규칙", "규칙입니다", "규칙이에요", "규칙으로", "경우", "경우를", "경우에", "것", "것을", "것이", "것은",
          "것입니다", "거예요", "때", "때를", "이를", "이", "그", "이런", "이렇게", "합니다", "해요", "됩니다", "돼요",
          "있습니다", "있어요", "수", "등", "또는", "즉", "바로", "모두", "하는", "되는", "입니다", "이에요", "예요",
          "부릅니다", "불러요", "가리킵니다", "가리켜요", "안전하게"}

JOSA = sorted(["으로부터", "에서부터", "까지는", "까지도", "에서는", "으로는", "이라고", "라고", "이라는", "라는",
               "에서", "으로", "까지", "부터", "에게", "처럼", "보다", "이나", "하고", "이며", "이고", "이면",
               "은", "는", "이", "가", "을", "를", "의", "에", "로", "도", "만", "과", "와", "나", "면", "며", "고"],
              key=len, reverse=True)
ENDINGS = sorted(["했습니다", "됐습니다", "되었습니다", "합니다", "입니다", "습니다", "니다", "어요", "아요", "해요",
                  "돼요", "예요", "에요", "이에요", "하는", "되는", "하여", "해서", "하면", "되면", "는", "은", "던",
                  "고", "며", "면", "서", "게", "지"], key=len, reverse=True)

# 베이스에 나가는 동작. 카드가 이 중 하나를 쓰면 문장이 다른 것을 써도 같은 말로 봄
MOVE = {"진루", "나가", "나간", "들어가", "들어와", "살아", "살", "가", "간", "걸어", "출루"}

STRICT = re.compile(r"[1-4]루타|단타|홈런|만루|무사|[123]사|[0-9]+\s*(?:개|루|구|아웃|점|명|번|초)|[0-9]+")
NEG_MARK = ("없이", "않", "아니", "없는", "없고", "못")

_ALIAS_CACHE = {}


def load_aliases(cards_dir=None):
    """cards 폴더 yaml에서 {카드 ID: [제목, 별칭...]}. yaml 패키지 없이 id/title/aliases만 읽음."""
    if cards_dir is None:
        cards_dir = Path(__file__).resolve().parents[2] / "cards"
    cards_dir = Path(cards_dir)
    key = str(cards_dir)
    if key in _ALIAS_CACHE:
        return _ALIAS_CACHE[key]
    out = {}
    for p in sorted(cards_dir.glob("**/*.yaml")):
        cid, title, al, in_al = None, None, [], False
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith("id:"):
                cid = line[3:].strip().strip("'\"")
            elif line.startswith("title:"):
                title = line[6:].strip().strip("'\"")
            elif line.startswith("aliases:"):
                in_al = True
                rest = line[8:].strip()
                if rest.startswith("[") and rest.endswith("]"):
                    al += [x.strip().strip("'\"") for x in rest[1:-1].split(",") if x.strip()]
                    in_al = False
            elif in_al and line.startswith("- "):
                al.append(line[2:].strip().strip("'\""))
            elif in_al and not line.startswith(" "):
                in_al = False
        if cid and CARD_ID.match(cid):
            out[cid] = [x for x in [title] + al if x]
    _ALIAS_CACHE[key] = out
    return out


BASE_HIT = re.compile(r"^(?:[1-4]루타|단타|홈런)$")


def _canon(text, names):
    """별칭을 카드 제목으로 바꿈(긴 것부터). names: [(별칭, 제목)]
    1루타·단타처럼 몇 루까지 갔는지 담은 말은 제목으로 바꾸지 않고 '단타'로만 맞춤(2번 조건에서 씀)."""
    text = text.replace("1루타", "단타")
    for a, t in names:
        if a != t and not BASE_HIT.match(a) and a in text:
            text = text.replace(a, t)
    return text


def _chunks(text):
    """괄호 밖 쉼표·마침표 기준 구절."""
    out, buf, depth = [], "", 0
    for ch in text:
        depth += ch == "("
        depth -= ch == ")" and depth > 0
        if ch in ",.!?/" and depth == 0:
            out.append(buf)
            buf = ""
        else:
            buf += ch
    out.append(buf)
    return [c.strip() for c in out if c.strip()]


def _stem(w):
    w = re.sub(r"[^\w가-힣·]", "", w)
    for _ in range(2):
        for j in JOSA + ENDINGS:
            if w.endswith(j) and len(w) - len(j) >= 1:
                w = w[: -len(j)]
                break
    return w


def _strict(s):
    return {re.sub(r"\s+", "", m) for m in STRICT.findall(s)}


def _negated_terms(card):
    """카드의 'X 없이', 'X이나 Y 없이'에서 X, Y 어간 (바로 앞 단어와 '이나/나/와/과'로 이어진 단어만)."""
    out = set()
    for c in _chunks(card):
        ws = c.split()
        for i, w in enumerate(ws):
            if w != "없이" or i == 0:
                continue
            j = i - 1
            out.add(_stem(ws[j]))
            while j > 0 and re.search(r"(이나|나|와|과)$", ws[j - 1]):
                j -= 1
                out.add(_stem(re.sub(r"(이나|나|와|과)$", "", ws[j])))
    return {t for t in out if len(t) >= 2}


def _either(card):
    """카드의 'X나 Y', 'X 또는 Y'에서 숫자·베이스·아웃 표현 쌍. 문장이 한쪽만 말하면 조건을 좁힌 것."""
    out = []
    for m in re.finditer(r"(\S+?)(?:이나|나)?\s+또는\s+(\S+)|(\S+?)(?:이나|나)\s+(\S+)", card):
        a, b = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        sa, sb = _strict(a), _strict(b)
        if sa and sb:
            out.append((sa, sb))
    return out


def card_check(sentence, card_texts, players=(), card_ids=(), aliases=None):
    """sentence: 근거 표시 뺀 문장. card_texts: 인용한 카드 본문 목록.
    돌려줌 {"status": "covered"|None, "why": str}"""
    if aliases is None:
        try:
            aliases = load_aliases()
        except OSError:
            aliases = {}
    names = []
    for cid in card_ids:
        ns = aliases.get(cid) or []
        if ns:
            names += [(a, ns[0]) for a in ns]
    names.sort(key=lambda x: -len(x[0]))
    sent = _canon(re.sub(r"\[[^\]]*\]", "", sentence), names).strip()
    card = _canon(" ".join(card_texts), names)
    card = re.sub(r"\(출처:[^)]*\)", "", card)
    card_flat = re.sub(r"\s+", "", card)

    for p in players:
        if p and p in sent:
            return {"status": None, "why": f"선수 이름 {p}"}
    # 2. 숫자·베이스·아웃 표현은 카드 한 구절 안에 같이 있어야 함
    for sc in _chunks(sent):
        need = _strict(sc)
        if need and not any(need <= _strict(cc) for cc in _chunks(card)):
            return {"status": None, "why": f"카드 구절에 같이 없음: {sorted(need)}"}
    # 2-1. 카드의 'X나 Y' 조건에서 한쪽만 말함 (예: 카드 '무사나 1사', 문장 '1사에')
    have = _strict(sent)
    for sa, sb in _either(card):
        if bool(sa & have) != bool(sb & have):
            return {"status": None, "why": f"카드는 {sorted(sa)} 또는 {sorted(sb)}인데 한쪽만 말함"}
    # 3. 카드에서 '없이'로 부정된 말을 부정 없이 씀
    if not any(m in sent for m in NEG_MARK):
        for t in _negated_terms(card):
            if t in sent:
                return {"status": None, "why": f"카드는 '{t} 없이'인데 문장에 부정이 없음"}
    # 4. 단어 겹침
    words = [w for w in re.split(r"\s+", sent) if w]
    content, miss = 0, []
    for w in words:
        if re.sub(r"[^\w가-힣]", "", w) in FILLER or _stem(w) in FILLER or not _stem(w):
            continue
        content += 1
        st = _stem(w)
        if st in MOVE and any(m in card_flat for m in ("가면", "가요", "나가", "나간", "진루", "들어와", "살면")):
            continue
        if st not in card_flat and (len(st) < 3 or st[:2] not in card_flat):
            miss.append(w)
    if content == 0:
        return {"status": None, "why": "내용 단어 없음"}
    cover = 1 - len(miss) / content
    if cover < 0.85:
        return {"status": None, "why": f"카드에 없는 말 {len(miss)}/{content}: {' '.join(miss[:5])}"}
    return {"status": "covered", "why": f"카드 본문과 일치 {content - len(miss)}/{content}"}
