"""Mini LaTeX-like math -> HTML converter for junior-high math.

Supported inside $...$:
  \frac{a}{b}   \sqrt{x}   x^{2} / x^2   a_{1} / a_1
  \pm \times \div \le \ge \ne \cdots \angle \triangle \parallel \perp \deg \cdot
  \le -> ≦, \ge -> ≧ (Japanese textbook style)
  letters are italic; digits/operators upright.
  \text{...} -> upright text
  \vec{AB} not needed.
"""
import re
import html as _html

SYMBOLS = {
    r'\pm': '±', r'\times': '×', r'\div': '÷', r'\le': '≦', r'\ge': '≧',
    r'\ne': '≠', r'\cdots': '…', r'\angle': '∠', r'\triangle': '△',
    r'\parallel': '∥', r'\perp': '⊥', r'\deg': '°', r'\cdot': '・',
    r'\pi': '<i>π</i>', r'\equiv': '≡', r'\therefore': '∴', r'\because': '∵',
    r'\ldots': '…', r'\to': '→', r'\Rightarrow': '⇒', r'\leftrightarrow': '⇔',
    r'\quad': '&emsp;', r'\qquad': '&emsp;&emsp;', r'\fallingdotseq': '≒', r'\approx': '≒', r'\propto': '∝', r'\,': '&thinsp;', r'\;': '&ensp;', r'\!': '',
    r'\lt': '<', r'\gt': '>', r'\sim': '∽', r'\cong': '≡', r'\infty': '∞',
    r'\%': '%', r'\{': '{', r'\}': '}', r'\backslash': '\\',
}


def ce_convert(s):
    """chemistry formula: digits after a letter or ')' become subscripts; leading digits are coefficients;
    '->' becomes an arrow; letters upright."""
    out = []
    i = 0
    at_start = True
    n = len(s)
    while i < n:
        c = s[i]
        if s.startswith('->', i):
            out.append(' → ')
            i += 2
            at_start = True
            continue
        if c == ' ':
            out.append(' ')
            i += 1
            at_start = True
            continue
        if c == '+':
            out.append(' + ')
            i += 1
            at_start = True
            continue
        if c.isdigit():
            m = re.match(r'\d+', s[i:])
            d = m.group(0)
            i += len(d)
            if at_start:
                out.append(d)
            else:
                out.append('<sub>%s</sub>' % d)
            continue
        at_start = False
        out.append(_html.escape(c))
        i += 1
    return '<span class="ce">%s</span>' % re.sub(' +', ' ', ''.join(out)).strip()


_ITALIC_RE = re.compile(r'[A-Za-z]')


def _find_brace(s, i):
    """s[i] == '{'; return index of matching '}'"""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == '{':
            depth += 1
        elif s[j] == '}':
            depth -= 1
            if depth == 0:
                return j
    raise ValueError('unbalanced braces in math: ' + s)


def _arg(s, i):
    """parse one argument starting at s[i]: either {…} or single token. returns (content, next_index)"""
    if i < len(s) and s[i] == '{':
        j = _find_brace(s, i)
        return s[i + 1:j], j + 1
    # single char / command
    if i < len(s) and s[i] == '\\':
        m = re.match(r'\\[A-Za-z]+', s[i:])
        if m:
            return m.group(0), i + len(m.group(0))
    return s[i:i + 1], i + 1


def convert(s, upright=False):
    out = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == '\\':
            m = re.match(r'\\([A-Za-z]+|[,;!%{}\\])', s[i:])
            if not m:
                out.append('\\')
                i += 1
                continue
            cmd = m.group(0)
            i += len(cmd)
            if cmd == r'\frac':
                a, i = _arg(s, i)
                b, i = _arg(s, i)
                out.append('<span class="frac"><span class="n">%s</span><span class="d">%s</span></span>' % (convert(a), convert(b)))
            elif cmd == r'\dfrac':
                a, i = _arg(s, i)
                b, i = _arg(s, i)
                out.append('<span class="frac big"><span class="n">%s</span><span class="d">%s</span></span>' % (convert(a), convert(b)))
            elif cmd == r'\sqrt':
                a, i = _arg(s, i)
                out.append('<span class="sqrt"><span class="rs">√</span><span class="rad">%s</span></span>' % convert(a))
            elif cmd == r'\text' or cmd == r'\mathrm' or cmd == r'\rm':
                a, i = _arg(s, i)
                out.append('<span class="up">%s</span>' % _html.escape(a))
            elif cmd == r'\ce':
                a, i = _arg(s, i)
                out.append(ce_convert(a))
            elif cmd == r'\overline':
                a, i = _arg(s, i)
                out.append('<span class="ovl">%s</span>' % convert(a))
            elif cmd == r'\vec':
                a, i = _arg(s, i)
                out.append('<span class="vec">%s</span>' % convert(a))
            elif cmd == r'\bar':
                a, i = _arg(s, i)
                out.append('<span class="ovl">%s</span>' % convert(a))
            elif cmd == r'\boxed':
                a, i = _arg(s, i)
                out.append('<span class="boxed">%s</span>' % convert(a))
            elif cmd == r'\ul':
                a, i = _arg(s, i)
                out.append('<u>%s</u>' % convert(a))
            elif cmd in SYMBOLS:
                out.append(SYMBOLS[cmd])
            else:
                out.append(_html.escape(cmd))
        elif c == '^':
            a, i2 = _arg(s, i + 1)
            i = i2
            out.append('<sup>%s</sup>' % convert(a))
        elif c == '_':
            a, i2 = _arg(s, i + 1)
            i = i2
            out.append('<sub>%s</sub>' % convert(a))
        elif c == '{':
            j = _find_brace(s, i)
            out.append(convert(s[i + 1:j]))
            i = j + 1
        elif c == '}':
            i += 1
        elif c == '[' and ']' in s[i:]:
            j = s.index(']', i)
            out.append('[' + convert(s[i + 1:j], True) + ']')
            i = j + 1
        elif _ITALIC_RE.match(c):
            # consecutive letters -> italic each (keep as one run)
            m = re.match(r'[A-Za-z]+', s[i:])
            run = m.group(0)
            i += len(run)
            out.append(('<span class="up">%s</span>' if upright else '<i>%s</i>') % run)
        elif c == '-':
            out.append('−')
            i += 1
        elif c == '*':
            out.append('×')
            i += 1
        elif c == "'":
            out.append('′')
            i += 1
        elif c == '<':
            out.append('&lt;')
            i += 1
        elif c == '>':
            out.append('&gt;')
            i += 1
        elif c == '&':
            out.append('&amp;')
            i += 1
        elif c == ' ':
            out.append(' ')
            i += 1
        else:
            out.append(c)
            i += 1
    return ''.join(out)


def math_html(s, display=False):
    cls = 'math dm' if display else 'math'
    return '<span class="%s">%s</span>' % (cls, convert(s))


if __name__ == '__main__':
    import sys
    print(convert(sys.argv[1]))
