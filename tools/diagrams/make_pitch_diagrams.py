#!/usr/bin/env python3
"""구종 도식 생성기. 실행: python3 make_pitch_diagrams.py  (같은 폴더에 term.<이름>.svg 14개와 preview.html 생성)

그림은 모양을 보여주는 도식이고 실제 움직임 크기와 다를 수 있음.
오른손 투수 기준. 위에서 본 모습(좌우 움직임)과 옆에서 본 모습(낙차) 두 칸.
"""
import math
from pathlib import Path

FONT = "'Noto Sans KR','Apple SD Gothic Neo','Malgun Gothic','WenQuanYi Zen Hei',sans-serif"
INK, MUTED, LINE, ACCENT, GROUND = "#1f2933", "#7b8794", "#cbd2d9", "#4B1E8A", "#f1f3f5"

# id, 제목, dx(양수=글러브 쪽, 음수=팔 쪽), drop(음수=아래), 설명, 모양
PITCHES = [
    ("fastball", "직구(포심)", 0, 0, "거의 휘지 않고 곧게 와요", "straight"),
    ("sinker", "싱커(투심)", -12, -14, "팔 쪽으로 움직이며 가라앉아요", "late"),
    ("cutter", "커터", 8, -3, "끝에서 글러브 쪽으로 살짝 휘어요", "late"),
    ("slider", "슬라이더", 22, -10, "글러브 쪽으로 휘며 조금 떨어져요", "late"),
    ("sweeper", "스위퍼", 42, -8, "글러브 쪽으로 옆으로 크게 휘어요", "late"),
    ("slurve", "슬러브", 28, -26, "옆으로 휘면서 아래로도 떨어져요", "late"),
    ("curveball", "커브", 16, -48, "위에서 아래로 크게 떨어져요", "late"),
    ("knuckle_curve", "너클커브", 14, -52, "커브처럼 크게 떨어지고 흔들려요", "wobble_small"),
    ("forkball", "포크볼", 0, -52, "회전이 적고 뚝 떨어져요", "late"),
    ("splitter", "스플리터", 0, -42, "직구처럼 오다 아래로 떨어져요", "late"),
    ("changeup", "체인지업", -14, -32, "느리게 와서 팔 쪽으로 떨어져요", "late"),
    ("eephus", "이퓨스", 0, 0, "아주 높이 떴다가 느리게 떨어져요", "eephus"),
    ("screwball", "스크루볼", -28, -30, "팔 쪽으로 휘며 떨어져요", "late"),
    ("knuckleball", "너클볼", 0, -10, "불규칙하게 흔들려요", "wobble"),
]

# 공이 홈까지 가는 시간(초). 빠를수록 짧게. 실제 비율을 대략 따름
MOVE = {"fastball":0.7,"sinker":0.72,"cutter":0.74,"slider":0.8,"sweeper":0.85,"slurve":0.9,"curveball":1.1,
        "knuckle_curve":1.05,"forkball":0.9,"splitter":0.85,"changeup":0.95,"eephus":1.9,"screwball":0.95,"knuckleball":1.2}
HOLD = 1.0

W, H = 420, 300


def f(x):
    return f"{x:.1f}"


def top_path(dx, kind):
    x0, y0, y1 = 80, 28, 190
    x1 = x0 + dx
    if kind == "eephus":
        return f"M{x0},{y0} L{x0},{y1}"
    if kind in ("wobble", "wobble_small"):
        amp = 9 if kind == "wobble" else 4
        pts = []
        n = 14
        for i in range(n + 1):
            t = i / n
            y = y0 + (y1 - y0) * t
            x = x0 + dx * t * t + (amp * math.sin(t * 9) if kind == "wobble" else amp * math.sin(t * 9) * t)
            pts.append((x, y))
        return "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts)
    if kind == "straight":
        return f"M{x0},{y0} L{x1},{y1}"
    return f"M{x0},{y0} C{x0},{y0 + 100} {f(x0 + dx * 0.25)},{y0 + 130} {f(x1)},{y1}"


