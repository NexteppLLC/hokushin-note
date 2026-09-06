# -*- coding: utf-8 -*-
"""Export the Markdown sources as structured JSON (for app conversion).

usage: python3 build/export_json.py            -> data/export/<subject>.json + data/export/index.json

Output schema (per subject):
{
  "subject": "science", "title": "...", "ruby": true,
  "sections": [                       # one per heading (#, ##, ###), in document order
    {"level": 2, "code": "R13", "title": "電流の性質", "heading": "R13　電流の性質",
     "path": ["5 中2 物理", "R13　電流の性質"],
     "blocks": [
        {"type": "point", "title": "要点", "md": "..."},          # any :::type block (raw markdown body)
        {"type": "text", "md": "..."},                               # paragraphs outside blocks
        {"type": "exercise", "title": "一問一答", "question_md": "...", "answer_md": "...",
         "items": [{"no": 1, "q": "...", "a": "..."}, ...]}          # a :::q block followed by :::a, paired
     ]}
  ]
}
Inline markup kept as-is in "md" strings: $...$ (mini-LaTeX), {漢字|よみ} (explicit ruby), **bold**,
==mark==, __underline__, [[svg:name]] (figure in src/<subject>/figs/name.svg), [[pb]] (page break).
"""
import os, re, json, glob, sys
sys.path.insert(0, os.path.dirname(__file__))
import editions as ED

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBJECTS = ['plan', 'japanese', 'math', 'english', 'science', 'social']

HEAD_RE = re.compile(r'^(#{1,3})\s+(.*?)\s*(\{[^}]*\})?\s*$')
BLK_RE = re.compile(r'^:::(\w+)(?:\s+(.*))?$')
CODE_RE = re.compile(r'^([A-Z]{1,3}\d{0,2}[a-zA-Z]?(?:-\d+)?|[0-9]{1,2}(?:-[0-9]{1,2})?|Day\s?\d+)\s*[　 ]\s*(.*)$')


def read_source(subject, ed=None):
    ed = ed or ED.latest()
    sdir = ED.src_dir(ed, subject)
    files = sorted(f for f in glob.glob(os.path.join(sdir, '*.md')) if '.inc.' not in os.path.basename(f))

    def include(m):
        name = m.group(1)
        for cand in (os.path.join(sdir, name), ED.src_dir(ed, name), os.path.join(ROOT, 'src', name)):
            if os.path.exists(cand):
                return open(cand, encoding='utf-8').read()
        raise FileNotFoundError(name)
    parts = []
    for f in files:
        txt = open(f, encoding='utf-8').read()
        txt = re.sub(r'\[\[include:([^\]]+)\]\]', include, txt)
        parts.append('<!-- file: %s -->\n%s' % (os.path.basename(f), txt))
    return '\n'.join(parts)


def split_item_block(md):
    """Split a body like '1. foo　2. bar\n3. baz' or '(1) foo　(2) bar' into numbered items (best effort).
    Keep the shared material before the first item separately. The separator order
    is unchanged so existing item numbers and persistent progress keys stay stable."""
    patterns = [
        (r'(\d{1,2})\\?\.\s', lambda lab: int(lab)),                      # 1. / 1\. (escaped)
        (r'(問\s?\d{1,2}|\(\d{1,2}\)|（\d{1,2}）)(?=[　 （(]|$)', lambda lab: int(re.sub(r'\D', '', lab))),  # 問1 / (1) / （1）
    ]
    for pat, tonum in patterns:
        for sep in (r'^', r'(?:^|(?<=　))', r'(?:^|(?<=[　 ]))'):
            s = re.sub(sep + pat, lambda m: '\n@@%s@@ ' % m.group(1), md, flags=re.M)
            items, prefix = [], []
            for chunk in s.split('\n'):
                m = re.match(r'^@@(.+?)@@ (.*)$', chunk.strip())
                if m:
                    items.append({'no': tonum(m.group(1)), 'label': m.group(1), 'text': m.group(2).strip()})
                elif items and chunk.strip():
                    items[-1]['text'] += '\n' + chunk.strip()
                elif not items:
                    prefix.append(chunk)
            nos = [it['no'] for it in items]
            if len(items) >= 2 and nos == list(range(nos[0], nos[0] + len(nos))):
                return {'context_md': '\n'.join(prefix).strip(), 'items': items}
    return None


def split_items(md):
    """Backward-compatible item-only API; use split_item_block for question bodies."""
    block = split_item_block(md)
    return block['items'] if block else None


def pair_items(q_md, a_md):
    qi, ai = split_items(q_md), split_items(a_md)
    if not qi or not ai:
        return None
    amap = {it['no']: it['text'] for it in ai}
    out = []
    for it in qi:
        out.append({'no': it['no'], 'label': it['label'], 'q': it['text'], 'a': amap.get(it['no'])})
    return out


