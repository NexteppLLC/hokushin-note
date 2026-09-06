# -*- coding: utf-8 -*-
"""Export the material as app content (rendered HTML per block) -> data/app/content.json

usage: python3 build/export_app.py
"""
import os, re, json, sys, html as _html
sys.path.insert(0, os.path.dirname(__file__))
from export_json import parse, ROOT, split_items, split_item_block, pair_items
import editions as ED
from mdconv import Converter
from ruby_engine import RubyDict, RubyEngine, annotate_html

SUBJECTS = [
    ('english', 'E', '英語', '英'),
    ('math', 'M', '数学', '数'),
    ('japanese', 'J', '国語', '国'),
    ('science', 'S', '理科', '理'),
    ('social', 'H', '社会', '社'),
]

CODE_TOKEN = re.compile(r'[A-Z]{1,3}\d{0,2}[a-z]?(?:-\d+)?|\d{1,2}-\d{1,2}|Day\s?\d+')


def heading_codes(heading):
    """All unit codes named in a heading: 'W1〜W8　…' -> W1..W8, 'VR1・VR2　…／VT1・VT2　…' -> all four."""
    head = re.split(r'[　]', heading)[0]
    codes = []
    # ranges like W1〜W8
    for m in re.finditer(r'([A-Z]{1,3})(\d{1,2})〜([A-Z]{1,3})?(\d{1,2})', head):
        pre, a, pre2, b = m.group(1), int(m.group(2)), m.group(3) or m.group(1), int(m.group(4))
        if pre == pre2:
            codes += ['%s%d' % (pre, i) for i in range(a, b + 1)]
    for part in re.split(r'／', heading):
        h = re.split(r'[　]', part.strip())[0]
        for tok in re.split(r'[・,、/]', h):
            tok = tok.strip()
            if CODE_TOKEN.fullmatch(tok) and tok not in codes:
                codes.append(tok)
    return codes


SUP = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹', 'n': 'ⁿ'}


def plain_math(tex):
    t = tex
    t = re.sub(r'\\frac\{([^{}]*)\}\{([^{}]*)\}', r'\1/\2', t)
    t = re.sub(r'\\sqrt\{([^{}]*)\}', r'√\1', t)
    t = re.sub(r'\^\{?([0-9n])\}?', lambda m: SUP.get(m.group(1), '^' + m.group(1)), t)
    for k, v in (('\\pm', '±'), ('\\times', '×'), ('\\div', '÷'), ('\\le', '≤'), ('\\ge', '≥'), ('\\ne', '≠'), ('\\pi', 'π'), ('\\to', '→'), ('\\cdot', '・'), ('\\angle', '∠'), ('\\triangle', '△'), ('\\parallel', '∥'), ('\\perp', '⊥'), ('\\degree', '°')):
        t = t.replace(k, v)
    t = t.replace('{', '').replace('}', '').replace('\\', '')
    return t


def plain_title(s):
    if not s:
        return s
    s = re.sub(r'\$([^$]+)\$', lambda m: plain_math(m.group(1)), s)
    s = re.sub(r'\*\*(.+?)\*\*', r'\1', s)
    s = re.sub(r'==(.+?)==', r'\1', s)
    s = re.sub(r'__(.+?)__', r'\1', s)
    s = re.sub(r'\{([^{}|]+)\|[^{}]+\}', r'\1', s)   # explicit ruby -> base text
    return s.strip()


def strip_pb(md):
    return re.sub(r'^\[\[pb\]\]\s*$', '', md, flags=re.M).strip()


class Renderer:
    def __init__(self, subject, ruby_cfg, ed):
        self.conv = Converter(figdir=ED.src_dir(ed, subject, 'figs'))
        self.eng = None
        if ruby_cfg.get('ruby'):
            rd = RubyDict()
            for dp in ruby_cfg.get('ruby_dicts', ['ruby_common.txt']):
                rd.load(ED.find_src(ed, dp))
            self.eng = RubyEngine(rd)

    def html(self, md):
        md = strip_pb(md)
        if not md:
            return ''
        h = self.conv.convert(md)
        h = re.sub(r'<div class="pb"></div>', '', h)
        if self.eng:
            h = annotate_html(h, self.eng)
        return h.strip()


TABLE_ROW = re.compile(r'^\|(.*)\|\s*$')


def table_rows(md):
    rows = []
    for line in md.split('\n'):
        m = TABLE_ROW.match(line.strip())
        if not m:
            continue
        cells = [c.strip() for c in m.group(1).split('|')]
        if all(re.fullmatch(r':?-{2,}:?', c) for c in cells if c):
            continue
        rows.append(cells)
    return rows


