# -*- coding: utf-8 -*-
"""Figures for the science material (kana labels so that no ruby is needed inside SVG)."""
import os, sys, math
sys.path.insert(0, os.path.dirname(__file__))
from svgfig import Fig
import editions as ED
EDITION, _args = ED.resolve(sys.argv[1:])

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = ED.src_dir(EDITION, 'science', 'figs')
os.makedirs(OUT, exist_ok=True)

FONT = 'font-family="Noto Sans CJK JP, Noto Sans, sans-serif"'


def save(f, name):
    f.save(os.path.join(OUT, name + '.svg'))


def panels(figs, gap=16):
    w = sum(f.w for f in figs) + gap * (len(figs) - 1)
    h = max(f.h for f in figs)
    parts = []
    x = 0
    for f in figs:
        parts.append('<g transform="translate(%d,0)">%s</g>' % (x, ''.join(f.items)))
        x += f.w + gap
    defs = '<defs><marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#000"/></marker></defs>'
    return '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">%s%s</svg>' % (w, h, w, h, defs, ''.join(parts))


def savep(figs, name, gap=16):
    open(os.path.join(OUT, name + '.svg'), 'w', encoding='utf-8').write(panels(figs, gap))


def txt(f, p, s, size=12, anchor='middle', dy=0, dx=0):
    cx, cy = f.P(*p)
    f.items.append('<text x="%.1f" y="%.1f" font-size="%d" text-anchor="%s" %s>%s</text>' % (cx + dx, cy + dy + 4, size, anchor, FONT, s))


# ---------- circuit elements (pixel coords, y up) ----------
def battery(f, x, y, vertical=False, label=None):
    """battery at (x,y): long line (+) left, short (-) right when horizontal"""
    if not vertical:
        f.line((x - 1, y - 9), (x - 1, y + 9), width=1.6)   # long (+)
        f.line((x + 4, y - 4), (x + 4, y + 4), width=3)   # short (-)
        txt(f, (x - 6, y + 14), '＋', 10)
        txt(f, (x + 8, y + 14), '−', 10)
    if label:
        txt(f, (x + 2, y - 18), label, 11)


def resistor(f, x1, x2, y, label=None):
    f.poly([(x1, y - 5), (x2, y - 5), (x2, y + 5), (x1, y + 5)], fill='#fff')
    if label:
        txt(f, ((x1 + x2) / 2, y - 16), label, 11)


def meter(f, x, y, sym, label=None):
    f.circle((x, y), 9, fill='#fff')
    txt(f, (x, y), sym, 11)
    if label:
        txt(f, (x, y - 16), label, 10)


def series_circuit(vlabel='12 V', ra='a', rb='b', amp='A₁', title='図1（ちょくれつ）'):
    f = Fig(230, 150, 0, 230, 0, 150)
    L, R, T, B = 20, 210, 120, 30
    # top wire with two resistors
    f.line((L, T), (60, T)); resistor(f, 60, 95, T, ra)
    f.line((95, T), (130, T)); resistor(f, 130, 165, T, rb)
    f.line((165, T), (R, T))
    f.line((R, T), (R, B)); f.line((L, T), (L, B))
    # bottom: battery and ammeter
    f.line((L, B), (114, B)); battery(f, 115, B); f.line((119, B), (151, B))
    meter(f, 160, B, 'A', amp); f.line((169, B), (R, B))
    txt(f, (115, B - 16), 'でんげん ' + vlabel, 10)
    txt(f, (115, 142), title, 12)
    txt(f, (115, 75), 'a, b：でんねつせん'.replace('a, b', ra + ', ' + rb), 10)
    return f


def parallel_circuit(vlabel='12 V', ra='a', rb='b', amp='A₂', title='図2（へいれつ）'):
    f = Fig(230, 170, 0, 230, 0, 170)
    L, R, T, M, B = 20, 210, 140, 100, 30
    # two branches between x=70 and x=160 at y=T and y=M
    f.line((L, T), (70, T)); resistor(f, 100, 135, T, ra); f.line((70, T), (100, T)); f.line((135, T), (160, T)); f.line((160, T), (R, T))
    f.line((70, T), (70, M)); f.line((160, T), (160, M))
    f.line((70, M), (100, M)); resistor(f, 100, 135, M, rb); f.line((135, M), (160, M))
    f.dot((70, T), 2.5); f.dot((160, T), 2.5)
    f.line((R, T), (R, B)); f.line((L, T), (L, B))
    f.line((L, B), (114, B)); battery(f, 115, B); f.line((119, B), (151, B))
    meter(f, 160, B, 'A', amp); f.line((169, B), (R, B))
    txt(f, (115, B - 16), 'でんげん ' + vlabel, 10)
    txt(f, (115, 162), title, 12)
    txt(f, (115, 62), ra + ', ' + rb + '：でんねつせん', 10)
    return f


savep([series_circuit(), parallel_circuit()], 'circuit_sp', gap=30)
savep([series_circuit('10 V', 'P', 'Q', 'A'), parallel_circuit('6 V', 'P', 'Q', 'A')], 'mock1_circuit', gap=30)