def side_path(drop, kind):
    x0, y0 = 250, 80
    x1, ref_y = 400, 130
    y1 = ref_y - drop  # drop 음수 -> y 아래(숫자 큼)
    if kind == "eephus":
        return f"M{x0},{y0} C290,4 360,4 {x1},{ref_y}"
    if kind in ("wobble", "wobble_small"):
        amp = 7 if kind == "wobble" else 3
        pts = []
        n = 14
        for i in range(n + 1):
            t = i / n
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t * t + (y0 and amp * math.sin(t * 9) * (1 if kind == "wobble" else t))
            pts.append((x, y))
        return "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts)
    if kind == "straight":
        return f"M{x0},{y0} L{x1},{ref_y}"
    return f"M{x0},{y0} C{x0 + 60},{y0 + 20} {x0 + 110},{f(y1 - 12 if drop else y1)} {x1},{f(y1)}"


def ball(pid, which, pathd, m, total):
    # 도식 위를 달리는 공(SMIL). 선은 공이 지나간 만큼 그려짐
    kt = f"0;{m / total:.3f};1"
    return (f'<path id="{pid}-{which}" d="{pathd}" fill="none" stroke="none"/>'
            f'<path d="{pathd}" pathLength="1" stroke="{ACCENT}" stroke-width="3" fill="none" stroke-linecap="round" stroke-dasharray="1" stroke-dashoffset="1">'
            f'<animate attributeName="stroke-dashoffset" values="1;0;0" keyTimes="{kt}" dur="{total}s" repeatCount="indefinite"/></path>'
            f'<g><circle r="6" fill="#ffffff" stroke="{ACCENT}" stroke-width="1.6"/><path d="M-3.5,-3.5 Q0,0 -3.5,3.5 M3.5,-3.5 Q0,0 3.5,3.5" stroke="{ACCENT}" stroke-width="1" fill="none"/>'
            f'<animateMotion dur="{total}s" repeatCount="indefinite" keyPoints="0;1;1" keyTimes="{kt}" calcMode="linear"><mpath href="#{pid}-{which}"/></animateMotion></g>')


