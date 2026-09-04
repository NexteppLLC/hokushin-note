"""Dictionary-based furigana (ruby) engine.

Dictionary file format (UTF-8, one entry per line):
    key=reading
    key=reading1|reading2      # one reading per kanji-run inside key
    #key=reading               # key applies only when preceded by a digit (e.g. #人=にん)
    ~prefixKEY=reading         # key applies only when preceded by prefix (kana); '*' in prefix = any hiragana
    ; comment lines start with ';'

key may contain trailing/inner okurigana (kana). Ruby is placed only on kanji runs
inside the key; kana in the key are emitted as-is.
Matching: at each kanji position, the longest key that matches the text is used.
Unmatched kanji runs are reported (so the dictionary can be completed).
"""
import re
from collections import defaultdict

KANJI_RE = re.compile(r'[一-鿿㐀-䶿々〆ヶ]')
KANJI_RUN_RE = re.compile(r'[一-鿿㐀-䶿々〆ヶ]+')


def is_kanji(ch):
    return bool(KANJI_RE.match(ch))


class RubyDict:
    def __init__(self):
        self.entries = {}        # key -> list of readings (per kanji run)
        self.digit_entries = {}  # key (after digit) -> readings
        self.ctx_entries = defaultdict(list)  # key -> [(prefix, readings)]
        self.maxlen = 1
        self.first_index = defaultdict(list)  # first char -> keys (sorted by len desc)
        self.digit_first_index = defaultdict(list)
        self.ctx_first_index = defaultdict(list)  # first kanji -> [(prefix, key)]

    def load(self, path):
        with open(path, encoding='utf-8') as f:
            for ln, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith(';'):
                    continue
                if '=' not in line:
                    raise ValueError('%s:%d bad line: %s' % (path, ln, line))
                key, val = line.split('=', 1)
                key = key.strip().replace('_', ' ')
                val = val.strip()
                digit = False
                prefix = None
                if key.startswith('#'):
                    digit = True
                    key = key[1:]
                elif key.startswith('~'):
                    key = key[1:]
                    m = KANJI_RE.search(key)
                    if not m or m.start() == 0:
                        raise ValueError('%s:%d context entry needs a kana prefix: %s' % (path, ln, key))
                    prefix, key = key[:m.start()], key[m.start():]
                readings = val.split('|')
                runs = KANJI_RUN_RE.findall(key)
                if len(runs) != len(readings):
                    raise ValueError('%s:%d readings count mismatch for %s (%d runs, %d readings)' % (path, ln, key, len(runs), len(readings)))
                if digit:
                    self.digit_entries[key] = readings
                elif prefix is not None:
                    self.ctx_entries[key].append((prefix, readings))
                else:
                    self.entries[key] = readings
                self.maxlen = max(self.maxlen, len(key))
        self._index()

    def add(self, key, val):
        readings = val.split('|')
        self.entries[key] = readings
        self._index()

    def _index(self):
        self.first_index = defaultdict(list)
        for k in self.entries:
            self.first_index[k[0]].append(k)
        for k in self.first_index:
            self.first_index[k].sort(key=len, reverse=True)
        self.digit_first_index = defaultdict(list)
        for k in self.digit_entries:
            self.digit_first_index[k[0]].append(k)
        for k in self.digit_first_index:
            self.digit_first_index[k].sort(key=len, reverse=True)
        self.ctx_first_index = defaultdict(list)
        for k, lst in self.ctx_entries.items():
            for prefix, readings in lst:
                self.ctx_first_index[k[0]].append((prefix, k, readings))
        for k in self.ctx_first_index:
            # explicit prefixes before wildcard ones, longer keys first
            self.ctx_first_index[k].sort(key=lambda t: ('*' in t[0], -len(t[1]), -len(t[0])))


HIRA_RE = re.compile(r'[ぁ-ゖー]')


def _prefix_match(seg, prefix):
    for a, b in zip(seg, prefix):
        if b == '*':
            if not HIRA_RE.match(a):
                return False
        elif a != b:
            return False
    return True


def _render_key(key, readings):
    """Return HTML for key with ruby on each kanji run."""
    out = []
    pos = 0
    ri = 0
    for m in KANJI_RUN_RE.finditer(key):
        if m.start() > pos:
            out.append(key[pos:m.start()])
        out.append('<ruby>%s<rt>%s</rt></ruby>' % (m.group(0), readings[ri]))
        ri += 1
        pos = m.end()
    if pos < len(key):
        out.append(key[pos:])
    return ''.join(out)


