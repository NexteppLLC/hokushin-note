# -*- coding: utf-8 -*-
"""Generate 16 sets of 12 大問1-style calculation problems with verified answers."""
import os, sys, json, random, math
from fractions import Fraction as F
sys.path.insert(0, os.path.dirname(__file__))
import editions as ED
EDITION, _args = ED.resolve(sys.argv[1:])

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rng = random.Random(20261011)


def fmt_int(n):
    return str(n) if n >= 0 else '-%d' % (-n)


def pn(n):
    """parenthesize negatives for use after an operator"""
    return '(%s)' % fmt_int(n) if n < 0 else str(n)


def fmt_frac(fr):
    fr = F(fr)
    if fr.denominator == 1:
        return fmt_int(fr.numerator)
    s = '\\frac{%d}{%d}' % (abs(fr.numerator), fr.denominator)
    return ('-' if fr < 0 else '') + s


def term(coef, var, first=False):
    """format coef*var for polynomial display"""
    c = F(coef)
    if c == 0:
        return ''
    sign = '-' if c < 0 else ('' if first else '+')
    a = abs(c)
    if var == '':
        body = fmt_frac(a)
    elif a == 1:
        body = var
    else:
        body = fmt_frac(a) + var
    return sign + body


def poly(terms):
    """terms: list of (coef, var). returns latex-ish string"""
    out = ''
    first = True
    for c, v in terms:
        t = term(c, v, first)
        if t:
            out += t
            first = False
    return out if out else '0'


def sqrt_simplify(n):
    """n>0 -> (k, m) with sqrt(n) = k*sqrt(m), m squarefree"""
    k = 1
    m = n
    p = 2
    while p * p <= m:
        while m % (p * p) == 0:
            m //= (p * p)
            k *= p
        p += 1
    return k, m


def fmt_sqrt(k, m, coef_only=False):
    if m == 1:
        return fmt_int(k)
    if k == 1:
        return '\\sqrt{%d}' % m
    if k == -1:
        return '-\\sqrt{%d}' % m
    return '%s\\sqrt{%d}' % (fmt_int(k), m)


# ---------------- problem generators ----------------

def p_seifu():
    kind = rng.choice(['a', 'b', 'c'])
    if kind == 'a':  # a + b × c
        a = rng.choice([-9, -7, -6, -5, -4, 3, 5, 8])
        b = rng.choice([-4, -3, -2, 2, 3, 4])
        c = rng.choice([-6, -5, -3, 2, 4, 7])
        q = '%s + %s \\times %s' % (fmt_int(a), pn(b), pn(c))
        ans = a + b * c
        return '$%s$ を計算しなさい。' % q, '$%s$' % fmt_int(ans)
    if kind == 'b':  # a - b ÷ c  with exact
        c = rng.choice([-4, -3, 3, 4, 6])
        k = rng.choice([-5, -3, -2, 2, 3, 4])
        b = k * c
        a = rng.choice([-8, -6, -3, 2, 5, 9])
        q = '%s - %s \\div %s' % (fmt_int(a), pn(b), pn(c))
        ans = a - b // c
        return '$%s$ を計算しなさい。' % q, '$%s$' % fmt_int(ans)
    # (-a)^2 - b × c
    a = rng.choice([2, 3, 4, 5])
    b = rng.choice([2, 3, 4])
    c = rng.choice([-5, -3, -2, 3, 6])
    q = '(-%d)^2 - %d \\times %s' % (a, b, pn(c))
    ans = a * a - b * c
    return '$%s$ を計算しなさい。' % q, '$%s$' % fmt_int(ans)


def p_mojishiki():
    kind = rng.choice(['a', 'b'])
    if kind == 'a':  # a(bx + cy) - d(ex + fy)
        a = rng.choice([2, 3, 4, 5])
        b = rng.choice([1, 2, 3])
        c = rng.choice([-3, -2, -1, 1, 2])
        d = rng.choice([2, 3, 4])
        e = rng.choice([1, 2, 3])
        f = rng.choice([-2, -1, 1, 2, 3])
        q = '%d(%s) - %d(%s)' % (a, poly([(b, 'x'), (c, 'y')]), d, poly([(e, 'x'), (f, 'y')]))
        ans = poly([(a * b - d * e, 'x'), (a * c - d * f, 'y')])
        return '$%s$ を計算しなさい。' % q, '$%s$' % ans
    # monomial: (a x^2 y) × (b x y^2) ÷ (c x y) style -> keep simple: 8x^2y ÷ 2xy × 3y
    a = rng.choice([4, 6, 8, 12])
    c = rng.choice([2, 4])
    if a % c:
        c = 2
    d = rng.choice([2, 3, 5])
    q = '%dx^2y \\div %dxy \\times %dy' % (a, c, d)
    coef = a // c * d
    return '$%s$ を計算しなさい。' % q, '$%dxy$' % coef