def svg(pid, title, dx, drop, note, kind, animate=False):
    ref_top = "M80,28 L80,190"
    ref_side = "M250,80 L400,130"
    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{title}의 움직임 도식">')
    s.append(f'<rect width="{W}" height="{H}" rx="12" fill="#ffffff" stroke="{LINE}"/>')
    s.append(f'<text x="18" y="30" font-family="{FONT}" font-size="18" font-weight="700" fill="{INK}">{title}</text>')
    s.append(f'<text x="18" y="50" font-family="{FONT}" font-size="12.5" fill="{MUTED}">{note}</text>')
    # 위에서 본 칸
    s.append(f'<g transform="translate(0,52)">')
    s.append(f'<text x="18" y="14" font-family="{FONT}" font-size="11" fill="{MUTED}">위에서 본 모습</text>')
    s.append(f'<rect x="28" y="22" width="104" height="188" rx="8" fill="{GROUND}"/>')
    s.append(f'<circle cx="80" cy="30" r="6" fill="{MUTED}"/>')  # 마운드
    s.append(f'<path d="M72,196 L88,196 L90,204 L80,210 L70,204 Z" fill="#ffffff" stroke="{MUTED}"/>')  # 홈
    s.append(f'<text x="30" y="224" font-family="{FONT}" font-size="10.5" fill="{MUTED}">3루 쪽</text>')
    s.append(f'<text x="132" y="224" text-anchor="end" font-family="{FONT}" font-size="10.5" fill="{MUTED}">1루 쪽</text>')
    s.append(f'<path d="{ref_top}" stroke="{MUTED}" stroke-width="1.4" stroke-dasharray="4 4" fill="none" transform="translate(0,0)"/>' if kind != "straight" else "")
    m = MOVE[pid]; total = round(m + HOLD, 2)
    if animate:
        s.append(ball(pid, "top", top_path(dx, kind), m, total))
    else:
        s.append(f'<path d="{top_path(dx, kind)}" stroke="{ACCENT}" stroke-width="3" fill="none" stroke-linecap="round"/>')
        ex = 80 + dx
        s.append(f'<circle cx="{f(ex)}" cy="190" r="5" fill="{ACCENT}"/>')
    s.append("</g>")
    # 옆에서 본 칸
    s.append(f'<g transform="translate(0,52)">')
    s.append(f'<text x="242" y="14" font-family="{FONT}" font-size="11" fill="{MUTED}">옆에서 본 모습</text>')
    s.append(f'<rect x="228" y="22" width="178" height="188" rx="8" fill="{GROUND}"/>')
    s.append(f'<line x1="228" y1="190" x2="406" y2="190" stroke="{MUTED}" stroke-width="1.2"/>')
    s.append(f'<circle cx="250" cy="80" r="6" fill="{MUTED}"/>')  # 투수 손
    s.append(f'<rect x="394" y="98" width="8" height="64" fill="none" stroke="{MUTED}" stroke-width="1.5"/>')  # 존
    s.append(f'<text x="398" y="92" text-anchor="middle" font-family="{FONT}" font-size="10.5" fill="{MUTED}">존</text>')
    s.append(f'<text x="250" y="104" text-anchor="middle" font-family="{FONT}" font-size="10.5" fill="{MUTED}">투수</text>')
    if kind != "straight":
        s.append(f'<path d="{ref_side}" stroke="{MUTED}" stroke-width="1.4" stroke-dasharray="4 4" fill="none"/>')
    if animate:
        s.append(ball(pid, "side", side_path(drop, kind), m, total))
    else:
        s.append(f'<path d="{side_path(drop, kind)}" stroke="{ACCENT}" stroke-width="3" fill="none" stroke-linecap="round"/>')
    s.append("</g>")
    s.append(f'<text x="18" y="{H - 10}" font-family="{FONT}" font-size="10.5" fill="{MUTED}">점선은 직구가 가는 길이에요. 오른손 투수 기준 도식이고 실제 크기와 달라요.</text>')
    s.append("</svg>")
    return "\n".join(x for x in s if x)


# ---------- 포수 쪽에서 본 장면(투수 모션 + 타자) ----------
RELEASE = 0.6   # 팔을 휘두르기 시작해서 공을 놓기까지(초)
ZX, ZY, ZW, ZH = 186, 146, 48, 42  # 스트라이크 존: 타자 무릎~어깨와 벨트 중간


def scene_path(dx, drop, kind):
    x0, y0 = 202, 32
    xe = 210 + dx * 0.9
    ye = 167 - drop * 0.55
    if kind == "eephus":
        return f"M{x0},{y0} C{x0},4 {xe},14 {xe},{ye}"
    if kind in ("wobble", "wobble_small"):
        amp = 7 if kind == "wobble" else 3
        pts = []
        n = 16
        for i in range(n + 1):
            t = i / n
            x = x0 + (xe - x0) * t + amp * math.sin(t * 10) * t
            y = y0 + (ye - y0) * t
            pts.append((x, y))
        return "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts)
    if kind == "straight":
        return f"M{x0},{y0} L{f(xe)},{f(ye)}"
    return (f"M{x0},{y0} C{f(x0 + dx * 0.05)},{f(y0 + (ye - y0) * 0.45)} "
            f"{f(210 + dx * 0.35)},{f(y0 + (ye - y0) * 0.78)} {f(xe)},{f(ye)}")


SKIN, JERSEY, PANTS, CAP, GLOVE, WOOD, OUTL = "#ffe0c6", "#ffffff", "#ffffff", "#4B1E8A", "#b9783a", "#e9b777", "#25232e"
TOPC, GRAYS, BLUSH = "#7a4bc2", "#9097a3", "#ff9fa8"
_SLEEVE = [CAP]
SOCK, CLEAT, SKIN_D = "#4B1E8A", "#212529", "#d9a77f"


FLAT = True


def _mix(c, t, w):
    c = c.lstrip("#")
    r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    tr, tg, tb = (255, 255, 255) if w else (0, 0, 0)
    return "#%02x%02x%02x" % (round(r + (tr - r) * t), round(g + (tg - g) * t), round(b + (tb - b) * t))


