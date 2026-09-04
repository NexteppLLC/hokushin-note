"""Custom markdown -> HTML converter for the study materials."""
import re
import os
import html as _html
import markdown
from mathconv import convert as math_convert

PH_RE = re.compile(r'⟦(\d+)⟧')


class Converter:
    def __init__(self, figdir=None):
        self.figdir = figdir or '.'
        self.ph = []

    def _stash(self, html):
        self.ph.append(html)
        return '⟦%d⟧' % (len(self.ph) - 1)

    # ---------- inline pre-processing ----------
    def _inline(self, text):
        # block-level directives on their own line -> raw html blocks
        def blockdir(m):
            body = m.group(1)
            if body == 'pb':
                return '\n<div class="pb"></div>\n'
            if body.startswith('lines'):
                n = int(body.split(':', 1)[1]) if ':' in body else 2
                return '\n<div class="lines">%s</div>\n' % ''.join('<div class="ln"></div>' for _ in range(n))
            if body.startswith('space'):
                h = body.split(':', 1)[1] if ':' in body else '1'
                return '\n<div style="height:%sem"></div>\n' % h
            if body.startswith('genko'):
                spec = body.split(':', 1)[1] if ':' in body else '12x15'
                rows, cols = [int(x) for x in spec.lower().split('x')]
                cells = ''.join('<tr>%s</tr>' % ''.join('<td></td>' for _ in range(cols)) for _ in range(rows))
                return '\n<table class="genko">%s</table>\n' % cells
            if body.startswith('svg:'):
                name = body[4:]
                p = os.path.join(self.figdir, name if name.endswith('.svg') else name + '.svg')
                svg = re.sub(r'<\?xml[^>]*\?>', '', open(p, encoding='utf-8').read())
                return '\n' + self._stash('<div class="fig">%s</div>' % svg) + '\n'
            return m.group(0)
        text = re.sub(r'^\[\[([^\[\]]+)\]\]\s*$', blockdir, text, flags=re.M)
        # display math $$...$$
        text = re.sub(r'\$\$(.+?)\$\$', lambda m: self._stash('<div class="math dm">%s</div>' % math_convert(m.group(1))), text, flags=re.S)
        # inline math $...$  (not preceded by backslash)
        text = re.sub(r'(?<!\\)\$(.+?)(?<!\\)\$', lambda m: self._stash('<span class="math">%s</span>' % math_convert(m.group(1))), text)
        # explicit ruby {base|reading}
        text = re.sub(r'\{([^{}|]+)\|([^{}|]+)\}', lambda m: self._stash('<ruby>%s<rt>%s</rt></ruby>' % (m.group(1), m.group(2))), text)
        # inline directives
        def directive(m):
            body = m.group(1)
            if body == 'pb':
                return self._stash('<div class="pb"></div>')
            if body.startswith('svg:'):
                name = body[4:]
                p = os.path.join(self.figdir, name if name.endswith('.svg') else name + '.svg')
                with open(p, encoding='utf-8') as f:
                    svg = f.read()
                svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
                return self._stash('<div class="fig">%s</div>' % svg)
            if body.startswith('svgi:'):  # inline (no wrapper div, floats right)
                name = body[5:]
                p = os.path.join(self.figdir, name if name.endswith('.svg') else name + '.svg')
                with open(p, encoding='utf-8') as f:
                    svg = f.read()
                svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
                return self._stash('<span class="figr">%s</span>' % svg)
            if body.startswith('img:'):
                spec = body[4:]
                w = ''
                if '|' in spec:
                    spec, w = spec.split('|', 1)
                    w = ' style="width:%s"' % w
                p = os.path.join(self.figdir, spec)
                import base64, mimetypes
                mt = mimetypes.guess_type(p)[0] or 'image/png'
                with open(p, 'rb') as f:
                    data = base64.b64encode(f.read()).decode()
                return self._stash('<div class="fig"><img src="data:%s;base64,%s"%s></div>' % (mt, data, w))
            if body.startswith('blank'):
                w = '4'
                if ':' in body:
                    w = body.split(':', 1)[1]
                return self._stash('<span class="blank" style="min-width:%sem"></span>' % w)
            if body.startswith('lines'):
                n = 2
                if ':' in body:
                    n = int(body.split(':', 1)[1])
                return self._stash('<div class="lines">%s</div>' % ''.join('<div class="ln"></div>' for _ in range(n)))
            if body.startswith('space'):
                h = '1'
                if ':' in body:
                    h = body.split(':', 1)[1]
                return self._stash('<div style="height:%sem"></div>' % h)
            if body.startswith('genko'):
                # genko:rows x cols  e.g. genko:12x15
                spec = body.split(':', 1)[1] if ':' in body else '12x15'
                rows, cols = [int(x) for x in spec.lower().split('x')]
                cells = ''.join('<tr>%s</tr>' % ''.join('<td></td>' for _ in range(cols)) for _ in range(rows))
                return self._stash('<table class="genko">%s</table>' % cells)
            if body.startswith('ans'):
                # answer line
                lab = '答え'
                if ':' in body:
                    lab = body.split(':', 1)[1]
                return self._stash('<span class="ansline">%s：<span class="blank" style="min-width:6em"></span></span>' % lab)
            if body.startswith('box:'):
                # small inline box with text
                return self._stash('<span class="ibox">%s</span>' % _html.escape(body[4:]))
            if body.startswith('check'):
                return self._stash('<span class="chk">☐</span>')
            if body.startswith('score'):
                return self._stash('<span class="score">%s</span>' % _html.escape(body.split(':', 1)[1] if ':' in body else ''))
            return m.group(0)
        text = re.sub(r'\[\[([^\[\]]+)\]\]', directive, text)
        # highlight ==text==
        text = re.sub(r'==(.+?)==', lambda m: self._stash('<mark>%s</mark>' % m.group(1)), text)
        # underline __text__ -> <u> (we don't use markdown's bold-underscore)
        text = re.sub(r'(?<![A-Za-z0-9_])__(.+?)__(?![A-Za-z0-9_])', lambda m: self._stash('<u>%s</u>' % m.group(1)), text)
        # kanji-writing target in katakana: 〔カタカナ〕 -> styled
        return text

    # ---------- block pre-processing ----------
    def _blocks(self, text):
        lines = text.split('\n')
        out = []
        stack = []
        prev_num = None  # leading number of the previous non-blank line (for non-sequential numbered lines)
        for line in lines:
            # a numbered line that does not continue the previous item (e.g. "1. a 2. b" then "9. c")
            # must not become a new list item (markdown would renumber it) -> escape the period
            mn = re.match(r'^(\d+)\. ', line)
            if mn:
                num = int(mn.group(1))
                if prev_num is not None and num != prev_num + 1:
                    line = re.sub(r'^(\d+)\.', r'\1\\.', line)
                prev_num = num
            elif line.strip():
                prev_num = None
            else:
                prev_num = None
            m = re.match(r'^:::(\w+)(?:\s+(.*))?$', line)
            if m:
                name = m.group(1)
                title = (m.group(2) or '').strip()
                stack.append(name)
                cls = 'blk ' + name
                if name == 'cols':
                    out.append('')
                    out.append('<div class="cols" markdown="1">')
                    out.append('')
                    continue
                if name in ('q', 'a', 'box', 'point', 'note', 'warn', 'ex', 'memo', 'plan', 'tip', 'summary', 'goal', 'step', 'script', 'passage', 'dialog', 'rule', 'check', 'data', 'sub'):
                    out.append('')
                    if title:
                        out.append('<div class="%s" markdown="1">' % cls)
                        out.append('<div class="bt">%s</div>' % title)
                        out.append('')
                    else:
                        out.append('<div class="%s" markdown="1">' % cls)
                        out.append('')
                    continue
                # generic
                out.append('')
                out.append('<div class="%s" markdown="1">' % cls)
                if title:
                    out.append('<div class="bt">%s</div>' % title)
                out.append('')
                continue
            if line.strip() == ':::':
                if stack:
                    stack.pop()
                out.append('')
                out.append('</div>')
                out.append('')
                continue
            # a table / list must be preceded by a blank line (python-markdown requirement)
            if line.startswith('|') and out and out[-1].strip() and not out[-1].startswith('|'):
                out.append('')
            if re.match(r'^(- |\d+\. )', line) and out and out[-1].strip() and not re.match(r'^(\s*- |\s*\d+\\?\. |<)', out[-1]):
                out.append('')
            out.append(line)
        if stack:
            raise ValueError('unclosed blocks: %s' % stack)
        return '\n'.join(out)

    def convert(self, text):
        self.ph = []
        text = self._inline(text)
        text = self._blocks(text)
        md = markdown.Markdown(extensions=['tables', 'md_in_html', 'sane_lists', 'def_list', 'attr_list', 'nl2br'],
                               output_format='html5')
        html = md.convert(text)
        # restore placeholders (may be nested inside stashed html, so loop)
        for _ in range(5):
            if not PH_RE.search(html):
                break
            html = PH_RE.sub(lambda m: self.ph[int(m.group(1))], html)
        html = fix_tables(html)
        return html


def fix_tables(html):
    """Add nowrap to short cells (<=6 chars) so that short labels do not wrap."""
    def fixcell(m):
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        plain = re.sub(r'<[^>]+>', '', inner).strip()
        if len(plain) <= 6 and 'class=' not in attrs:
            attrs = attrs + ' class="nw"'
        return '<%s%s>%s</%s>' % (tag, attrs, inner, tag)
    def fix(m):
        t = m.group(0)
        return re.sub(r'<(t[dh])([^>]*)>(.*?)</\1>', fixcell, t, flags=re.S)
    return re.sub(r'<table>.*?</table>', fix, html, flags=re.S)