def p_bunsu():
    # (ax + by)/p - (cx + dy)/q  with p,q in {2,3,4,6}
    p, q = rng.choice([(2, 3), (3, 2), (3, 4), (2, 5), (4, 3)])
    a = rng.choice([1, 2, 3])
    b = rng.choice([-2, -1, 1, 2])
    c = rng.choice([1, 2])
    d = rng.choice([-3, -1, 1, 2])
    L = p * q // math.gcd(p, q)
    nx = F(a, p) - F(c, q)
    ny = F(b, p) - F(d, q)
    qs = '\\frac{%s}{%d} - \\frac{%s}{%d}' % (poly([(a, 'x'), (b, 'y')]), p, poly([(c, 'x'), (d, 'y')]), q)
    # answer as single fraction
    num = poly([(nx * L, 'x'), (ny * L, 'y')])
    ans = '\\frac{%s}{%d}' % (num, L)
    if nx * L == 0 or ny * L == 0:
        ans = poly([(nx, 'x'), (ny, 'y')])
    return '$%s$ を計算しなさい。' % qs, '$%s$' % ans


def p_ichiji():
    x = rng.choice([-4, -3, -2, 2, 3, 4, 5])
    a = rng.choice([2, 3, 4, 5])
    b = rng.choice([-7, -5, -3, 1, 4, 6])
    c = rng.choice([2, 3])
    # a x + b = c(x + k) -> choose k so that solution is x
    # a x + b = c x + c k -> (a-c) x = ck - b -> k = ((a-c)x + b)/c must be integer
    if a == c:
        a += 1
    k_num = (a - c) * x + b
    if k_num % c:
        # adjust b
        b = b + (c - k_num % c)
        k_num = (a - c) * x + b
    k = k_num // c
    q = '%s = %d(%s)' % (poly([(a, 'x'), (b, '')]), c, poly([(1, 'x'), (k, '')]))
    return '一次方程式 $%s$ を解きなさい。' % q, '$x = %s$' % fmt_int(x)


def p_renritsu():
    x = rng.choice([-3, -2, -1, 1, 2, 3, 4])
    y = rng.choice([-3, -2, -1, 1, 2, 3, 5])
    a1, b1 = rng.choice([(2, 1), (3, 2), (1, 3), (2, -1), (3, -2), (5, 2)])
    a2, b2 = rng.choice([(1, -1), (3, 1), (1, 2), (4, -3), (2, 3)])
    if a1 * b2 - a2 * b1 == 0:
        a2 += 1
    c1 = a1 * x + b1 * y
    c2 = a2 * x + b2 * y
    q = '\\begin{cases}%s = %s \\\\ %s = %s\\end{cases}'
    e1 = '%s = %s' % (poly([(a1, 'x'), (b1, 'y')]), fmt_int(c1))
    e2 = '%s = %s' % (poly([(a2, 'x'), (b2, 'y')]), fmt_int(c2))
    return '連立方程式 $%s$，$%s$ を解きなさい。' % (e1, e2), '$x = %s，y = %s$' % (fmt_int(x), fmt_int(y))


def p_tenkai_insu():
    kind = rng.choice(['t1', 't2', 'i1', 'i2', 'i3'])
    if kind == 't1':
        a = rng.choice([-5, -3, -2, 2, 3, 4, 6])
        b = rng.choice([-4, -2, -1, 1, 3, 5])
        q = '(%s)(%s)' % (poly([(1, 'x'), (a, '')]), poly([(1, 'x'), (b, '')]))
        return '$%s$ を展開しなさい。' % q, '$%s$' % poly([(1, 'x^2'), (a + b, 'x'), (a * b, '')])
    if kind == 't2':
        a = rng.choice([-6, -4, -3, 2, 3, 5, 7])
        q = '(%s)^2' % poly([(1, 'x'), (a, '')])
        return '$%s$ を展開しなさい。' % q, '$%s$' % poly([(1, 'x^2'), (2 * a, 'x'), (a * a, '')])
    if kind == 'i1':
        a = rng.choice([-6, -5, -3, -2, 2, 3, 4, 7])
        b = rng.choice([-4, -3, -2, -1, 1, 2, 5, 6])
        if a == b:
            b = -b
        q = poly([(1, 'x^2'), (a + b, 'x'), (a * b, '')])
        lo, hi = sorted([a, b])
        return '$%s$ を因数分解しなさい。' % q, '$(%s)(%s)$' % (poly([(1, 'x'), (lo, '')]), poly([(1, 'x'), (hi, '')]))
    if kind == 'i2':
        a = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
        q = poly([(1, 'x^2'), (0, 'x'), (-a * a, '')])
        return '$%s$ を因数分解しなさい。' % q, '$(x + %d)(x - %d)$' % (a, a)
    a = rng.choice([-5, -4, -3, 2, 3, 6])
    k = rng.choice([2, 3])
    q = poly([(k, 'x^2'), (k * 2 * a, 'x'), (k * a * a, '')])
    return '$%s$ を因数分解しなさい。' % q, '$%d(%s)^2$' % (k, poly([(1, 'x'), (a, '')]))