GRAD_BASE = [SKIN, JERSEY, PANTS, CAP, GLOVE, WOOD, SOCK, CLEAT]


def grad_defs():
    o = ["<defs>"]
    for c in GRAD_BASE:
        k = c.lstrip("#")
        lt, dk = _mix(c, 0.4, True), _mix(c, 0.22, False)
        o.append(f'<radialGradient id="r{k}" cx="0.36" cy="0.3" r="0.8"><stop offset="0" stop-color="{lt}"/><stop offset="0.5" stop-color="{c}"/><stop offset="1" stop-color="{dk}"/></radialGradient>')
        o.append(f'<linearGradient id="l{k}" x1="0" y1="0" x2="1" y2="0.3"><stop offset="0" stop-color="{lt}"/><stop offset="0.45" stop-color="{c}"/><stop offset="1" stop-color="{dk}"/></linearGradient>')
    o.append("</defs>")
    return "".join(o)


def add_defs(svg_text):
    i = svg_text.index(">", svg_text.index("<svg")) + 1
    return svg_text[:i] + grad_defs() + svg_text[i:]


def _taper(x1, y1, x2, y2, w1, w2):
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    p = [(x1 + nx * w1 / 2, y1 + ny * w1 / 2), (x2 + nx * w2 / 2, y2 + ny * w2 / 2),
         (x2 - nx * w2 / 2, y2 - ny * w2 / 2), (x1 - nx * w1 / 2, y1 - ny * w1 / 2)]
    d = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in p) + " Z"
    return [("path", d), ("circle", (x1, y1, w1 / 2)), ("circle", (x2, y2, w2 / 2))]


class Fig:
    """도형을 모아 두었다가 외곽선 한 번, 색 한 번 두 번에 나눠 그림 -> 이음매 없는 외곽선"""
    def __init__(self):
        self.items = []

    def add(self, shapes, color, outline=True):
        self.items.append((shapes, color, outline))

    def limb(self, a, b, w1, w2, color):
        self.add(_taper(*a, *b, w1, w2), color)

    def svg(self):
        def el(sh, fill, stroke=None, sw=0):
            k, v = sh
            st = f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"' if stroke else ""
            if not stroke and len(fill) > 7:
                return ""
            if not stroke and fill in GRAD_BASE and not FLAT:
                fill = f"url(#{'l' if k == 'path' else 'r'}{fill.lstrip('#')})"
            if k == "path":
                return f'<path d="{v}" fill="{fill}"{st}/>'
            if k == "circle":
                return f'<circle cx="{f(v[0])}" cy="{f(v[1])}" r="{f(v[2])}" fill="{fill}"{st}/>'
            if k == "ellipse":
                return f'<ellipse cx="{f(v[0])}" cy="{f(v[1])}" rx="{f(v[2])}" ry="{f(v[3])}" fill="{fill}"{st}/>'
        out = []
        for shapes, color, ol in self.items:
            if ol:
                out += [el(sh, OUTL, OUTL, 3) for sh in shapes]
        for shapes, color, ol in self.items:
            out += [el(sh, color) for sh in shapes]
        return "".join(out)


def _leg(F, hip, knee, ankle, front=True):
    F.limb(hip, knee, 12, 10, PANTS)
    F.limb(knee, ankle, 10, 8.5, PANTS)
    mid = (knee[0] + (ankle[0] - knee[0]) * 0.5, knee[1] + (ankle[1] - knee[1]) * 0.5)
    F.limb(mid, ankle, 8.7, 8.2, SOCK)
    sx = 3 if front else -3
    F.add([("ellipse", (ankle[0] + sx, ankle[1] + 2, 7.6, 4.2))], JERSEY)


