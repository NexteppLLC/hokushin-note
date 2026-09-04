# -*- coding: utf-8 -*-
import os, sys, math
sys.path.insert(0, os.path.dirname(__file__))
from svgfig import Fig
import editions as ED
EDITION, _args = ED.resolve(sys.argv[1:])

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = ED.src_dir(EDITION, 'math', 'figs')
os.makedirs(OUT, exist_ok=True)


def save(f, name):
    f.save(os.path.join(OUT, name + '.svg'))


def panels(figs, gap=16):
    """combine several Fig objects horizontally into one svg"""
    w = sum(f.w for f in figs) + gap * (len(figs) - 1)
    h = max(f.h for f in figs)
    parts = []
    x = 0
    for f in figs:
        inner = ''.join(f.items)
        parts.append('<g transform="translate(%d,0)">%s</g>' % (x, inner))
        x += f.w + gap
    defs = '<defs><marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#000"/></marker></defs>'
    return '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">%s%s</svg>' % (w, h, w, h, defs, ''.join(parts))


def savep(figs, name, gap=16):
    open(os.path.join(OUT, name + '.svg'), 'w', encoding='utf-8').write(panels(figs, gap))


# ---------- q8_road ----------
f = Fig(260, 200, -1, 15, -1, 11)
f.poly([(0, 0), (14, 0), (14, 10), (0, 10)])
# roads: vertical at x=5..6.2, horizontal y=4..5.2
f.poly([(5, 0), (6.2, 0), (6.2, 10), (5, 10)], fill='#ddd')
f.poly([(0, 4), (14, 4), (14, 5.2), (0, 5.2)], fill='#ddd')
f.text((7, -0.6), '14 m', dy=6)
f.text((-0.6, 5), '10 m', anchor='end')
f.text((5.6, 10.3), 'x m', dy=-4, italic=True)
f.text((14.4, 4.6), 'x m', anchor='start', italic=True)
save(f, 'q8_road')

# ---------- q9_move ----------
f = Fig(220, 220, -1, 9.5, -1, 9.5)
A, B, C, D = (0, 8), (0, 0), (8, 0), (8, 8)
f.poly([A, B, C, D])
for p, n, pos in [(A, 'A', 'ul'), (B, 'B', 'dl'), (C, 'C', 'dr'), (D, 'D', 'ur')]:
    f.label(p, n, pos)
P, Q = (0, 5), (3, 0)
f.dot(P); f.label(P, 'P', 'l')
f.dot(Q); f.label(Q, 'Q', 'd')
f.poly([P, B, Q], fill='#eee')
f.text((4, 8.4), '8 cm', dy=-4)
save(f, 'q9_move')

# ---------- d2_1_basic (4 panels) ----------
p1 = Fig(200, 170, -1, 9, -1, 7.5)
A, B = (1, 3), (7, 3)
p1.line(A, B); p1.dot(A); p1.dot(B); p1.label(A, 'A', 'dl'); p1.label(B, 'B', 'dr')
p1.arc(A, 4, -60, 60, dash=True); p1.arc(B, 4, 120, 240, dash=True)
p1.line((4, 0.2), (4, 6.5), width=1.5)
p1.text((4, 7), '① 垂直二等分線', size=11)
p2 = Fig(200, 170, -1, 9, -1, 7.5)
O = (1, 1)
p2.line(O, (8, 1)); p2.line(O, (5.5, 6.5))
p2.arc(O, 3, 0, 62, dash=True)
c = (4, 1); d = (1 + 3 * math.cos(math.radians(60)), 1 + 3 * math.sin(math.radians(60)))
p2.arc(c, 2.2, 20, 100, dash=True); p2.arc(d, 2.2, -30, 45, dash=True)
p2.line(O, (7.2, 4.6), width=1.5)
p2.label(O, 'O', 'dl'); p2.text((4, 7), '② 角の二等分線', size=11)
p3 = Fig(200, 170, -1, 9, -1, 7.5)
p3.line((0, 1), (8, 1)); P = (4, 5); p3.dot(P); p3.label(P, 'P', 'ur')
p3.arc(P, 4.2, 210, 330, dash=True)
p3.arc((1.4, 1), 3.2, 240, 300, dash=True); p3.arc((6.6, 1), 3.2, 240, 300, dash=True)
p3.line(P, (4, -0.8), width=1.5); p3.text((8.4, 1), 'ℓ', anchor='start'); p3.text((4, 7), '④ 点Pから垂線', size=11)
p4 = Fig(200, 170, -1, 9, -1, 7.5)
p4.circle((4, 3), 3)
a1, a2, a3 = (4 + 3 * math.cos(math.radians(150)), 3 + 3 * math.sin(math.radians(150))), (4 + 3 * math.cos(math.radians(80)), 3 + 3 * math.sin(math.radians(80))), (4 + 3 * math.cos(math.radians(-20)), 3 + 3 * math.sin(math.radians(-20)))
p4.line(a1, a2); p4.line(a2, a3)
for pt in (a1, a2, a3):
    p4.dot(pt)
