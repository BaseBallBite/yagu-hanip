#!/usr/bin/env python3
"""규칙 카드용 그림(체크스윙) 생성. 사용: python3 make_rule_diagrams.py <출력 폴더>"""
import sys
from pathlib import Path

FONT = "'Noto Sans KR','Apple SD Gothic Neo','Malgun Gothic','WenQuanYi Zen Hei',sans-serif"
INK, MUTED, LINE, ACCENT, GROUND = "#1f2933", "#7b8794", "#cbd2d9", "#4B1E8A", "#f1f3f5"
SKIN, OUTL, WOOD, TOPC, SOFT = "#ffe0c6", "#25232e", "#e9b777", "#7a4bc2", "#ece4f7"
W, H = 680, 640
T = 3.4


def t(x, y, s, size=12, fill=INK, anchor="middle", weight=400):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}">{s}</text>')


def limb(pts, w, fill):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    return (f'<path d="{d}" fill="none" stroke="{OUTL}" stroke-width="{w + 4}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{fill}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')


def camera(x, y, facing):
    d = 1 if facing == "r" else -1
    return (f'<g transform="translate({x},{y})">'
            f'<rect x="-14" y="-9" width="22" height="18" rx="4" fill="#ffffff" stroke="{OUTL}" stroke-width="2"/>'
            f'<circle cx="-8" cy="-12" r="4.5" fill="{ACCENT}" stroke="{OUTL}" stroke-width="1.6"/>'
            f'<circle cx="2" cy="-12" r="4.5" fill="{ACCENT}" stroke="{OUTL}" stroke-width="1.6"/>'
            f'<path d="M8,-4 L17,-8 L17,8 L8,4 Z" fill="#ffffff" stroke="{OUTL}" stroke-width="2" stroke-linejoin="round"/></g>'
            if d == 1 else
            f'<g transform="translate({x},{y}) scale(-1,1)">'
            f'<rect x="-14" y="-9" width="22" height="18" rx="4" fill="#ffffff" stroke="{OUTL}" stroke-width="2"/>'
            f'<circle cx="-8" cy="-12" r="4.5" fill="{ACCENT}" stroke="{OUTL}" stroke-width="1.6"/>'
            f'<circle cx="2" cy="-12" r="4.5" fill="{ACCENT}" stroke="{OUTL}" stroke-width="1.6"/>'
            f'<path d="M8,-4 L17,-8 L17,8 L8,4 Z" fill="#ffffff" stroke="{OUTL}" stroke-width="2" stroke-linejoin="round"/></g>')


def top_panel(anim):
    o = [f'<rect x="18" y="64" width="644" height="206" rx="12" fill="{GROUND}"/>']
    for bx in (206, 384):
        o.append(f'<rect x="{bx}" y="76" width="90" height="180" fill="#ffffff" stroke="{MUTED}" stroke-width="3"/>')
    o.append(f'<line x1="206" y1="76" x2="186" y2="64" stroke="{MUTED}" stroke-width="3"/>')
    o.append(f'<line x1="474" y1="76" x2="494" y2="64" stroke="{MUTED}" stroke-width="3"/>')
    o.append(f'<line x1="70" y1="162" x2="610" y2="162" stroke="{MUTED}" stroke-width="1.8" stroke-dasharray="5 4"/>')
    o.append(f'<line x1="232" y1="130" x2="450" y2="130" stroke="{ACCENT}" stroke-width="2" stroke-dasharray="6 4"/>')
    o.append(f'<polygon points="312,162 368,162 368,184 340,206 312,184" fill="#ffffff" stroke="{MUTED}" stroke-width="2"/>')
    o.append(f'<line x1="312" y1="162" x2="368" y2="162" stroke="{ACCENT}" stroke-width="3.5"/>')
    # 배트
    bat = (f'<line x1="288" y1="142" x2="358" y2="124" stroke="{OUTL}" stroke-width="8.4" stroke-linecap="round"/>'
           f'<line x1="288" y1="142" x2="358" y2="124" stroke="{WOOD}" stroke-width="5.2" stroke-linecap="round"/>')
    if anim:
        o.append(f'<g>{bat}<animateTransform attributeName="transform" type="rotate" values="35 288 142;35 288 142;0 288 142;0 288 142" '
                 f'keyTimes="0;0.15;0.55;1" dur="{T}s" repeatCount="indefinite"/></g>')
    else:
        o.append(bat)
    # 설명 상자
    o.append(f'<rect x="244" y="72" width="192" height="38" rx="8" fill="{ACCENT}" stroke="#ffffff" stroke-width="2"/>')
    o.append(t(340, 88, "홈플레이트 앞면과", 12, "#ffffff", weight=700))
    o.append(t(340, 103, "평행한 기준선", 12, "#ffffff", weight=700))
    o.append(f'<path d="M300,110 L300,126" stroke="{ACCENT}" stroke-width="2" fill="none"/><path d="M295,121 L300,128 L305,121 Z" fill="{ACCENT}"/>')
    o.append(f'<rect x="372" y="206" width="104" height="26" rx="8" fill="{SOFT}" stroke="{ACCENT}" stroke-width="1.5"/>')
    o.append(t(424, 223, "홈플레이트 앞면", 11.5, INK, weight=700))
    o.append(f'<path d="M384,206 L370,176" stroke="{ACCENT}" stroke-width="2" fill="none"/><path d="M366,182 L369,172 L377,179 Z" fill="{ACCENT}"/>')
    # 카메라
    o.append(camera(52, 162, "r"))
    o.append(camera(628, 162, "l"))
    for cx, side in ((52, "3루 쪽"), (628, "1루 쪽")):
        o.append(t(cx + (22 if cx < 300 else -22), 192, "카메라 위치:", 10.5, MUTED))
        o.append(t(cx + (22 if cx < 300 else -22), 206, f"{side} 뒤에서", 10.5, MUTED))
        o.append(t(cx + (22 if cx < 300 else -22), 220, "본 높이", 10.5, MUTED))
    return "".join(o)