def _arm(F, sh, el, hand, glove=False, mitt=False):
    F.limb(sh, el, 9, 7.8, _SLEEVE[0])
    F.limb(el, hand, 7.8, 6.4, _SLEEVE[0])
    if glove:
        F.add([("ellipse", (hand[0], hand[1], 7.4, 8.4))], GLOVE)
        F.add([("path", f"M{hand[0] - 4},{hand[1] + 1} Q{hand[0]},{hand[1] + 4} {hand[0] + 4},{hand[1] + 1}")], GLOVE, outline=False)
    else:
        F.add([("circle", (hand[0], hand[1], 4.6))], JERSEY if mitt else SKIN)


def _torso(F, cx, top=47, waist=64, lean=0):
    d = (f"M{cx - 12 + lean},{top + 3} Q{cx + lean},{top - 3} {cx + 12 + lean},{top + 3} "
         f"L{cx + 9},{waist} L{cx - 9},{waist} Z")
    F.add([("path", d)], TOPC)
    F.limb((cx + lean, top + 3), (cx, waist - 4), 2.2, 2.2, JERSEY)
    F.add([("path", f"M{cx - 9},{waist - 3.5} L{cx + 9},{waist - 3.5} L{cx + 9},{waist} L{cx - 9},{waist} Z")], JERSEY)


def _head(F, cx, cy, face=0):
    F.add([("ellipse", (cx, cy, 11.4, 10.6))], SKIN)
    F.add([("ellipse", (cx - 6.4 + face * 0.5, cy + 4.2, 2.8, 1.9)), ("ellipse", (cx + 6.4 + face * 0.5, cy + 4.2, 2.8, 1.9))], BLUSH, outline=False)
    F.add([("path", f"M{cx - 11.8},{cy - 1.5} Q{cx - 11.8},{cy - 13.5} {cx},{cy - 13.5} Q{cx + 11.8},{cy - 13.5} {cx + 11.8},{cy - 1.5} Z")], CAP)
    F.add([("path", f"M{cx - 11.6},{cy - 4.5} L{cx + 11.6},{cy - 4.5} L{cx + 11.8},{cy - 1.5} L{cx - 11.8},{cy - 1.5} Z")], TOPC, outline=False)
    F.add([("ellipse", (cx + face, cy - 0.8, 12.2, 2.4))], CAP)
    fx = face * 0.5
    F.add([("circle", (cx - 3.8 + fx, cy + 2.6, 1.5)), ("circle", (cx + 3.8 + fx, cy + 2.6, 1.5))], OUTL, outline=False)
    F.add([("ellipse", (cx + fx, cy + 6.4, 1.6, 1.1))], OUTL, outline=False)


def pitcher_pose(kind):
    F = Fig()
    _SLEEVE[0] = GRAYS
    hipL, hipR = (206.5, 64), (213.5, 64)
    if kind == "A":   # 준비: 앞다리를 들고 두 손을 가슴 앞에
        _leg(F, hipL, (205.5, 80), (204.5, 96), False)
        _leg(F, hipR, (224, 71), (222, 86))
        _torso(F, 210)
        _arm(F, (201, 50), (198, 60), (207, 63))
        _arm(F, (219, 50), (222, 60), (211, 62), glove=True)
        _head(F, 210, 36)
    elif kind == "C":  # 팔을 뒤로 젖히며 내딛음
        _leg(F, hipL, (202.5, 80), (199.5, 96), False)
        _leg(F, hipR, (222, 79), (226, 96.5))
        _torso(F, 210, lean=-1)
        _arm(F, (200, 50), (190, 51), (187, 40))
        _arm(F, (220, 50), (227, 54), (230, 61), glove=True)
        _head(F, 209.5, 36, face=-0.8)
    elif kind == "B":  # 공을 놓는 순간
        _leg(F, hipL, (201, 81), (196, 96), False)
        _leg(F, hipR, (220, 80), (222.5, 97))
        _torso(F, 210, lean=1)
        _arm(F, (219.5, 50), (225, 57), (219, 65), glove=True)
        _head(F, 210.5, 37, face=0.6)
        _arm(F, (201, 49), (197, 40), (202, 31.5))
    else:              # D: 팔로 스루
        _leg(F, hipL, (201.5, 80), (198.5, 95), False)
        _leg(F, hipR, (219, 80), (222, 97))
        _torso(F, 211, top=49, waist=65, lean=2)
        _arm(F, (221, 52), (227, 60), (222, 67), glove=True)
        _arm(F, (202, 51), (207, 61), (217, 70))
        _head(F, 212, 39, face=1)
    return F.svg()