def p_heihoukon():
    kind = rng.choice(['a', 'b', 'c', 'd'])
    if kind == 'a':  # sqrt(m) × sqrt(n)
        m, n = rng.choice([(6, 8), (3, 12), (2, 18), (5, 10), (6, 3), (14, 7), (15, 6), (12, 10)])
        k, r = sqrt_simplify(m * n)
        return '$\\sqrt{%d} \\times \\sqrt{%d}$ を計算しなさい。' % (m, n), '$%s$' % fmt_sqrt(k, r)
    if kind == 'b':  # sqrt(a) + sqrt(b) same radical
        r = rng.choice([2, 3, 5, 6, 7])
        k1 = rng.choice([2, 3, 4, 5])
        k2 = rng.choice([1, 2, 3])
        sign = rng.choice([1, -1])
        a = k1 * k1 * r
        b = k2 * k2 * r
        res = k1 + sign * k2
        q = '\\sqrt{%d} %s \\sqrt{%d}' % (a, '+' if sign > 0 else '-', b)
        return '$%s$ を計算しなさい。' % q, '$%s$' % fmt_sqrt(res, r)
    if kind == 'c':  # rationalize a/sqrt(b)
        b = rng.choice([2, 3, 5, 6, 7])
        a = rng.choice([b, 2 * b, 3 * b, b * b])
        # a/sqrt(b) = a sqrt(b)/b
        c = F(a, b)
        coef = c
        if coef.denominator == 1:
            return '$\\frac{%d}{\\sqrt{%d}}$ の分母を有理化しなさい。' % (a, b), '$%s$' % fmt_sqrt(int(coef), b)
        return '$\\frac{%d}{\\sqrt{%d}}$ の分母を有理化しなさい。' % (a, b), '$\\frac{%d\\sqrt{%d}}{%d}$' % (coef.numerator, b, coef.denominator)
    # (sqrt(a) + b)(sqrt(a) - b) or (sqrt a + sqrt b)^2
    a = rng.choice([2, 3, 5, 6, 7])
    b = rng.choice([1, 2, 3])
    sub = rng.choice([True, False])
    if sub:
        return '$(\\sqrt{%d} + %d)(\\sqrt{%d} - %d)$ を計算しなさい。' % (a, b, a, b), '$%s$' % fmt_int(a - b * b)
    # (sqrt a + b)^2 = a + b^2 + 2b sqrt a
    return '$(\\sqrt{%d} + %d)^2$ を計算しなさい。' % (a, b), '$%d + %s$' % (a + b * b, fmt_sqrt(2 * b, a))


