"""Build a subject PDF.

usage: python3 build/build.py [<edition>] <subject> [--png] [--pages 1-3] [--nopdf]
Reads src/<edition>/<subject>/config.json and *.md (sorted), converts, applies ruby if configured,
renders out/<edition>/<subject>.html and .pdf (two-pass for TOC page numbers).
<edition> defaults to the last entry of editions.json.
"""
import sys, os, re, json, glob, subprocess, asyncio, html as _html
sys.path.insert(0, os.path.dirname(__file__))
from mdconv import Converter
from ruby_engine import RubyDict, RubyEngine, annotate_html
import editions as ED

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def slugify_headings(html):
    """Add ids to h1/h2 and collect toc entries."""
    toc = []
    counter = [0]

    def rep(m):
        level = m.group(1)
        attrs = m.group(2) or ''
        inner = m.group(3)
        counter[0] += 1
        hid = 'h%d' % counter[0]
        text = re.sub(r'<[^>]+>', '', inner)
        text = re.sub(r'\s+', ' ', text).strip()
        if 'notoc' in attrs:
            return m.group(0)
        toc.append((int(level), hid, text))
        return '<h%s id="%s"%s>%s</h%s>' % (level, hid, attrs, inner, level)
    html = re.sub(r'<h([12])([^>]*)>(.*?)</h\1>', rep, html, flags=re.S)
    return html, toc


def make_toc_html(toc, pages=None):
    items = []
    for level, hid, text in toc:
        pn = ''
        if pages and hid in pages:
            pn = str(pages[hid])
        items.append('<li class="l%d"><span class="t">%s</span><span class="pn">%s</span></li>' % (level, _html.escape(text), pn))
    return '<div class="toc"><h1 class="first" notoc>もくじ</h1><ul>%s</ul></div>' % ''.join(items)


def wrap(body, cfg, css):
    cls = 'ruby' if cfg.get('ruby') else ''
    return ('<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><title>%s</title>'
            '<style>%s</style></head><body class="%s">%s</body></html>') % (cfg.get('title', ''), css, cls, body)


async def render_pdf(html_path, pdf_path, cfg):
    from playwright.async_api import async_playwright
    header = cfg.get('header', '')
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        await pg.goto('file://' + html_path)
        await pg.wait_for_timeout(300)
        await pg.pdf(path=pdf_path, format='A4',
                     margin={'top': '16mm', 'bottom': '16mm', 'left': '15mm', 'right': '15mm'},
                     display_header_footer=True, print_background=True, prefer_css_page_size=True,
                     header_template='<div style="font-size:7.5pt;width:100%%;padding:0 15mm;color:#555;font-family:sans-serif;display:flex;justify-content:space-between"><span>%s</span><span>%s</span></div>' % (header, cfg.get('header_right', '')),
                     footer_template='<div style="font-size:8pt;width:100%;text-align:center;color:#555;font-family:sans-serif">— <span class="pageNumber"></span> / <span class="totalPages"></span> —</div>')
        await b.close()


def page_map(pdf_path, toc):
    """Find the page number of each heading text via pdftotext."""
    out = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], capture_output=True, text=True).stdout
    pages = out.split('\f')
    result = {}
    norm = lambda s: re.sub(r'\s+', '', s)
    npages = [norm(p) for p in pages]
    # skip cover + TOC pages: the TOC pages contain the last heading text within the first few pages
    start = 0
    if toc:
        last_key = norm(toc[-1][2])
        for i in range(min(6, len(npages))):
            if 'もくじ' in npages[i] or (last_key and last_key in npages[i] and i < 4):
                start = i + 1
    for level, hid, text in toc:
        key = norm(text)
        found = None
        for i in range(start, len(npages)):
            if key and key in npages[i]:
                found = i + 1
                break
        if found:
            result[hid] = found
            start = found - 1
    return result