def _img(name, x, y, w, h):
    import base64
    data = base64.b64encode((Path(__file__).parent / "assets" / name).read_bytes()).decode()
    return f'<image x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" href="data:image/png;base64,{data}"/>'


def batter():
    h = 120
    w = h * 581 / 665
    left = 70
    return (f'<ellipse cx="{left + w * 0.5:.0f}" cy="222" rx="42" ry="4" fill="#000" opacity="0.09"/>'
            + _img("batter_stance.png", left, 222 - h + 3, w, h))


def pitcher_img():
    h = 76
    w = h * 357 / 673
    return _img("pitcher_windup.png", 210 - w / 2, 100 - h + 2, w, h)


def batter_doodle():
    F = Fig()
    _SLEEVE[0] = CAP
    # 우타자: 어깨가 있는 몸통, 허리, 벌린 다리. 배트는 어깨 뒤, 얼굴은 투수 쪽
    _leg(F, (147, 177), (140, 198), (137, 218), False)
    _leg(F, (158, 177), (166, 198), (165, 218))
    F.add([("path", "M141,172 L163,172 Q166,183 164,189 L140,189 Q138,183 141,172 Z")], JERSEY)
    _arm(F, (146, 152), (148, 164), (139, 148), mitt=True)   # 먼 팔
    F.add([("path", "M137,152 Q138,142 152,142 Q166,142 167,152 L163,177 L141,177 Z")], JERSEY)
    F.add([("path", "M141.5,174 L162.5,174 L162,178 L141,178 Z")], CAP, outline=False)
    F.limb((139, 148), (124, 100), 3.4, 6.2, WOOD)
    F.add([("ellipse", (124, 100, 3.4, 3.3))], WOOD)
    _arm(F, (141, 152), (138, 165), (140, 148), mitt=True)
    F.add([("circle", (139.5, 148, 5))], JERSEY)
    # 머리
    F.add([("ellipse", (153, 128, 12.5, 11.5))], SKIN)
    F.add([("ellipse", (158.8, 134, 2.7, 1.8))], BLUSH, outline=False)
    F.add([("circle", (161, 129, 1.5))], OUTL, outline=False)
    F.add([("path", "M157.6,135 Q160,137.5 162.6,135")], OUTL, outline=False)
    F.add([("path", "M140,128 Q139.5,113.5 153,113.5 Q166.5,113.5 166.5,125 L171,127 L166.5,129 L141,130 Z")], CAP)
    F.add([("ellipse", (142.5, 132, 3.8, 5.6))], TOPC)
    shadow = '<ellipse cx="151" cy="222" rx="24" ry="3.6" fill="#000" opacity="0.09"/>'
    return shadow + '<g transform="translate(151,222) scale(1.25) translate(-151,-222)">' + F.svg() + "</g>"


def figures(total, r, a):
    rd = min(r + 0.14 / total, a)
    kt = f"0;{r * 0.35:.3f};{r:.3f};{rd:.3f};{a:.3f};1"

    def grp(kind, vals):
        return (f'<g opacity="{vals.split(";")[0]}">{pitcher_pose(kind)}'
                f'<animate attributeName="opacity" values="{vals}" keyTimes="{kt}" dur="{total}s" calcMode="discrete" repeatCount="indefinite"/></g>')
    out = [f'<ellipse cx="210" cy="99" rx="24" ry="3.4" fill="#000" opacity="0.09"/>']
    out.append(pitcher_img())
    out.append(batter())
    out.append(f'<text x="78" y="236" text-anchor="middle" font-family="{FONT}" font-size="10.5" fill="{MUTED}">우타자</text>')
    out.append(f'<text x="210" y="252" text-anchor="middle" font-family="{FONT}" font-size="10.5" fill="{MUTED}">홈</text>')
    out.append(f'<text x="256" y="52" text-anchor="start" font-family="{FONT}" font-size="11" fill="{MUTED}">투수(오른손)</text>')
    return "".join(out)