def p_nijihouteishiki():
    kind = rng.choice(['f', 'f', 's', 'q', 'q'])
    if kind == 'f':  # factorable
        a = rng.choice([-7, -6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6])
        b = rng.choice([-8, -5, -4, -3, -2, 1, 2, 3, 5, 7])
        if a == b:
            b = -b
        # (x - a)(x - b) = x^2 - (a+b)x + ab
        q = '%s = 0' % poly([(1, 'x^2'), (-(a + b), 'x'), (a * b, '')])
        lo, hi = sorted([a, b])
        return '二次方程式 $%s$ を解きなさい。' % q, '$x = %s，%s$' % (fmt_int(lo), fmt_int(hi))
    if kind == 's':  # (x + m)^2 = k
        m = rng.choice([-5, -3, -2, 1, 2, 4])
        k = rng.choice([2, 3, 5, 7, 10, 11])
        q = '(%s)^2 = %d' % (poly([(1, 'x'), (m, '')]), k)
        return '二次方程式 $%s$ を解きなさい。' % q, '$x = %s \\pm \\sqrt{%d}$' % (fmt_int(-m), k)
    # formula: x^2 + bx + c = 0 with D>0 non-square
    while True:
        b = rng.choice([-7, -5, -3, -1, 1, 3, 5, 7, 2, 4, 6])
        c = rng.choice([-5, -3, -2, -1, 1, 2, 3])
        D = b * b - 4 * c
        if D > 0 and int(math.isqrt(D)) ** 2 != D:
            break
    k, r = sqrt_simplify(D)
    # x = (-b ± k√r)/2
    if k % 2 == 0 and b % 2 == 0:
        ans = '$x = %s \\pm %s$' % (fmt_int(-b // 2), fmt_sqrt(k // 2, r))
    else:
        ans = '$x = \\frac{%s \\pm %s}{2}$' % (fmt_int(-b), fmt_sqrt(k, r))
    q = '%s = 0' % poly([(1, 'x^2'), (b, 'x'), (c, '')])
    return '二次方程式 $%s$ を解きなさい。' % q, ans


def p_ichijikansu():
    kind = rng.choice(['a', 'b', 'c'])
    if kind == 'a':  # through two points
        a = rng.choice([-3, -2, -1, 1, 2, 3])
        b = rng.choice([-5, -3, -1, 1, 2, 4])
        x1 = rng.choice([-3, -2, -1, 1, 2])
        x2 = x1 + rng.choice([2, 3, 4])
        y1, y2 = a * x1 + b, a * x2 + b
        return '2点 $(%s, %s)$，$(%s, %s)$ を通る直線の式を求めなさい。' % (fmt_int(x1), fmt_int(y1), fmt_int(x2), fmt_int(y2)), '$y = %s$' % poly([(a, 'x'), (b, '')])
    if kind == 'b':  # 変化の割合 & 式 from slope and point
        a = rng.choice([-4, -2, 2, 3, 5])
        b = rng.choice([-6, -2, 1, 3, 7])
        x1 = rng.choice([-2, -1, 1, 2, 3])
        y1 = a * x1 + b
        return '変化の割合が $%s$ で、点 $(%s, %s)$ を通る一次関数の式を求めなさい。' % (fmt_int(a), fmt_int(x1), fmt_int(y1)), '$y = %s$' % poly([(a, 'x'), (b, '')])
    # y = ax+b, x range -> y range
    a = rng.choice([-3, -2, 2, 3])
    b = rng.choice([-4, -1, 1, 5])
    x1 = rng.choice([-3, -2, -1])
    x2 = rng.choice([1, 2, 3, 4])
    ys = sorted([a * x1 + b, a * x2 + b])
    return '一次関数 $y = %s$ で、$x$ の変域が $%s \\le x \\le %s$ のときの $y$ の変域を求めなさい。' % (poly([(a, 'x'), (b, '')]), fmt_int(x1), fmt_int(x2)), '$%s \\le y \\le %s$' % (fmt_int(ys[0]), fmt_int(ys[1]))


def p_hirei():
    kind = rng.choice(['p', 'r'])
    if kind == 'p':
        a = rng.choice([-4, -3, -2, 2, 3, 5])
        x1 = rng.choice([-3, -2, 2, 4])
        return '$y$ は $x$ に比例し、$x = %s$ のとき $y = %s$ である。$y$ を $x$ の式で表しなさい。' % (fmt_int(x1), fmt_int(a * x1)), '$y = %s$' % poly([(a, 'x')])
    a = rng.choice([-24, -12, -8, 6, 12, 18, 20])
    divs = [d for d in [-6, -4, -3, -2, 2, 3, 4, 6] if a % d == 0]
    x1 = rng.choice(divs)
    return '$y$ は $x$ に反比例し、$x = %s$ のとき $y = %s$ である。$y$ を $x$ の式で表しなさい。' % (fmt_int(x1), fmt_int(a // x1)), '$y = \\frac{%d}{x}$' % a if a > 0 else '$y = -\\frac{%d}{x}$' % (-a)


def p_shikinoatai():
    kind = rng.choice(['v', 'e'])
    if kind == 'v':
        x = rng.choice([-3, -2, 2, 3, 4])
        y = rng.choice([-4, -2, -1, 1, 3, 5])
        a = rng.choice([2, 3, 5])
        b = rng.choice([-3, -2, 2, 4])
        val = a * x * x - b * y
        return '$x = %s$，$y = %s$ のとき、$%s$ の値を求めなさい。' % (fmt_int(x), fmt_int(y), poly([(a, 'x^2'), (-b, 'y')])), '$%s$' % fmt_int(val)
    # 等式変形: solve for b in a formula like 2a + 3b = c -> b = (c - 2a)/3 ; or S = (a+b)h/2 -> a
    a = rng.choice([2, 3, 4, 5])
    b = rng.choice([2, 3, 5])
    return '等式 $%dx + %dy = 12$ を $y$ について解きなさい。' % (a, b), '$y = \\frac{12 - %dx}{%d}$' % (a, b) if b != 1 else '$y = 12 - %dx$' % a


def p_kakuritsu():
    kind = rng.choice(['dice_sum', 'coin', 'card'])
    if kind == 'dice_sum':
        s = rng.choice([5, 6, 7, 8, 9, 10])
        cnt = sum(1 for i in range(1, 7) for j in range(1, 7) if i + j == s)
        fr = F(cnt, 36)
        return '大小2つのさいころを同時に投げるとき、出た目の和が $%d$ になる確率を求めなさい。' % s, '$%s$' % fmt_frac(fr)
    if kind == 'coin':
        n = rng.choice([2, 3])
        if n == 2:
            return '2枚の硬貨を同時に投げるとき、1枚が表で1枚が裏になる確率を求めなさい。', '$\\frac{1}{2}$'
        return '3枚の硬貨を同時に投げるとき、少なくとも1枚は表になる確率を求めなさい。', '$\\frac{7}{8}$'
    n = rng.choice([5, 6, 8])
    return '1から%dまでの数字を1つずつ書いた%d枚のカードから1枚引くとき、その数が奇数である確率を求めなさい。' % (n, n), '$%s$' % fmt_frac(F(sum(1 for i in range(1, n + 1) if i % 2), n))


def p_shiryo():
    kind = rng.choice(['mean', 'median', 'range'])
    data = sorted(rng.sample(range(2, 20), 7))
    if kind == 'mean':
        while sum(data) % 7:
            data = sorted(rng.sample(range(2, 20), 7))
        return '次のデータの平均値を求めなさい。　%s' % '，'.join(str(d) for d in data), '$%d$' % (sum(data) // 7)
    if kind == 'median':
        return '次のデータの中央値を求めなさい。　%s' % '，'.join(str(d) for d in rng.sample(data, 7)), '$%d$' % data[3]
    return '次のデータの範囲（レンジ）を求めなさい。　%s' % '，'.join(str(d) for d in rng.sample(data, 7)), '$%d$' % (data[-1] - data[0])


GEN = [p_seifu, p_mojishiki, p_bunsu, p_ichiji, p_renritsu, p_tenkai_insu, p_heihoukon, p_nijihouteishiki, p_ichijikansu, p_hirei, p_shikinoatai, None]

sets = []
for s in range(16):
    probs = []
    for i, g in enumerate(GEN):
        if g is None:
            g = p_kakuritsu if s % 2 == 0 else p_shiryo
        q, a = g()
        probs.append({'no': i + 1, 'q': q, 'a': a})
    sets.append(probs)

out = ['# 2　大問1 計算ドリル（16回）', '',
       ''':::box 計算ドリルのやり方（1回12分）
- 北辰の大問1（12問・46点）と同じ並び：正負の数 → 文字式 → 分数の式 → 一次方程式 → 連立方程式 → 展開・因数分解 → 平方根 → **二次方程式（新範囲）** → 一次関数 → 比例・反比例 → 式の値・等式変形 → 確率・資料。
- **12分**を計って解く。終わったら答え合わせ。**間違えた問題は、途中式を書いて解き直す**。
- 配点は本番と同じ（4点×10問＋3点×2問＝46点）。目標：毎回42点以上。ミスの種類（符号／移項／約分／√の整理）を直しノートに1行。
- (1)〜(12) は右の☐でチェック。3回連続で満点の型は、その型だけ飛ばしてOK。
:::''', '']
for s, probs in enumerate(sets):
    out.append('## C%d　大問1計算ドリル%d' % (s + 1, s + 1))
    out.append('')
    out.append(':::q 次の各問いに答えなさい。【(1)〜(10) 各4点、(11)(12) 各3点】')
    for p in probs:
        out.append('(%d) %s [[check]]' % (p['no'], p['q']))
        out.append('')
    out.append(':::')
    out.append(':::a 解答')
    out.append('　'.join('(%d) %s' % (p['no'], p['a']) for p in probs))
    out.append('')
    out.append('**得点**（　／46）　**ミスの型**：☐符号　☐移項　☐約分・通分　☐√の整理　☐因数分解の組み合わせ　☐計算の順序')
    out.append(':::')
    out.append('')
    if s % 2 == 1:
        out.append('[[pb]]')
        out.append('')

os.makedirs(ED.src_dir(EDITION, 'math'), exist_ok=True)
open(ED.src_dir(EDITION, 'math', '20_calc.md'), 'w', encoding='utf-8').write('\n'.join(out))
json.dump(sets, open(ED.data_dir(EDITION, 'math_calc.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok')