def parse(subject, ed=None):
    ed = ed or ED.latest()
    cfg = json.load(open(ED.src_dir(ed, subject, 'config.json'), encoding='utf-8'))
    text = read_source(subject, ed)
    sections = []
    path = {1: None, 2: None, 3: None}
    cur = None
    cur_file = None
    blk = None       # current open block dict
    text_buf = []    # paragraphs outside blocks

    def new_section(level, heading, attrs):
        nonlocal cur
        code, title = None, heading
        m = CODE_RE.match(heading)
        if m:
            code, title = m.group(1).replace(' ', ''), m.group(2).strip()
        path[level] = heading
        for l in range(level + 1, 4):
            path[l] = None
        cur = {'level': level, 'code': code, 'title': title, 'heading': heading,
               'path': [path[l] for l in range(1, level + 1) if path[l]],
               'file': cur_file, 'notoc': bool(attrs and 'notoc' in attrs), 'blocks': []}
        sections.append(cur)

    def flush_text():
        nonlocal text_buf
        body = '\n'.join(text_buf).strip()
        body = re.sub(r'\n{3,}', '\n\n', body)
        if body and body != '[[pb]]' and cur is not None:
            cur['blocks'].append({'type': 'text', 'md': body})
        text_buf = []

    new_section(1, '（冒頭）', None)
    for line in text.split('\n'):
        mf = re.match(r'^<!-- file: (.*?) -->$', line)
        if mf:
            cur_file = mf.group(1)
            continue
        if blk is None:
            mh = HEAD_RE.match(line)
            if mh:
                flush_text()
                new_section(len(mh.group(1)), mh.group(2).strip(), mh.group(3))
                continue
            mb = BLK_RE.match(line)
            if mb:
                flush_text()
                blk = {'type': mb.group(1), 'title': (mb.group(2) or '').strip(), 'lines': [], 'depth': 1}
                continue
            if line.strip() == '[[pb]]':
                continue
            text_buf.append(line)
        else:
            if BLK_RE.match(line):
                blk['depth'] += 1
                blk['lines'].append(line)
                continue
            if line.strip() == ':::':
                blk['depth'] -= 1
                if blk['depth'] == 0:
                    body = '\n'.join(blk['lines']).strip()
                    cur['blocks'].append({'type': blk['type'], 'title': blk['title'], 'md': body})
                    blk = None
                else:
                    blk['lines'].append(line)
                continue
            blk['lines'].append(line)
    flush_text()
    if blk is not None:
        raise ValueError('unclosed block in %s' % subject)

    # pair q -> a
    for sec in sections:
        out = []
        blocks = sec['blocks']
        i = 0
        while i < len(blocks):
            b = blocks[i]
            if b['type'] == 'q':
                j = i
                while j < len(blocks) and blocks[j]['type'] == 'q':
                    j += 1
                if j < len(blocks) and blocks[j]['type'] == 'a':
                    qs = blocks[i:j]
                    a = blocks[j]
                    ex = {'type': 'exercise', 'title': qs[0]['title'],
                          'question_md': '\n\n'.join((q['title'] + '\n' if q['title'] else '') + q['md'] for q in qs) if len(qs) > 1 else qs[0]['md'],
                          'answer_title': a['title'], 'answer_md': a['md']}
                    if len(qs) > 1:
                        ex['question_parts'] = [{'title': q['title'], 'md': q['md']} for q in qs]
                    else:
                        items = pair_items(qs[0]['md'], a['md'])
                        if items:
                            ex['items'] = items
                            ex['context_md'] = split_item_block(qs[0]['md'])['context_md']
                    out.append(ex)
                    i = j + 1
                    continue
            out.append(b)
            i += 1
        sec['blocks'] = out
    sections = [s for s in sections if s['blocks'] or s['level'] <= 2]
    return {'subject': subject, 'title': cfg.get('title', subject), 'ruby': bool(cfg.get('ruby')),
            'ruby_dicts': cfg.get('ruby_dicts', []), 'sections': sections}


def main():
    ed, _ = ED.resolve(sys.argv[1:])
    outdir = ED.data_dir(ed, 'export')
    os.makedirs(outdir, exist_ok=True)
    index = []
    for s in SUBJECTS:
        d = parse(s, ed)
        n_ex = sum(1 for sec in d['sections'] for b in sec['blocks'] if b['type'] == 'exercise')
        n_items = sum(len(b.get('items', [])) for sec in d['sections'] for b in sec['blocks'] if b['type'] == 'exercise')
        with open(os.path.join(outdir, s + '.json'), 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        index.append({'subject': s, 'title': d['title'], 'file': s + '.json', 'sections': len(d['sections']),
                      'exercises': n_ex, 'paired_items': n_items,
                      'codes': [sec['code'] for sec in d['sections'] if sec['code']]})
        print('%-9s sections=%3d exercises=%3d paired_items=%4d' % (s, len(d['sections']), n_ex, n_items))
    with open(os.path.join(outdir, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