def scene_svg(pid, title, dx, drop, note, kind):
    m = MOVE[pid]
    total = round(RELEASE + m + 0.9, 2)
    r = RELEASE / total
    a = (RELEASE + m) / total
    kt4 = f"0;{r:.3f};{a:.3f};1"
    path = scene_path(dx, drop, kind)
    ref = f"M202,32 L210,176"
    s = []
    W2 = 680
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W2} {H}" width="{W2}" height="{H}" role="img" aria-label="{title} 던지는 장면과 옆에서 본 모습">')
    s.append(f'<rect width="{W2}" height="{H}" rx="12" fill="#ffffff" stroke="{LINE}"/>')
    s.append(f'<text x="18" y="30" font-family="{FONT}" font-size="18" font-weight="700" fill="{INK}">{title}</text>')
    s.append(f'<text x="18" y="50" font-family="{FONT}" font-size="12.5" fill="{MUTED}">{note}</text>')
    s.append('<g transform="translate(25,48) scale(0.88)">')
    # 회색 구장: 바닥, 마운드, 타석 선, 홈플레이트
    s.append('<defs><clipPath id="fc"><rect x="-14" y="10" width="484" height="250" rx="12"/></clipPath></defs>')
    s.append('<g clip-path="url(#fc)">')
    s.append(f'<rect x="-14" y="10" width="484" height="250" fill="{GROUND}"/>')
    s.append('<ellipse cx="210" cy="238" rx="214" ry="96" fill="#e3e7eb"/>')
    s.append(f'<path d="M183,224 L-14,112 M237,224 L434,112" stroke="{LINE}" stroke-width="2.2" fill="none"/>')
    s.append('<ellipse cx="210" cy="95" rx="50" ry="9" fill="#d3d9df"/>')
    s.append(f'<g fill="none" stroke="{MUTED}" stroke-width="1.6" stroke-linejoin="round">'
             '<path d="M118,198 L174,198 L178,248 L106,248 Z"/><path d="M302,198 L246,198 L242,248 L314,248 Z"/></g>')
    s.append(f'<path d="M183,222 L237,222 L237,228 L210,238 L183,228 Z" fill="#ffffff" stroke="{MUTED}" stroke-width="1.5"/>')
    s.append(f'<rect x="{ZX}" y="{ZY}" width="{ZW}" height="{ZH}" fill="none" stroke="{MUTED}" stroke-width="1.6" stroke-dasharray="4 3"/>')
    # 투수(세 동작: 준비 -> 젖힘 -> 놓음)와 우타자
    s.append(figures(total, r, a))
    # 직구 점선(기준)과 공
    if kind != "straight":
        s.append(f'<path d="{ref}" stroke="{MUTED}" stroke-width="1.4" stroke-dasharray="4 4" fill="none" opacity="0.8"/>')
    s.append(f'<path id="{pid}-sc" d="{path}" fill="none" stroke="none"/>')
    for col, wd in ((ACCENT, 2.6),):
        s.append(f'<path d="{path}" pathLength="1" stroke="{col}" stroke-width="{wd}" fill="none" stroke-linecap="round" stroke-dasharray="1" stroke-dashoffset="1">'
                 f'<animate attributeName="stroke-dashoffset" values="1;1;0;0" keyTimes="{kt4}" dur="{total}s" repeatCount="indefinite"/></path>')
    s.append(f'<g><circle r="2.5" fill="#ffffff" stroke="{ACCENT}" stroke-width="1.6" opacity="0">'
             f'<animate attributeName="r" values="2.5;2.5;8;8" keyTimes="{kt4}" dur="{total}s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0;1;1;1" keyTimes="{kt4}" dur="{total}s" calcMode="discrete" repeatCount="indefinite"/></circle>'
             f'<animateMotion dur="{total}s" repeatCount="indefinite" keyPoints="0;0;1;1" keyTimes="{kt4}" calcMode="linear"><mpath href="#{pid}-sc"/></animateMotion></g>')
    s.append('</g></g>')
    # 옆에서 본 모습(낙차). 장면과 같은 타이밍으로 움직임
    sp = side_path(drop, kind)
    s.append('<g transform="translate(230,52)">')
    s.append(f'<text x="242" y="14" font-family="{FONT}" font-size="11" fill="{MUTED}">옆에서 본 모습</text>')
    s.append(f'<rect x="228" y="22" width="178" height="188" rx="8" fill="{GROUND}"/>')
    s.append(f'<line x1="228" y1="190" x2="406" y2="190" stroke="{MUTED}" stroke-width="1.2"/>')
    s.append(f'<circle cx="250" cy="80" r="6" fill="{MUTED}"/>')
    s.append(f'<text x="250" y="104" text-anchor="middle" font-family="{FONT}" font-size="10.5" fill="{MUTED}">투수</text>')
    s.append(f'<rect x="394" y="98" width="8" height="64" fill="none" stroke="{MUTED}" stroke-width="1.5"/>')
    s.append(f'<text x="398" y="92" text-anchor="middle" font-family="{FONT}" font-size="10.5" fill="{MUTED}">존</text>')
    if kind != "straight":
        s.append(f'<path d="M250,80 L400,130" stroke="{MUTED}" stroke-width="1.4" stroke-dasharray="4 4" fill="none"/>')
    s.append(f'<path id="{pid}-sd" d="{sp}" fill="none" stroke="none"/>')
    s.append(f'<path d="{sp}" pathLength="1" stroke="{ACCENT}" stroke-width="3" fill="none" stroke-linecap="round" stroke-dasharray="1" stroke-dashoffset="1">'
             f'<animate attributeName="stroke-dashoffset" values="1;1;0;0" keyTimes="{kt4}" dur="{total}s" repeatCount="indefinite"/></path>')
    s.append(f'<g><circle r="6" fill="#ffffff" stroke="{ACCENT}" stroke-width="1.6" opacity="0">'
             f'<animate attributeName="opacity" values="0;1;1;1" keyTimes="{kt4}" dur="{total}s" calcMode="discrete" repeatCount="indefinite"/></circle>'
             f'<animateMotion dur="{total}s" repeatCount="indefinite" keyPoints="0;0;1;1" keyTimes="{kt4}" calcMode="linear"><mpath href="#{pid}-sd"/></animateMotion></g>')
    s.append('</g>')
    s.append(f'<text x="18" y="{H - 10}" font-family="{FONT}" font-size="10.5" fill="{MUTED}">왼쪽은 포수 쪽, 오른쪽은 옆에서 본 모습이에요. 점선은 직구가 가는 길이고 실제 크기와 달라요.</text>')
    s.append("</svg>")
    return "\n".join(s)


def main():
    out = Path(__file__).parent
    cards = []
    for pid, title, dx, drop, note, kind in PITCHES:
        (out / f"term.{pid}.svg").write_text(add_defs(svg(pid, title, dx, drop, note, kind)), encoding="utf-8")
        (out / f"term.{pid}.detail.anim.svg").write_text(add_defs(svg(pid, title, dx, drop, note, kind, animate=True)), encoding="utf-8")
        (out / f"term.{pid}.anim.svg").write_text(add_defs(scene_svg(pid, title, dx, drop, note, kind)), encoding="utf-8")
        cards.append(f'<figure><img src="term.{pid}.anim.svg" alt="{title}"><figcaption>term.{pid}</figcaption></figure>')
    html = ('<!doctype html><meta charset="utf-8"><title>구종 도식 미리보기</title>'
            '<style>body{font-family:sans-serif;background:#f8f9fa;margin:16px}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px}'
            'figure{margin:0}img{width:100%;height:auto}figcaption{font-size:12px;color:#7b8794}</style><main>' + "".join(cards) + "</main>")
    (out / "preview.html").write_text(html, encoding="utf-8")
    print(len(PITCHES), "개 생성")


if __name__ == "__main__":
    main()