class RubyEngine:
    def __init__(self, rdict):
        self.d = rdict
        self.unmatched = defaultdict(int)
        self.unmatched_ctx = {}

    def annotate(self, text):
        """Annotate plain text (no HTML tags) with ruby."""
        out = []
        i = 0
        n = len(text)
        while i < n:
            ch = text[i]
            if not is_kanji(ch):
                out.append(ch)
                i += 1
                continue
            # kanji position: try preceding-context entries, then digit-context entries
            matched = None
            for prefix, k, readings in self.d.ctx_first_index.get(ch, []):
                L = len(prefix)
                if i >= L and text.startswith(k, i) and _prefix_match(text[i - L:i], prefix):
                    matched = (k, readings)
                    break
            if matched is None and i > 0 and (text[i - 1].isdigit() or text[i - 1] in '０１２３４５６７８９'):
                for k in self.d.digit_first_index.get(ch, []):
                    if text.startswith(k, i):
                        matched = (k, self.d.digit_entries[k])
                        break
            # a longer plain entry beats a shorter context entry (e.g. 方法 over ~の方)
            for k in self.d.first_index.get(ch, []):
                if text.startswith(k, i):
                    if matched is None or len(k) > len(matched[0]):
                        matched = (k, self.d.entries[k])
                    break
            if matched is None:
                # unmatched: take the maximal kanji run, emit without ruby, record
                m = KANJI_RUN_RE.match(text, i)
                run = m.group(0)
                # try to split the run: match longest prefix from dictionary, else report run
                # (we still try prefix matches for partial coverage)
                sub_out, consumed = self._partial(text, i, run)
                if consumed == 0:
                    self.unmatched[run] += 1
                    self.unmatched_ctx.setdefault(run, text[max(0, i - 8):i + len(run) + 8])
                    out.append(run)
                    i += len(run)
                else:
                    out.append(sub_out)
                    i += consumed
                continue
            k, readings = matched
            out.append(_render_key(k, readings))
            i += len(k)
        return ''.join(out)

    def _partial(self, text, i, run):
        """Try to match the beginning of a kanji run with a shorter key (e.g. run = 細胞分裂 -> 細胞 + 分裂)."""
        # find longest key that is a prefix of run (pure-kanji keys only) with len < len(run)
        for L in range(len(run) - 1, 0, -1):
            k = run[:L]
            if k in self.d.entries:
                rest_text = text[i + L:]
                # recursively annotate the rest of the run
                rest_run = run[L:]
                rest_html = self.annotate(rest_run)
                return _render_key(k, self.d.entries[k]) + rest_html, len(run)
        return '', 0


TAG_RE = re.compile(r'(<[^>]+>)')
SKIP_TAGS = {'ruby', 'rt', 'svg', 'style', 'script', 'code', 'pre'}


def annotate_html(html, engine):
    """Annotate text nodes of an HTML fragment; skips content inside ruby/rt/svg/style/script/code/pre
    and inside elements carrying class 'noruby' (tracked by a nesting counter)."""
    parts = TAG_RE.split(html)
    out = []
    skip_stack = []  # tag names being skipped
    noruby_depth = 0
    depth_stack = []  # (tagname, is_noruby)
    for part in parts:
        if not part:
            continue
        if part.startswith('<'):
            m = re.match(r'<\s*(/?)\s*([A-Za-z0-9]+)', part)
            if m:
                closing = m.group(1) == '/'
                tag = m.group(2).lower()
                selfclosing = part.endswith('/>') or tag in ('br', 'img', 'hr', 'input', 'meta', 'link', 'path', 'circle', 'line', 'rect', 'polygon', 'polyline', 'ellipse', 'use')
                if not closing:
                    is_noruby = bool(re.search(r'class="[^"]*\bnoruby\b', part))
                    if not selfclosing:
                        depth_stack.append((tag, is_noruby or tag in SKIP_TAGS))
                        if is_noruby or tag in SKIP_TAGS:
                            noruby_depth += 1
                else:
                    # pop until matching tag
                    while depth_stack:
                        t, nr = depth_stack.pop()
                        if nr:
                            noruby_depth -= 1
                        if t == tag:
                            break
            out.append(part)
        else:
            if noruby_depth > 0:
                out.append(part)
            else:
                out.append(engine.annotate(part))
    return ''.join(out)