# perpendicular bisectors
for u, v in [(a1, a2), (a2, a3)]:
    mx, my = (u[0] + v[0]) / 2, (u[1] + v[1]) / 2
    dx, dy = v[0] - u[0], v[1] - u[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L
    p4.line((mx - nx * 3.5, my - ny * 3.5), (mx + nx * 3.5, my + ny * 3.5), dash=True)
p4.dot((4, 3)); p4.label((4, 3), 'O', 'dr'); p4.text((4, 7), '⑤ 円の中心', size=11)
savep([p1, p2, p3, p4], 'd2_1_basic')

# ---------- d2_1_ex (5 panels) ----------
e1 = Fig(150, 150, -1, 8, -1, 7)
e1.line((1, 3), (7, 3)); e1.dot((1, 3)); e1.dot((7, 3)); e1.label((1, 3), 'A', 'dl'); e1.label((7, 3), 'B', 'dr'); e1.text((3.5, 6.2), '1', size=12)
e2 = Fig(150, 150, -1, 8, -1, 7)
e2.line((1, 1), (7, 1)); e2.line((1, 1), (5, 6)); e2.label((1, 1), 'O', 'dl'); e2.label((7, 1), 'X', 'dr'); e2.label((5, 6), 'Y', 'ur'); e2.text((3.5, 6.2), '2', size=12, dx=-40)
e3 = Fig(150, 150, -1, 8, -1, 7)
e3.line((0, 1.5), (7, 1.5)); e3.dot((3.5, 5)); e3.label((3.5, 5), 'P', 'ur'); e3.text((7, 1.5), 'ℓ', dx=8, anchor='start'); e3.text((3.5, 6.2), '3', size=12)
e4 = Fig(150, 150, -1, 8, -1, 7)
e4.line((0, 1.5), (7, 1.5)); e4.dot((3.5, 1.5)); e4.label((3.5, 1.5), 'A', 'd'); e4.text((7, 1.5), 'ℓ', dx=8, anchor='start'); e4.text((3.5, 6.2), '4', size=12)
e5 = Fig(150, 150, -1, 8, -1, 7)
e5.line((0, 1), (7, 1)); e5.dot((2, 5)); e5.dot((5.5, 3.5)); e5.label((2, 5), 'A', 'ul'); e5.label((5.5, 3.5), 'B', 'ur'); e5.text((7, 1), 'ℓ', dx=8, anchor='start'); e5.text((3.5, 6.2), '5', size=12)
savep([e1, e2, e3, e4, e5], 'd2_1_ex', gap=10)

# ---------- d2_2_ex ----------
def tri(fig, A, B, C, labels=('A', 'B', 'C')):
    fig.poly([A, B, C])
    fig.label(A, labels[0], 'u'); fig.label(B, labels[1], 'dl'); fig.label(C, labels[2], 'dr')
x1 = Fig(150, 150, -1, 8, -1, 7); tri(x1, (2.5, 6), (0.5, 1), (7, 1)); x1.text((3.5, 6.6), '1', size=12, dx=30)
x2 = Fig(150, 150, -1, 8, -1, 7); tri(x2, (2, 6), (0.5, 1), (7, 1.5)); x2.text((3.5, 6.6), '2', size=12, dx=30)
x3 = Fig(150, 150, -1, 8, -1, 7); x3.line((0, 1.5), (7, 1.5)); x3.dot((3.5, 1.5)); x3.label((3.5, 1.5), 'A', 'd'); x3.text((7, 1.5), 'ℓ', dx=8, anchor='start'); x3.text((3.5, 6.2), '3', size=12)
x4 = Fig(150, 150, -1, 8, -1, 7); x4.circle((3.5, 3), 2.5); x4.dot((3.5, 3)); x4.label((3.5, 3), 'O', 'dr'); ap = (3.5 + 2.5 * math.cos(math.radians(40)), 3 + 2.5 * math.sin(math.radians(40))); x4.dot(ap); x4.label(ap, 'A', 'ur'); x4.text((3.5, 6.2), '4', size=12, dx=-40)
x5 = Fig(150, 150, -1, 8, -1, 7); x5.line((1, 2), (6, 2)); x5.dot((1, 2)); x5.dot((6, 2)); x5.label((1, 2), 'A', 'dl'); x5.label((6, 2), 'B', 'dr'); x5.text((3.5, 6.2), '5', size=12)
savep([x1, x2, x3, x4, x5], 'd2_2_ex', gap=10)

# ---------- d2_5_box (box plots A, B) ----------
def boxplot(name, data_sets, xmax=45, xlabel='通学時間（分）', w=420):
    f = Fig(w, 150, -6, xmax + 3, -1.2, 3.2)
    for i, (lab, (mn, q1, md, q3, mx)) in enumerate(data_sets):
        y = 2.2 - i * 1.3
        f.line((mn, y), (q1, y)); f.line((q3, y), (mx, y))
        f.poly([(q1, y - 0.35), (q3, y - 0.35), (q3, y + 0.35), (q1, y + 0.35)], fill='#eee')
        f.line((md, y - 0.35), (md, y + 0.35), width=1.6)
        f.line((mn, y - 0.2), (mn, y + 0.2)); f.line((mx, y - 0.2), (mx, y + 0.2))
        f.text((-3, y), lab, anchor='middle')
    f.line((0, 0), (xmax, 0), width=1)
    for x in range(0, xmax + 1, 5):
        f.line((x, -0.1), (x, 0.1), width=0.8); f.text((x, -0.35), str(x), size=10, dy=6)
    f.text((xmax / 2, -1.0), xlabel, size=10, dy=6)
    save(f, name)

boxplot('d2_5_box', [('A組', (5, 10, 15, 22, 35)), ('B組', (8, 15, 20, 30, 40))])
boxplot('m2_box', [('A組', (5, 12, 20, 28, 38)), ('B組', (8, 15, 22, 25, 35))])

# ---------- d2_6_dots (square perimeter n=1,2,3) ----------
figs = []
for n in (1, 2, 3):
    f = Fig(110, 120, -1, 4.5, -1.5, 4.2)
    side = n + 1
    for i in range(side):
        for j in range(side):
            if i in (0, side - 1) or j in (0, side - 1):
                f.dot((i * 3 / (side - 1), j * 3 / (side - 1)), r=4)
    f.text((1.5, -1.0), '%d番目' % n, size=11, dy=4)
    figs.append(f)
savep(figs, 'd2_6_dots', gap=20)

# ---------- d2_8_angles ----------
g1 = Fig(200, 160, -1, 9, -1, 7)
g1.line((0, 5.5), (8, 5.5)); g1.line((0, 0.5), (8, 0.5)); g1.text((8.3, 5.5), 'ℓ', anchor='start'); g1.text((8.3, 0.5), 'm', anchor='start')
P1, V, P2 = (1.5, 5.5), (4.5, 3), (7.5, 0.5)
g1.line(P1, V); g1.line(V, P2)
g1.angle_mark(P1, (8, 5.5), V, r=0.9, label='55°'); g1.angle_mark(P2, (0, 0.5), V, r=0.9, label='30°'); g1.angle_mark(V, P1, P2, r=0.7, label='x')
g1.text((4, 6.6), '①', size=12)
g2 = Fig(200, 160, -1, 9, -1, 7)
A, B, C = (2.5, 5.5), (0.5, 0.5), (7, 0.5)
g2.poly([A, B, C]); g2.line(B, (-0.8, 0.5)); g2.label(A, 'A', 'u'); g2.label(B, 'B', 'd'); g2.label(C, 'C', 'dr')
g2.angle_mark(A, B, C, r=0.8, label='40°'); g2.angle_mark(B, (-0.8, 0.5), A, r=0.8, label='110°'); g2.text((4, 6.6), '②', size=12)
g3 = Fig(200, 160, -1, 9, -1, 7)
A, B, C = (4, 6), (1.5, 0.5), (6.5, 0.5)
g3.poly([A, B, C]); g3.label(A, 'A', 'u'); g3.label(B, 'B', 'dl'); g3.label(C, 'C', 'dr')
g3.tick(A, B); g3.tick(A, C); g3.angle_mark(A, B, C, r=0.8, label='36°'); g3.text((4, 6.9), '③', size=12, dx=-50)
savep([g1, g2, g3], 'd2_8_angles')

# ---------- d3_1_fig ----------
f = Fig(230, 230, -2, 8, -1.5, 11)
f.axes(); f.func(lambda x: x + 4, -2, 6); f.func(lambda x: -2 * x + 10, -0.5, 5.5)
f.dot((2, 6)); f.label((2, 6), 'A', 'r'); f.dot((0, 4)); f.label((0, 4), 'B', 'l'); f.dot((0, 10)); f.label((0, 10), 'C', 'l')
f.text((6, 10), 'ℓ', anchor='start'); f.text((5.5, -1), 'm', anchor='start')
save(f, 'd3_1_fig')

# ---------- d3_2_fig ----------
f = Fig(230, 170, -1, 8, -1, 5.5)
A, B, C, D = (0, 4), (0, 0), (6, 0), (6, 4)
f.poly([A, B, C, D]); f.label(A, 'A', 'ul'); f.label(B, 'B', 'dl'); f.label(C, 'C', 'dr'); f.label(D, 'D', 'ur')
P = (0, 2.5); f.dot(P); f.label(P, 'P', 'l'); f.poly([A, P, D], fill='#eee')
f.text((3, 4.4), '6 cm', dy=-4); f.text((-0.7, 2), '4 cm', anchor='end', dx=-20)
save(f, 'd3_2_fig')

# ---------- d3_3_fig (distance-time graph) ----------
f = Fig(300, 200, -4, 34, -250, 2000)
f.line((0, 0), (32, 0), width=1, arrow=True); f.line((0, 0), (0, 1900), width=1, arrow=True)
f.text((32, 0), 'x(分)', dx=-10, dy=14); f.text((0, 1900), 'y(m)', dx=14, dy=0); f.text((0, 0), 'O', dx=-8, dy=12)
f.poly([(0, 0), (10, 800), (15, 800), (30, 1800)], close=False, width=1.6)
for x, lab in [(10, '10'), (15, '15'), (30, '30')]:
    f.line((x, 0), (x, -60), width=0.8); f.text((x, -120), lab, size=10, dy=4)
for y, lab in [(800, '800'), (1800, '1800')]:
    f.line((0, y), (-0.5, y), width=0.8); f.text((-1, y), lab, size=10, anchor='end')
f.line((0, 800), (10, 800), dash=True, width=0.8); f.line((0, 1800), (30, 1800), dash=True, width=0.8); f.line((30, 0), (30, 1800), dash=True, width=0.8)
save(f, 'd3_3_fig')

# ---------- d3_4_fig ----------
f = Fig(230, 200, -5.5, 8, -1.5, 9.5)
f.axes(); f.poly([(0, 8), (-4, 0), (6, 0)]); f.dot((0, 8)); f.label((0, 8), 'A', 'r'); f.dot((-4, 0)); f.label((-4, 0), 'B', 'd'); f.dot((6, 0)); f.label((6, 0), 'C', 'd')
f.dot((4.5, 2)); f.label((4.5, 2), 'P', 'ur'); f.line((-4, 0), (4.5, 2), dash=True)
save(f, 'd3_4_fig')

# ---------- d4_1_fig (square ABCD, E on BC, F on CD) ----------
f = Fig(200, 200, -1, 8, -1, 8)
A, B, C, D = (0, 6), (0, 0), (6, 0), (6, 6)
f.poly([A, B, C, D]); f.label(A, 'A', 'ul'); f.label(B, 'B', 'dl'); f.label(C, 'C', 'dr'); f.label(D, 'D', 'ur')
E, F = (2.2, 0), (6, 2.2)
f.dot(E); f.label(E, 'E', 'd'); f.dot(F); f.label(F, 'F', 'r'); f.line(A, E); f.line(B, F)
f.tick(B, E); f.tick(C, F)
save(f, 'd4_1_fig')

# ---------- d4_1_ex (3 panels) ----------
h1 = Fig(170, 150, -1, 8, -1, 7)
A, B, C, D = (0.5, 5.5), (6.5, 0.5), (0.5, 1), (6.5, 5)
O = (3.5, 3)
h1.line(A, B); h1.line(C, D); h1.line(A, C); h1.line(B, D)
h1.label(A, 'A', 'ul'); h1.label(B, 'B', 'dr'); h1.label(C, 'C', 'dl'); h1.label(D, 'D', 'ur'); h1.label(O, 'O', 'u'); h1.text((3.5, 6.5), '1', size=12)
h2 = Fig(170, 150, -1, 8, -1, 7)
A, B, C = (3.5, 6), (0.5, 0.5), (6.5, 0.5); M = (3.5, 0.5)
h2.poly([A, B, C]); h2.line(A, M); h2.label(A, 'A', 'u'); h2.label(B, 'B', 'dl'); h2.label(C, 'C', 'dr'); h2.label(M, 'M', 'd'); h2.tick(A, B); h2.tick(A, C); h2.text((0.5, 6.5), '2', size=12)
h3 = Fig(170, 150, -1, 8, -1, 7)
A, B, C, D = (1.5, 5), (0.5, 0.5), (5.5, 0.5), (6.5, 5)
h3.poly([A, B, C, D]); h3.line(A, C); h3.label(A, 'A', 'ul'); h3.label(B, 'B', 'dl'); h3.label(C, 'C', 'dr'); h3.label(D, 'D', 'ur'); h3.text((3.5, 6.5), '3', size=12)
savep([h1, h2, h3], 'd4_1_ex')

# ---------- d4_2_fig (parallelogram with diagonals, P, Q) ----------
f = Fig(230, 170, -1, 9, -1, 6)
A, B, C, D = (1.5, 5), (0, 0), (6.5, 0), (8, 5)
f.poly([A, B, C, D]); f.line(A, C); f.line(B, D)
O = (4, 2.5); f.label(O, 'O', 'u')
P, Q = (3.2, 5), (4.8, 0)
f.line(P, Q); f.dot(P); f.dot(Q); f.label(P, 'P', 'u'); f.label(Q, 'Q', 'd')
f.label(A, 'A', 'ul'); f.label(B, 'B', 'dl'); f.label(C, 'C', 'dr'); f.label(D, 'D', 'ur')
save(f, 'd4_2_fig')

# ---------- d4_2_ex ----------
k1 = Fig(170, 150, -1, 8, -1, 7)
A, B, C = (3.5, 6), (0.5, 0.5), (6.5, 0.5)
D = (3.5 - 3 * 0.35, 6 - 5.5 * 0.35); E = (3.5 + 3 * 0.35, 6 - 5.5 * 0.35)
k1.poly([A, B, C]); k1.line(D, C); k1.line(E, B); k1.label(A, 'A', 'u'); k1.label(B, 'B', 'dl'); k1.label(C, 'C', 'dr'); k1.label(D, 'D', 'l'); k1.label(E, 'E', 'r'); k1.text((0.5, 6.5), '1', size=12)
k2 = Fig(170, 150, -1, 8, -1, 7)
A, B, C, D = (1.5, 5), (0, 0.5), (5.5, 0.5), (7, 5); M = (0.75, 2.75); N = (6.25, 2.75)
k2.poly([A, B, C, D]); k2.line(A, N); k2.line(M, C); k2.line(M, N, dash=True)
k2.label(A, 'A', 'ul'); k2.label(B, 'B', 'dl'); k2.label(C, 'C', 'dr'); k2.label(D, 'D', 'ur'); k2.label(M, 'M', 'l'); k2.label(N, 'N', 'r'); k2.text((3.5, 6.5), '2', size=12)
k3 = Fig(170, 150, -1, 8, -1, 7)
A, B, C = (3.5, 6), (0.5, 0.5), (6.5, 0.5); D = (3.5, 0.5)
k3.poly([A, B, C]); k3.line(A, D); k3.label(A, 'A', 'u'); k3.label(B, 'B', 'dl'); k3.label(C, 'C', 'dr'); k3.label(D, 'D', 'd')
k3.angle_mark(B, C, A, r=0.7); k3.angle_mark(C, A, B, r=0.7); k3.text((0.5, 6.5), '3', size=12)
savep([k1, k2, k3], 'd4_2_ex')

# ---------- d4_3_fig (5 panels) ----------
a1 = Fig(160, 150, -1, 8, -1, 7)
a1.line((0, 6), (7, 6)); a1.line((0, 0.5), (7, 0.5)); a1.text((7.2, 6), 'ℓ', anchor='start'); a1.text((7.2, 0.5), 'm', anchor='start')
P1, V, P2 = (1.5, 6), (4, 3.3), (6.5, 0.5)
a1.line(P1, V); a1.line(V, P2); a1.angle_mark(P1, (7, 6), V, r=0.8, label='a'); a1.angle_mark(P2, (0, 0.5), V, r=0.8, label='b'); a1.angle_mark(V, P1, P2, r=0.6, label='x'); a1.text((3.5, 6.8), '①', size=11, dx=-40)
a2 = Fig(160, 150, -1, 8, -1, 7)
A, B, C = (3, 6), (0.5, 0.5), (6.5, 0.5); I = (3, 2.2)
a2.poly([A, B, C]); a2.line(B, I); a2.line(C, I); a2.label(A, 'A', 'u'); a2.label(B, 'B', 'dl'); a2.label(C, 'C', 'dr'); a2.label(I, 'I', 'u'); a2.angle_mark(A, B, C, r=0.8, label='50°'); a2.text((0.5, 6.5), '②', size=11)
a3 = Fig(160, 150, -1, 9, -1, 7)
A, B, C, D = (2.5, 5.5), (0.5, 0.5), (4.5, 0.5), (7.5, 0.5)
a3.poly([A, B, C]); a3.line(C, D); a3.line(A, D); a3.label(A, 'A', 'u'); a3.label(B, 'B', 'dl'); a3.label(C, 'C', 'd'); a3.label(D, 'D', 'dr'); a3.tick(A, B); a3.tick(A, C); a3.tick(C, D); a3.angle_mark(B, C, A, r=0.7, label='70°'); a3.text((4, 6.8), '③', size=11, dx=-50)
a4 = Fig(160, 150, -1, 8, -1, 7)
cx, cy, r = 3.5, 3, 3
pts = [(cx + r * math.cos(math.radians(90 + 72 * i)), cy + r * math.sin(math.radians(90 + 72 * i))) for i in range(5)]
a4.poly(pts)
names = ['A', 'B', 'C', 'D', 'E']
for pnt, nm, pos in zip(pts, names, ['u', 'ul', 'dl', 'dr', 'ur']):
    a4.label(pnt, nm, pos)
a4.line(pts[0], pts[2]); a4.line(pts[1], pts[3]); a4.text((3.5, 6.8), '④', size=11, dx=-45)
a5 = Fig(160, 150, -1, 8, -1, 7)
Pp, Qp, Rp, Sp = (0.5, 6), (0.5, 0.5), (7, 3.25), (3, 3.25)
a5.poly([Pp, Rp, Qp, Sp])
a5.angle_mark(Pp, Sp, Rp, r=0.8, label='a'); a5.angle_mark(Rp, Pp, Qp, r=0.9, label='b'); a5.angle_mark(Qp, Rp, Sp, r=0.8, label='c')
a5.angle_mark(Sp, Pp, Qp, r=0.6, label='x')
a5.text((3.5, 6.8), '⑤', size=11, dx=-45)
savep([a1, a2, a3, a4, a5], 'd4_3_fig', gap=8)

# ---------- d4_4_fig ----------
b1 = Fig(200, 150, -1, 9, -1, 7)
A, B, C, D = (1, 4.5), (0.5, 0.5), (5, 0.5), (4.5, 5.5); E = (7.5, 0.5)
b1.poly([A, B, C, D]); b1.line(A, C); b1.line(C, E); b1.line(D, E, dash=True); b1.line(A, E, dash=True)
b1.label(A, 'A', 'ul'); b1.label(B, 'B', 'dl'); b1.label(C, 'C', 'd'); b1.label(D, 'D', 'ur'); b1.label(E, 'E', 'dr'); b1.text((4, 6.6), '①', size=11, dx=-50)
b2 = Fig(200, 150, -1, 9, -1, 7)
# cuboid: front face EFGH? draw ABCD top, EFGH bottom
E, F, G, H = (0.5, 0.5), (4.5, 0.5), (6.5, 2), (2.5, 2)
A, B, C, D = (0.5, 4.5), (4.5, 4.5), (6.5, 6), (2.5, 6)
b2.poly([E, F, G, H], dash=False); b2.poly([A, B, C, D]); b2.line(A, E); b2.line(B, F); b2.line(C, G); b2.line(D, H, dash=True)
b2.line(E, H, dash=True); b2.line(H, G, dash=True); b2.line(H, D, dash=True)
b2.line(A, F, dash=True); b2.line(A, H, dash=True); b2.line(F, H, dash=True)
for pnt, nm, pos in [(A, 'A', 'ul'), (B, 'B', 'ur'), (C, 'C', 'ur'), (D, 'D', 'ul'), (E, 'E', 'dl'), (F, 'F', 'dr'), (G, 'G', 'dr'), (H, 'H', 'ur')]:
    b2.label(pnt, nm, pos)
b2.text((4, 6.8), '②', size=11, dx=-70)
b3 = Fig(200, 150, -1, 9, -1, 7)
A, D, B, C = (2, 5), (5.5, 5), (0.5, 0.5), (7.5, 0.5)
b3.poly([A, B, C, D]); b3.line(A, C); b3.line(B, D); O = (3.6, 2.6)
b3.label(A, 'A', 'ul'); b3.label(D, 'D', 'ur'); b3.label(B, 'B', 'dl'); b3.label(C, 'C', 'dr'); b3.label(O, 'O', 'r'); b3.text((4, 6.6), '③', size=11, dx=-50)
savep([b1, b2, b3], 'd4_4_fig')

# ---------- m1_d2 ----------
n1 = Fig(170, 150, -1, 8, -1, 7)
tri(n1, (2.5, 6), (0.5, 0.5), (7, 0.5)); n1.text((0.5, 6.5), '(1)', size=11)
n2figs = []
for n in (1, 2, 3):
    f = Fig(90, 110, -0.7, 3.7, -1.3, 3.5)
    side = n + 1
    hgt = 3 * math.sqrt(3) / 2
    for i in range(side):
        for j in range(side - i):
            if i == 0 or j == 0 or i + j == side - 1:
                x = (j + i / 2) * 3 / (side - 1)
                y = i * hgt / (side - 1)
                f.dot((x, y), r=4)
    f.text((1.5, -1.0), '%d番目' % n, size=10, dy=4)
    n2figs.append(f)
n3 = Fig(170, 150, -1, 8, -1, 7)
n3.line((0, 6), (7, 6)); n3.line((0, 0.5), (7, 0.5)); n3.text((7.2, 6), 'ℓ', anchor='start'); n3.text((7.2, 0.5), 'm', anchor='start')
P1, V, P2 = (1.5, 6), (4, 3.3), (6.5, 0.5)
n3.line(P1, V); n3.line(V, P2); n3.angle_mark(P1, (7, 6), V, r=0.8, label='35°'); n3.angle_mark(P2, (0, 0.5), V, r=0.8, label='50°'); n3.angle_mark(V, P1, P2, r=0.6, label='x'); n3.text((0.5, 6.7), '(5)', size=11)
lbl = Fig(40, 110, 0, 1, 0, 1); lbl.text((0.5, 0.9), '(4)', size=11)
savep([n1, lbl] + n2figs + [n3], 'm1_d2', gap=8)

# ---------- m1_d3 ----------
f = Fig(230, 230, -2, 8, -1.5, 9)
f.axes(); f.func(lambda x: -x + 7, -1, 7.5); f.func(lambda x: 2 * x + 1, -1, 3.8)
f.dot((2, 5)); f.label((2, 5), 'A', 'r'); f.dot((0, 7)); f.label((0, 7), 'B', 'l'); f.dot((0, 1)); f.label((0, 1), 'C', 'l')
f.text((7.5, -0.5), 'ℓ', anchor='start'); f.text((3.8, 8.6), 'm', anchor='start')
save(f, 'm1_d3')

# ---------- m1_d4 ----------
r1 = Fig(200, 150, -1, 9, -1, 6.5)
A, B, C, D = (1.5, 5), (0, 0.5), (6.5, 0.5), (8, 5)
r1.poly([A, B, C, D]); r1.line(B, D)
E = (0 + (8 - 0) * 0.25, 0.5 + 4.5 * 0.25); F = (0 + 8 * 0.75, 0.5 + 4.5 * 0.75)
r1.dot(E); r1.dot(F); r1.line(A, E); r1.line(C, F); r1.label(E, 'E', 'dr'); r1.label(F, 'F', 'ul')
r1.label(A, 'A', 'ul'); r1.label(B, 'B', 'dl'); r1.label(C, 'C', 'dr'); r1.label(D, 'D', 'ur'); r1.text((4, 6.2), '(1)', size=11, dx=-70)
r2 = Fig(180, 150, -1, 8, -1, 6.5)
A, B, C = (2.5, 5.5), (0.5, 0.5), (7, 0.5); D = (3.3, 0.5)
r2.poly([A, B, C]); r2.line(A, D); r2.label(A, 'A', 'u'); r2.label(B, 'B', 'dl'); r2.label(C, 'C', 'dr'); r2.label(D, 'D', 'd'); r2.angle_mark(A, B, D, r=0.7, label='25°'); r2.tick(A, D); r2.tick(B, D); r2.text((0.5, 6.2), '(2)', size=11)
r3 = Fig(200, 150, -1, 9, -1, 6.5)
A, B, C, D = (1.5, 5), (0, 0.5), (6.5, 0.5), (8, 5); E = (3.25, 0.5); F = (7.25, 2.75)
r3.poly([A, B, C, D]); r3.poly([A, E, F], fill='#eee'); r3.dot(E); r3.dot(F)
r3.label(A, 'A', 'ul'); r3.label(B, 'B', 'dl'); r3.label(C, 'C', 'dr'); r3.label(D, 'D', 'ur'); r3.label(E, 'E', 'd'); r3.label(F, 'F', 'r'); r3.text((4, 6.2), '(3)', size=11, dx=-70)
savep([r1, r2, r3], 'm1_d4', gap=10)

# ---------- m2_d2 ----------
s1 = Fig(170, 150, -1, 8, -1, 7)
s1.line((1, 1.5), (6, 1.5)); s1.dot((1, 1.5)); s1.dot((6, 1.5)); s1.label((1, 1.5), 'A', 'dl'); s1.label((6, 1.5), 'B', 'dr'); s1.text((0.5, 6.5), '(1)', size=11)
# box plot as separate fig object
bx = Fig(420, 150, -6, 48, -1.2, 3.2)
for i, (lab, (mn, q1, md, q3, mx)) in enumerate([('A組', (5, 12, 20, 28, 38)), ('B組', (8, 15, 22, 25, 35))]):
    y = 2.2 - i * 1.3
    bx.line((mn, y), (q1, y)); bx.line((q3, y), (mx, y))
    bx.poly([(q1, y - 0.35), (q3, y - 0.35), (q3, y + 0.35), (q1, y + 0.35)], fill='#eee')
    bx.line((md, y - 0.35), (md, y + 0.35), width=1.6)
    bx.line((mn, y - 0.2), (mn, y + 0.2)); bx.line((mx, y - 0.2), (mx, y + 0.2))
    bx.text((-3, y), lab)
bx.line((0, 0), (45, 0), width=1)
for x in range(0, 46, 5):
    bx.line((x, -0.1), (x, 0.1), width=0.8); bx.text((x, -0.35), str(x), size=10, dy=6)
bx.text((22, -1.0), '(3) 通学時間（分）', size=10, dy=6)
savep([s1, bx], 'm2_d2', gap=20)

# ---------- m2_d4 ----------
t1 = Fig(200, 160, -1, 8, -1, 7)
A, B, C = (3.5, 6), (0.5, 0.5), (6.5, 0.5); M = (3.5, 0.5)
t1.poly([A, B, C]); t1.tick(A, B); t1.tick(A, C)
# foot of perpendicular from M to AB and AC
def foot(P, U, V):
    ux, uy = V[0] - U[0], V[1] - U[1]
    t = ((P[0] - U[0]) * ux + (P[1] - U[1]) * uy) / (ux * ux + uy * uy)
    return (U[0] + t * ux, U[1] + t * uy)
D = foot(M, A, B); E = foot(M, A, C)
t1.line(M, D); t1.line(M, E); t1.right_angle(D, A, M); t1.right_angle(E, A, M)
t1.label(A, 'A', 'u'); t1.label(B, 'B', 'dl'); t1.label(C, 'C', 'dr'); t1.label(M, 'M', 'd'); t1.label(D, 'D', 'l'); t1.label(E, 'E', 'r'); t1.text((0.5, 6.6), '図①', size=11)
t2 = Fig(200, 160, -1, 9, -1, 7)
A, D, B, C = (2.5, 5), (5, 5), (0.5, 0.5), (7.5, 0.5)
t2.poly([A, B, C, D]); t2.line(A, C); t2.line(B, D); O = (3.4, 3.3)
t2.label(A, 'A', 'ul'); t2.label(D, 'D', 'ur'); t2.label(B, 'B', 'dl'); t2.label(C, 'C', 'dr'); t2.label(O, 'O', 'r'); t2.text((0.5, 6.6), '図②', size=11)
savep([t1, t2], 'm2_d4')

print('figures written:', len(os.listdir(OUT)))