def batter(swing, anim):
    ex, ey = (250, 162) if swing else (206, 176)
    hx, hy = 188, 106
    o = []
    o.append(f'<ellipse cx="122" cy="204" rx="82" ry="7" fill="#000000" opacity="0.08"/>')
    o.append(limb([(110, 128), (84, 162), (62, 192)], 15, "#ffffff"))      # 뒷다리
    o.append(limb([(124, 128), (152, 156), (172, 190)], 15, "#ffffff"))    # 앞다리
    o.append(f'<path d="M48,196 Q56,186 70,190 L76,198 Q60,204 48,198 Z" fill="{ACCENT}" stroke="{OUTL}" stroke-width="2.5" stroke-linejoin="round"/>')
    o.append(f'<path d="M164,196 Q172,184 188,190 L192,198 Q176,206 164,200 Z" fill="{ACCENT}" stroke="{OUTL}" stroke-width="2.5" stroke-linejoin="round"/>')
    o.append(f'<path d="M92,78 Q116,66 142,76 L136,134 Q116,140 98,134 Z" fill="#ffffff" stroke="{OUTL}" stroke-width="3" stroke-linejoin="round"/>')
    o.append(f'<rect x="97" y="124" width="40" height="8" rx="2" fill="{ACCENT}" stroke="{OUTL}" stroke-width="2"/>')
    o.append(f'<path d="M100,92 L130,90" stroke="{TOPC}" stroke-width="4" fill="none" stroke-linecap="round"/>')
    o.append(f'<circle cx="118" cy="54" r="15" fill="{SKIN}" stroke="{OUTL}" stroke-width="3"/>')
    o.append(f'<path d="M102,52 Q104,34 120,34 Q134,34 136,50 L152,52 L136,56 Q124,46 102,56 Z" fill="{ACCENT}" stroke="{OUTL}" stroke-width="3" stroke-linejoin="round"/>')
    o.append(f'<path d="M104,52 Q99,58 106,66" fill="none" stroke="{OUTL}" stroke-width="3" stroke-linecap="round"/>')
    o.append(limb([(100, 84), (126, 104), (hx, hy)], 8, "#ffffff"))        # 뒷팔
    o.append(limb([(134, 82), (158, 98), (hx, hy)], 8, SKIN))             # 앞팔
    bat = limb([(hx, hy), (ex, ey)], 8, WOOD)
    if anim:
        o.append(f'<g>{bat}<animateTransform attributeName="transform" type="rotate" values="-55 {hx} {hy};-55 {hx} {hy};0 {hx} {hy};0 {hx} {hy}" '
                 f'keyTimes="0;0.15;0.55;1" dur="{T}s" repeatCount="indefinite"/></g>')
    else:
        o.append(bat)
    o.append(f'<circle cx="{hx}" cy="{hy}" r="5.5" fill="{ACCENT}" stroke="{OUTL}" stroke-width="2.5"/>')
    return "".join(o), ex, ey


def b64(name):
    import base64
    return base64.b64encode((Path(__file__).parent / "assets" / name).read_bytes()).decode()