def vocab_items(md):
    """english V tables: | No | 単語 | 品詞 | 意味 | ☐ | No | 単語 | 品詞 | 意味 | ☐ |"""
    items = []
    for cells in table_rows(md):
        if cells and cells[0] == 'No':
            continue
        for off in (0, 5):
            if len(cells) >= off + 4 and re.fullmatch(r'\d+', cells[off] or ''):
                items.append({'n': int(cells[off]), 'word': cells[off + 1], 'pos': cells[off + 2], 'meaning': cells[off + 3]})
    return items if len(items) >= 5 else None


def kanji_items(md):
    """japanese K tables: | No | 問題 | ☐ | No | 問題 | ☐ |"""
    items = []
    for cells in table_rows(md):
        if cells and cells[0] == 'No':
            continue
        for off in (0, 3):
            if len(cells) >= off + 2 and re.fullmatch(r'\d+', cells[off] or ''):
                items.append({'n': int(cells[off]), 'q': cells[off + 1]})
    items.sort(key=lambda x: x['n'])
    return items if items else None


def kanji_answers(md):
    """'**読み**　1 とどこおる　2 したう…' / '**書き**　1 誠実 …' -> {'読み': {1: ..}, '書き': {..}}"""
    out = {}
    for line in md.split('\n'):
        m = re.match(r'^\*\*(読み|書き)\*\*\s*(.*)$', line.strip())
        if not m:
            continue
        d = {}
        for mm in re.finditer(r'(\d+)\s+([^\d　]+)', m.group(2)):
            d[int(mm.group(1))] = mm.group(2).strip()
        out[m.group(1)] = d
    return out


def mock_answer_key(sec, title):
    """Only match a mock's answer inside its source file and M-code, never by number alone."""
    unit = sec['path'][1] if len(sec['path']) > 1 else ''
    code = re.match(r'^(M\d+)\s', unit)
    number = re.match(r'^大問\s*(\d+)', title)
    if not code or not number:
        return None
    return (sec['file'], code.group(1), int(number.group(1)))


def linked_mock_questions(doc):
    """Copy, rather than move, separated mock answers. Existing unit/block indices remain intact."""
    answers = {}
    for sec in doc['sections']:
        for b in sec['blocks']:
            if b['type'] == 'a':
                k = mock_answer_key(sec, b['title'])
                if k:
                    answers.setdefault(k, []).append(b)
    linked = {}
    for sec in doc['sections']:
        key = mock_answer_key(sec, sec['heading'])
        candidates = answers.get(key, [])
        if len(candidates) != 1:
            continue
        questions = [b for b in sec['blocks'] if b['type'] == 'q']
        if len(questions) != 1:
            continue
        q, a = questions[0], candidates[0]
        ex = {'type': 'exercise', 'title': q['title'], 'question_md': q['md'],
              'answer_title': a['title'], 'answer_md': a['md']}
        items = pair_items(q['md'], a['md'])
        # Refuse item-wise grading if an answer number is missing or unmatched.
        qi, ai = split_items(q['md']), split_items(a['md'])
        if items and [i['no'] for i in qi] == [i['no'] for i in ai]:
            ex['items'] = items
            ex['context_md'] = split_item_block(q['md'])['context_md']
        linked[id(q)] = ex
    return linked