# ---------- low pressure with fronts ----------
def low_pressure():
    f = Fig(330, 230, 0, 330, 0, 230)
    cx, cy = 150, 165
    # isobars (ellipses approximated by circles)
    for r in (22, 44, 66):
        f.circle((cx, cy), r, color='#666', width=0.9)
    txt(f, (cx, cy), '低', 16)
    txt(f, (cx, cy + 22), '（てい）', 9)
    import math as m

    def front(ex, ey, color, kind):
        f.line((cx, cy), (ex, ey), width=2, color=color)
        x0, y0 = f.P(cx, cy)
        x1, y1 = f.P(ex, ey)
        dx, dy = x1 - x0, y1 - y0
        L = m.hypot(dx, dy)
        dx, dy = dx / L, dy / L
        nx, ny = dy, -dx  # perpendicular pointing east-ish / north-east-ish (forward side)
        n = 5
        for i in range(1, n + 1):
            t = i / (n + 1)
            px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if kind == 'cold':
                pts = [(px - 5 * dx, py - 5 * dy), (px + 5 * dx, py + 5 * dy), (px + 9 * nx, py + 9 * ny)]
            else:
                pts = []
                for k in range(0, 9):
                    th = m.pi * k / 8
                    pts.append((px + 5 * (m.cos(th) * dx + m.sin(th) * nx), py + 5 * (m.cos(th) * dy + m.sin(th) * ny)))
            f.items.append('<polygon points="%s" fill="%s" stroke="none"/>' % (' '.join('%.1f,%.1f' % q for q in pts), color))

    front(290, 105, '#c00', 'warm')
    front(40, 60, '#00a', 'cold')
    txt(f, (250, 92), 'ぜんせん Y', 11)
    txt(f, (34, 88), 'ぜんせん X', 11)
    # points
    for (px, py, lab) in ((60, 110, 'A'), (150, 90, 'B'), (270, 150, 'C')):
        f.dot((px, py), 3)
        txt(f, (px + 10, py + 2), lab, 12, anchor='start')
    txt(f, (300, 210), '北', 12)
    f.line((300, 190), (300, 205), width=1, arrow=True)
    txt(f, (165, 15), '（ていきあつは ひがしへ すすむ →）', 10)
    return f


save(low_pressure(), 'low_pressure')


# ---------- blood circulation ----------
def blood():
    f = Fig(440, 340, 0, 440, 0, 340)

    def box(x1, y1, x2, y2, label, size=11):
        f.poly([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], fill='#fff')
        txt(f, ((x1 + x2) / 2, (y1 + y2) / 2), label, size)

    def path(pts, arrow_end=True):
        for a, b in zip(pts, pts[1:]):
            f.line(a, b, width=1.4, arrow=(arrow_end and b is pts[-1]))

    def lab(p, s, anchor='middle', dx=0, dy=0):
        txt(f, p, s, 12, anchor=anchor, dx=dx, dy=dy)

    # organs
    box(150, 290, 250, 325, 'はい')
    box(140, 190, 200, 230, 'うしんぼう', 10)
    box(140, 150, 200, 190, 'うしんしつ', 10)
    box(200, 190, 260, 230, 'さしんぼう', 10)
    box(200, 150, 260, 190, 'さしんしつ', 10)
    txt(f, (200, 240), 'しんぞう', 10)
    box(50, 45, 120, 75, 'ぜんしん', 10)
    box(150, 45, 230, 75, 'しょうちょう', 10)
    box(150, 100, 230, 130, 'かんぞう', 10)
    box(330, 45, 400, 75, 'じんぞう', 10)
    # (1) pulmonary artery: right ventricle -> lungs (left side)
    path([(140, 170), (110, 170), (110, 305), (150, 305)])
    lab((110, 215), '①', 'end', dx=-4)
    # (2) pulmonary vein: lungs -> left atrium (right side)
    path([(250, 305), (290, 305), (290, 210), (260, 210)])
    lab((290, 260), '②', 'start', dx=4)
    # (7) aorta: left ventricle -> right trunk -> bottom -> organs
    path([(260, 170), (415, 170), (415, 20), (85, 20), (85, 45)])
    path([(190, 20), (190, 45)])
    path([(415, 60), (400, 60)])
    lab((415, 120), '⑦', 'start', dx=4)
    lab((408, 60), '⑤', 'middle', dy=-14)
    # (3) portal vein: small intestine -> liver
    path([(190, 75), (190, 100)])
    lab((190, 87), '③', 'start', dx=6)
    # (8) vena cava: body -> left trunk -> right atrium (from above)
    path([(85, 75), (85, 90), (25, 90), (25, 250), (104, 250)], arrow_end=False)
    # hop over (1)
    sx, sy = f.P(104, 250)
    f.items.append('<path d="M %.1f %.1f a 6 6 0 0 1 12 0" fill="none" stroke="#000" stroke-width="1.4"/>' % (sx, sy))
    path([(116, 250), (170, 250), (170, 230)])
    lab((25, 180), '⑧', 'end', dx=-4)
    # (4) liver -> vena cava
    path([(150, 115), (25, 115)], arrow_end=False)
    f.line((60, 115), (40, 115), width=1.4, arrow=True)
    lab((90, 115), '④', 'middle', dy=-12)
    # (6) kidney -> vena cava (runs under the heart)
    path([(365, 75), (365, 140), (25, 140)], arrow_end=False)
    f.line((60, 140), (40, 140), width=1.4, arrow=True)
    lab((300, 140), '⑥', 'middle', dy=-12)
    return f


save(blood(), 'blood')
# Keep the expanded h5 diagrams and repaired circuit layout in sync.
if (EDITION.get('id') if isinstance(EDITION, dict) else EDITION) == 'h5':
    import subprocess
    subprocess.run([sys.executable, os.path.join(ROOT, 'build', 'generate_science_visuals.py'), ROOT], check=True)
print('ok')
