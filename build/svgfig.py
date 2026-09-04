# -*- coding: utf-8 -*-
"""Tiny SVG helper for geometry figures (math coordinates: y up)."""
import math


class Fig:
    def __init__(self, w=260, h=200, xmin=-1, xmax=9, ymin=-1, ymax=7, font=13):
        self.w, self.h = w, h
        self.xmin, self.xmax, self.ymin, self.ymax = xmin, xmax, ymin, ymax
        self.font = font
        self.items = []

    def P(self, x, y):
        sx = (x - self.xmin) / (self.xmax - self.xmin) * self.w
        sy = self.h - (y - self.ymin) / (self.ymax - self.ymin) * self.h
        return sx, sy

    def line(self, a, b, dash=False, width=1.3, color='#000', arrow=False):
        x1, y1 = self.P(*a)
        x2, y2 = self.P(*b)
        d = ' stroke-dasharray="5,4"' if dash else ''
        m = ' marker-end="url(#arr)"' if arrow else ''
        self.items.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.1f"%s%s/>' % (x1, y1, x2, y2, color, width, d, m))

    def poly(self, pts, fill='none', dash=False, width=1.3, color='#000', close=True):
        s = ' '.join('%.1f,%.1f' % self.P(*p) for p in pts)
        d = ' stroke-dasharray="5,4"' if dash else ''
        tag = 'polygon' if close else 'polyline'
        self.items.append('<%s points="%s" fill="%s" stroke="%s" stroke-width="%.1f"%s/>' % (tag, s, fill, color, width, d))

    def circle(self, c, r, fill='none', dash=False, width=1.3, color='#000'):
        cx, cy = self.P(*c)
        rx = r / (self.xmax - self.xmin) * self.w
        d = ' stroke-dasharray="5,4"' if dash else ''
        self.items.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="%s" stroke-width="%.1f"%s/>' % (cx, cy, rx, fill, color, width, d))

    def dot(self, p, r=3, color='#000'):
        cx, cy = self.P(*p)
        self.items.append('<circle cx="%.1f" cy="%.1f" r="%d" fill="%s"/>' % (cx, cy, r, color))

    def text(self, p, s, dx=0, dy=0, size=None, anchor='middle', italic=False, color='#000'):
        cx, cy = self.P(*p)
        st = ' font-style="italic"' if italic else ''
        self.items.append('<text x="%.1f" y="%.1f" font-size="%d" text-anchor="%s" fill="%s"%s font-family="Noto Serif, Noto Serif CJK JP, serif">%s</text>' % (cx + dx, cy + dy + 4, size or self.font, anchor, color, st, s))

    def label(self, p, s, pos='ur'):
        off = {'ur': (5, -5), 'ul': (-5, -5), 'dr': (5, 12), 'dl': (-5, 12), 'u': (0, -8), 'd': (0, 14), 'l': (-8, 0), 'r': (8, 0)}
        dx, dy = off[pos]
        anchor = {'ur': 'start', 'ul': 'end', 'dr': 'start', 'dl': 'end', 'u': 'middle', 'd': 'middle', 'l': 'end', 'r': 'start'}[pos]
        self.text(p, s, dx, dy, anchor=anchor, italic=True)

    def arc(self, c, r, a1, a2, width=1.2, color='#000', dash=False):
        """arc centered c (math coords), radius r (x units), angles in degrees (math orientation, ccw)"""
        cx, cy = self.P(*c)
        rx = r / (self.xmax - self.xmin) * self.w
        ry = r / (self.ymax - self.ymin) * self.h
        a1r, a2r = math.radians(a1), math.radians(a2)
        x1, y1 = cx + rx * math.cos(a1r), cy - ry * math.sin(a1r)
        x2, y2 = cx + rx * math.cos(a2r), cy - ry * math.sin(a2r)
        large = 1 if (a2 - a1) % 360 > 180 else 0
        d = ' stroke-dasharray="4,3"' if dash else ''
        self.items.append('<path d="M %.1f %.1f A %.1f %.1f 0 %d 0 %.1f %.1f" fill="none" stroke="%s" stroke-width="%.1f"%s/>' % (x1, y1, rx, ry, large, x2, y2, color, width, d))

    def angle_mark(self, v, a, b, r=0.6, label=None, double=False):
        """angle at vertex v between rays toward a and b"""
        a1 = math.degrees(math.atan2(a[1] - v[1], a[0] - v[0]))
        a2 = math.degrees(math.atan2(b[1] - v[1], b[0] - v[0]))
        # ensure ccw from a1 to a2 smaller than 180
        if (a2 - a1) % 360 > 180:
            a1, a2 = a2, a1
        self.arc(v, r, a1, a2)
        if double:
            self.arc(v, r * 1.25, a1, a2)
        if label:
            mid = math.radians((a1 + ((a2 - a1) % 360) / 2))
            self.text((v[0] + r * 1.9 * math.cos(mid), v[1] + r * 1.9 * math.sin(mid)), label, size=self.font - 1)

    def right_angle(self, v, a, b, s=0.35):
        ux = (a[0] - v[0], a[1] - v[1])
        uy = (b[0] - v[0], b[1] - v[1])
        lu = math.hypot(*ux)
        lv = math.hypot(*uy)
        ux = (ux[0] / lu * s, ux[1] / lu * s)
        uy = (uy[0] / lv * s, uy[1] / lv * s)
        p1 = (v[0] + ux[0], v[1] + ux[1])
        p2 = (v[0] + ux[0] + uy[0], v[1] + ux[1] + uy[1])
        p3 = (v[0] + uy[0], v[1] + uy[1])
        self.poly([p1, p2, p3], close=False, width=1)

    def tick(self, a, b, n=1, s=0.18):
        """equal-length marks on segment ab"""
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L * s, dx / L * s
        tx, ty = dx / L * 0.12, dy / L * 0.12
        for i in range(n):
            off = (i - (n - 1) / 2)
            cx, cy = mx + tx * off, my + ty * off
            self.line((cx - nx, cy - ny), (cx + nx, cy + ny), width=1)

    def axes(self, xlab='x', ylab='y', ticks=True):
        self.line((self.xmin, 0), (self.xmax, 0), width=1, arrow=True)
        self.line((0, self.ymin), (0, self.ymax), width=1, arrow=True)
        self.text((self.xmax, 0), xlab, dx=-8, dy=14, italic=True)
        self.text((0, self.ymax), ylab, dx=-10, dy=8, italic=True)
        self.text((0, 0), 'O', dx=-8, dy=12)
        if ticks:
            for x in range(int(math.ceil(self.xmin)), int(self.xmax) + 1):
                if x != 0:
                    self.line((x, -0.1), (x, 0.1), width=0.8)
            for y in range(int(math.ceil(self.ymin)), int(self.ymax) + 1):
                if y != 0:
                    self.line((-0.1, y), (0.1, y), width=0.8)

    def grid(self, step=1, color='#ccc'):
        for x in range(int(math.ceil(self.xmin)), int(self.xmax) + 1):
            self.line((x, self.ymin), (x, self.ymax), width=0.5, color=color)
        for y in range(int(math.ceil(self.ymin)), int(self.ymax) + 1):
            self.line((self.xmin, y), (self.xmax, y), width=0.5, color=color)

    def func(self, f, x0, x1, n=80, width=1.5, color='#000'):
        pts = []
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i / n
            pts.append((x, f(x)))
        self.poly(pts, close=False, width=width, color=color)

    def svg(self):
        defs = '<defs><marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#000"/></marker></defs>'
        return '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">%s%s</svg>' % (self.w, self.h, self.w, self.h, defs, ''.join(self.items))

    def save(self, path):
        open(path, 'w', encoding='utf-8').write(self.svg())