def card(x, title, sub, icon, swing, anim):
    o = [f'<g transform="translate({x},288)">',
         f'<rect width="316" height="312" rx="12" fill="#ffffff" stroke="{LINE}" stroke-width="1.5"/>',
         f'<path d="M0,12 Q0,0 12,0 L304,0 Q316,0 316,12 L316,62 L0,62 Z" fill="{ACCENT}"/>',
         f'<circle cx="46" cy="31" r="17" fill="#ffffff"/>',
         t(46, 38, icon, 20, ACCENT, weight=700),
         t(186, 28, title, 17, "#ffffff", weight=700),
         t(186, 48, sub, 12, "#e6dcf5"),
         '<g transform="translate(0,66)">']
    sc = 0.46
    if swing:
        lx, line = 80, 120
        o.append(f'<ellipse cx="{lx + 86}" cy="206" rx="86" ry="6" fill="#000000" opacity="0.08"/>')
        pink = f'<rect x="{line - 69}" y="34" width="69" height="152" fill="#ff9fa8" opacity="0.5">'
        if anim:
            pink += f'<animate attributeName="opacity" values="0.15;0.15;0.55;0.55" keyTimes="0;0.15;0.55;1" dur="{T}s" repeatCount="indefinite"/>'
        o.append(pink + '</rect>')
        o.append(f'<image x="{lx}" y="16" width="{374 * sc:.1f}" height="{409 * sc:.1f}" href="data:image/png;base64,{b64("batter_swing.png")}"/>')
        o.append(f'<polygon points="{line},218 {line},236 {line + 50},236 {line + 72},227 {line + 50},218" fill="#ffffff" stroke="{MUTED}" stroke-width="2"/>')
    else:
        lx, line = 70, 210
        o.append(f'<ellipse cx="{lx + 70}" cy="206" rx="80" ry="6" fill="#000000" opacity="0.08"/>')
        o.append(f'<image x="{lx}" y="14" width="{302 * sc:.1f}" height="{414 * sc:.1f}" href="data:image/png;base64,{b64("batter_noswing.png")}"/>')
        o.append(f'<polygon points="{line},218 {line},236 {line - 50},236 {line - 72},227 {line - 50},218" fill="#ffffff" stroke="{MUTED}" stroke-width="2"/>')
    o.append(f'<line x1="{line}" y1="214" x2="{line}" y2="238" stroke="{ACCENT}" stroke-width="3.5"/>')
    o.append(f'<line x1="{line}" y1="8" x2="{line}" y2="210" stroke="{ACCENT}" stroke-width="2.4" stroke-dasharray="7 5"/>')
    o.append('</g></g>')
    return "".join(o)


def svg(anim=False):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="체크스윙 판정 도식">',
         f'<rect width="{W}" height="{H}" rx="12" fill="#ffffff" stroke="{LINE}"/>',
         t(18, 32, "체크스윙", 18, INK, "start", 700),
         t(18, 52, "배트 끝이 기준선을 넘어 투수 쪽으로 가면 스윙이에요", 12.5, MUTED, "start"),
         top_panel(anim),
         card(18, "스윙 아님", "우타자 · 1루 쪽 카메라", "✓", False, anim),
         card(346, "스윙", "좌타자 · 3루 쪽 카메라", "!", True, anim),
         t(18, H - 12, "위는 위에서 내려다본 그림이고 아래는 카메라에서 본 모습이에요. 실제 판독은 배트 끝의 각도(타자 기준 90도)로 봐요.", 10.5, MUTED, "start"),
         "</svg>"]
    return "\n".join(o)