def build(subject, png=False, pages=None, pdf=True, ed=None):
    ed = ed or ED.latest()
    sdir = ED.src_dir(ed, subject)
    odir = ED.out_dir(ed)
    cfg = json.load(open(os.path.join(sdir, 'config.json'), encoding='utf-8'))
    css = open(os.path.join(ROOT, 'build', 'style.css'), encoding='utf-8').read()
    extra_css = cfg.get('css', '')
    if os.path.exists(os.path.join(sdir, 'extra.css')):
        extra_css += open(os.path.join(sdir, 'extra.css'), encoding='utf-8').read()
    css += '\n' + extra_css
    files = sorted(f for f in glob.glob(os.path.join(sdir, '*.md')) if '.inc.' not in os.path.basename(f))
    conv = Converter(figdir=os.path.join(sdir, 'figs'))
    parts = []

    def include(m):
        name = m.group(1)
        for cand in (os.path.join(sdir, name), ED.src_dir(ed, name), os.path.join(ROOT, 'src', name)):
            if os.path.exists(cand):
                return open(cand, encoding='utf-8').read()
        raise FileNotFoundError(name)
    for f in files:
        txt = open(f, encoding='utf-8').read()
        txt = re.sub(r'\[\[include:([^\]]+)\]\]', include, txt)
        parts.append(conv.convert(txt))
    body = '\n'.join(parts)
    body, toc = slugify_headings(body)
    if cfg.get('ruby'):
        rd = RubyDict()
        for dp in cfg.get('ruby_dicts', ['ruby_common.txt']):
            rd.load(ED.find_src(ed, dp))
        eng = RubyEngine(rd)
        body = annotate_html(body, eng)
        rep_path = os.path.join(odir, subject + '_unmatched.txt')
        with open(rep_path, 'w', encoding='utf-8') as f:
            for run, cnt in sorted(eng.unmatched.items(), key=lambda x: -x[1]):
                f.write('%s\t%d\t%s\n' % (run, cnt, eng.unmatched_ctx.get(run, '')))
        print('unmatched kanji runs: %d (see %s)' % (len(eng.unmatched), rep_path))
    cover = cfg.get('cover_html', '')
    if os.path.exists(os.path.join(sdir, 'cover.html')):
        cover = open(os.path.join(sdir, 'cover.html'), encoding='utf-8').read()
        if cfg.get('ruby'):
            cover = annotate_html(cover, eng)

    def toc_html(pm=None):
        h = make_toc_html(toc, pm)
        if cfg.get('ruby'):
            h = annotate_html(h, eng)
        return h
    if cfg.get('ruby'):
        toc_html()  # collect unmatched runs from the TOC as well
        with open(rep_path, 'w', encoding='utf-8') as f:
            for run, cnt in sorted(eng.unmatched.items(), key=lambda x: -x[1]):
                f.write('%s\t%d\t%s\n' % (run, cnt, eng.unmatched_ctx.get(run, '')))
        print('unmatched kanji runs (incl. cover/toc): %d' % len(eng.unmatched))
    html_path = os.path.join(odir, subject + '.html')
    pdf_path = os.path.join(odir, subject + '.pdf')
    # pass 1
    full = wrap(cover + toc_html() + body, cfg, css)
    open(html_path, 'w', encoding='utf-8').write(full)
    if not pdf:
        return
    asyncio.run(render_pdf(html_path, pdf_path, cfg))
    pm = page_map(pdf_path, toc)
    full = wrap(cover + toc_html(pm) + body, cfg, css)
    open(html_path, 'w', encoding='utf-8').write(full)
    asyncio.run(render_pdf(html_path, pdf_path, cfg))
    info = subprocess.run(['pdfinfo', pdf_path], capture_output=True, text=True).stdout
    m = re.search(r'Pages:\s+(\d+)', info)
    print('built %s: %s pages' % (pdf_path, m.group(1) if m else '?'))
    if png:
        pdir = os.path.join(odir, 'png_' + subject)
        os.makedirs(pdir, exist_ok=True)
        for f in glob.glob(os.path.join(pdir, '*.png')):
            os.remove(f)
        args = ['pdftoppm', '-png', '-r', '70']
        if pages:
            a, b = pages.split('-')
            args += ['-f', a, '-l', b]
        subprocess.run(args + [pdf_path, os.path.join(pdir, 'p')])
        print('png pages in', pdir)


if __name__ == '__main__':
    ed, args = ED.resolve(sys.argv[1:])
    subject = args[0]
    png = '--png' in args
    pages = None
    if '--pages' in args:
        pages = args[args.index('--pages') + 1]
    build(subject, png=png, pages=pages, pdf='--nopdf' not in args, ed=ed)