def build_subject(subject, key, name, short, ed):
    cfg = json.load(open(ED.src_dir(ed, subject, 'config.json'), encoding='utf-8'))
    R = Renderer(subject, cfg, ed)
    doc = parse(subject, ed)
    # The browser uses original unit positions for uncoded/repeated headings.
    # Append added chapters so existing notes, highlights and ink retain their keys.
    appended_files = {'44_visual_guide.md', '45_visual.md', '41_visual_guide.md',
                      '42_visual_history.md', '43_visual_geo.md'}
    doc['sections'].sort(key=lambda sec: os.path.basename(sec.get('file') or '') in appended_files)
    linked = linked_mock_questions(doc)
    units = []
    chapter = None
    cur = None

    def start_unit(sec):
        nonlocal cur
        codes = heading_codes(sec['heading'])
        code = sec['code'] or (codes[0] if codes else None)
        if code and code not in codes:
            codes.insert(0, code)
        cur = {'code': code, 'codes': codes, 'title': plain_title(sec['title'] if sec['code'] else sec['heading']),
               'heading': plain_title(sec['heading']), 'chapter': plain_title(chapter), 'content': []}
        units.append(cur)

    for sec in doc['sections']:
        if sec['level'] == 1:
            chapter = sec['heading']
            cur = None
            if sec['blocks']:
                # chapter-level content becomes its own unit (e.g. 0 この教材の使い方)
                start_unit(sec)
        elif sec['level'] == 2:
            start_unit(sec)
        else:  # level 3: fold into the current unit
            if cur is None:
                start_unit(sec)
            else:
                cur['content'].append({'t': 'h3', 'title': plain_title(sec['heading'])})
        if sec['level'] == 3 or cur is None:
            target = cur
        else:
            target = cur
        if target is None:
            continue
        for source_block in sec['blocks']:
            b = linked.get(id(source_block), source_block)
            if b['type'] == 'exercise':
                ex = {'t': 'ex', 'title': plain_title(b['title']), 'q': R.html(b['question_md']), 'atitle': plain_title(b.get('answer_title', '')), 'a': R.html(b['answer_md'])}
                if sec['level'] == 3:
                    ex['contextTitle'] = plain_title(sec['heading'])
                if b.get('context_md'):
                    ex['context'] = R.html(b['context_md'])
                # special: kanji sets (two q parts: 読み / 書き, table based)
                if subject == 'japanese' and b.get('question_parts') and any(p['title'].startswith(('読み', '書き')) for p in b['question_parts']):
                    ans = kanji_answers(b['answer_md'])
                    parts = []
                    for p in b['question_parts']:
                        kind = '読み' if p['title'].startswith('読み') else '書き'
                        its = kanji_items(p['md'])
                        if its:
                            for it in its:
                                it['a'] = ans.get(kind, {}).get(it['n'], '')
                                it['q'] = re.sub(r'__(.+?)__', r'<u>\1</u>', _html.escape(it['q']))
                            parts.append({'kind': kind, 'items': its})
                    if parts:
                        ex['kanji'] = parts
                elif b.get('items'):
                    ex['items'] = [{'n': it['no'], 'l': it.get('label') or ('%d.' % it['no']), 'q': R.html(it['q']), 'a': R.html(it['a'] or '')} for it in b['items']]
                elif b.get('question_parts'):
                    ex['parts'] = [{'title': plain_title(p['title']), 'html': R.html(p['md'])} for p in b['question_parts']]
                target['content'].append(ex)
            else:
                blk = {'t': b['type'], 'title': plain_title(b.get('title', '')), 'html': R.html(b['md'])}
                if subject == 'english' and b['type'] == 'text' and re.match(r'V\d+$', cur['code'] or ''):
                    v = vocab_items(b['md'])
                    if v:
                        blk['vocab'] = v
                if blk['html'] or blk.get('vocab'):
                    target['content'].append(blk)
    # Keep passage/data blocks in their original slots and attach them once to each
    # card. Do not concatenate the whole c.q to split items: that repeats all questions.
    for unit in units:
        shared = []
        for block in unit['content']:
            if block['t'] == 'h3':
                shared = []
            elif block['t'] in ('passage', 'dialog', 'data'):
                title = ('<div class="ex-title">' + _html.escape(block['title']) + '</div>') if block['title'] else ''
                shared.append(title + block['html'])
            elif block['t'] == 'ex' and shared:
                block['externalContext'] = '\n'.join(shared)
    # drop empty units
    units = [u for u in units if u['content']]
    return {'id': subject, 'key': key, 'name': name, 'short': short, 'title': cfg.get('title', name), 'ruby': bool(cfg.get('ruby')), 'units': units}


def build_edition(ed):
    out = {'id': ed['id'], 'name': ed['name'], 'short': ed.get('short', ed['name']), 'test_day': ed['test_day'], 'start': ed['start'], 'note': ed.get('note', ''), 'subjects': []}
    for subject, key, name, short in SUBJECTS:
        s = build_subject(subject, key, name, short, ed)
        n_ex = sum(1 for u in s['units'] for c in u['content'] if c['t'] == 'ex')
        n_items = sum(len(c.get('items', [])) + sum(len(p['items']) for p in c.get('kanji', [])) for u in s['units'] for c in u['content'] if c['t'] == 'ex')
        n_vocab = sum(len(c.get('vocab', [])) for u in s['units'] for c in u['content'] if c['t'] != 'ex')
        print('%s %-9s units=%3d exercises=%3d items=%4d vocab=%d' % (ed['id'], subject, len(s['units']), n_ex, n_items, n_vocab))
        out['subjects'].append(s)
    plan = json.load(open(ED.data_dir(ed, 'plan.json'), encoding='utf-8'))
    out['plan'] = plan
    # coverage of plan codes
    for s in out['subjects']:
        codes = set()
        for u in s['units']:
            codes.update(u['codes'])
        pc = set()
        for day in plan['days']:
            for t in day['tasks'].get(s['key'], []):
                pc.add(t['code'])
        missing = sorted(pc - codes)
        if missing:
            print('  ', s['id'], 'plan codes without unit (review activities):', missing)
    return out


def main():
    eds = [e for e in ED.load() if e.get('app', True)]
    out = {'generated': __import__('datetime').date.today().isoformat(), 'editions': [build_edition(e) for e in eds]}
    os.makedirs(os.path.join(ROOT, 'data', 'app'), exist_ok=True)
    p = os.path.join(ROOT, 'data', 'app', 'content.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print('wrote', p, os.path.getsize(p) // 1024, 'KB', '| editions:', ', '.join(e['id'] for e in eds))


if __name__ == '__main__':
    main()