# ---------- 스트라이크 존 ----------
def zone_svg():
    H2 = 400
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H2}" width="{W}" height="{H2}" role="img" aria-label="스트라이크 존 도식">',
         f'<rect width="{W}" height="{H2}" rx="12" fill="#ffffff" stroke="{LINE}"/>',
         t(18, 32, "스트라이크 존", 18, INK, "start", 700),
         t(18, 52, "공이 홈플레이트 위의 이 네모를 지나가면 스트라이크예요", 12.5, MUTED, "start")]
    for x, title, sub in ((18, "앞에서 본 모습", "포수 쪽에서 본 높이"), (346, "위에서 본 모습", "홈플레이트 위 너비")):
        o.append(f'<g transform="translate({x},68)"><rect width="316" height="300" rx="12" fill="#ffffff" stroke="{LINE}" stroke-width="1.5"/>'
                 f'<path d="M0,12 Q0,0 12,0 L304,0 Q316,0 316,12 L316,48 L0,48 Z" fill="{ACCENT}"/>'
                 + t(158, 22, title, 15, "#ffffff", weight=700) + t(158, 39, sub, 11.5, "#e6dcf5") + '</g>')
    # 왼쪽: 높이
    gy, hh = 332, 205          # 지면 y(전체 좌표), 타자 키(px)
    sc = hh / 665
    iw = 581 * sc
    zb, zt = gy - 0.2704 * hh, gy - 0.5575 * hh
    o.append(f'<ellipse cx="110" cy="{gy}" rx="70" ry="5" fill="#000" opacity="0.08"/>')
    o.append(f'<line x1="36" y1="{gy}" x2="300" y2="{gy}" stroke="{MUTED}" stroke-width="1.4"/>')
    o.append(f'<image x="52" y="{gy - hh}" width="{iw:.1f}" height="{hh}" href="data:image/png;base64,{b64("batter_stance.png")}"/>')
    o.append(f'<rect x="64" y="{zt:.1f}" width="150" height="{zb - zt:.1f}" fill="{ACCENT}" opacity="0.2"/>'
             f'<rect x="64" y="{zt:.1f}" width="150" height="{zb - zt:.1f}" fill="none" stroke="{ACCENT}" stroke-width="2.2" stroke-dasharray="6 4"/>')
    for yy, lab in ((zt, "키의 55.75%"), (zb, "키의 27.04%")):
        o.append(f'<line x1="214" y1="{yy:.1f}" x2="236" y2="{yy:.1f}" stroke="{ACCENT}" stroke-width="2"/>')
        o.append(t(242, yy + 4, lab, 12, ACCENT, "start", 700))
    o.append(t(262, gy + 17, "지면", 11.5, MUTED, "start"))
    o.append(t(82, zt + (zb - zt) / 2 + 5, "존", 14, ACCENT, "start", 700))
    # 오른쪽: 위에서 본 너비
    s = 3.2
    pw = 43.18 * s
    zw = 47.18 * s
    cx = 346 + 158
    top = 168
    px0 = cx - pw / 2
    zx0 = cx - zw / 2
    o.append(f'<rect x="{zx0:.1f}" y="{top - 12}" width="{zw:.1f}" height="{pw + 24:.1f}" fill="{ACCENT}" opacity="0.2"/>'
             f'<rect x="{zx0:.1f}" y="{top - 12}" width="{zw:.1f}" height="{pw + 24:.1f}" fill="none" stroke="{ACCENT}" stroke-width="2.2" stroke-dasharray="6 4"/>')
    pts = [(px0, top), (px0 + pw, top), (px0 + pw, top + pw / 2), (cx, top + pw), (px0, top + pw / 2)]
    o.append('<polygon points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in pts) + f'" fill="#ffffff" stroke="{MUTED}" stroke-width="2.2"/>')
    o.append(t(cx, top + pw / 2 + 4, "홈플레이트", 12, MUTED))
    # 치수선
    o.append(f'<path d="M{px0:.1f},{top - 26} L{px0 + pw:.1f},{top - 26}" stroke="{INK}" stroke-width="1.6"/>'
             f'<path d="M{px0:.1f},{top - 31} L{px0:.1f},{top - 21} M{px0 + pw:.1f},{top - 31} L{px0 + pw:.1f},{top - 21}" stroke="{INK}" stroke-width="1.6"/>')
    o.append(t(cx, top - 33, "홈플레이트 43.18cm", 12, INK, weight=700))
    o.append(f'<path d="M{zx0:.1f},{top + pw + 28} L{zx0 + zw:.1f},{top + pw + 28}" stroke="{ACCENT}" stroke-width="1.6"/>'
             f'<path d="M{zx0:.1f},{top + pw + 23} L{zx0:.1f},{top + pw + 33} M{zx0 + zw:.1f},{top + pw + 23} L{zx0 + zw:.1f},{top + pw + 33}" stroke="{ACCENT}" stroke-width="1.6"/>')
    o.append(t(cx, top + pw + 46, "존 47.18cm (양옆 2cm씩 더)", 12, ACCENT, weight=700))
    o.append(t(364, 154, "▲ 투수 쪽", 11, MUTED, "start"))
    o.append(t(18, 392, "KBO 2026 ABS 기준이에요. 홈플레이트의 중간면과 끝면 모두 높이 기준을 충족해야 스트라이크예요.", 10.5, MUTED, "start"))
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out.mkdir(parents=True, exist_ok=True)
    (out / "rule.check_swing.svg").write_text(svg(False), encoding="utf-8")
    (out / "rule.check_swing.anim.svg").write_text(svg(True), encoding="utf-8")
    (out / "rule.strike_zone.svg").write_text(zone_svg(), encoding="utf-8")
    print("3개 생성")


