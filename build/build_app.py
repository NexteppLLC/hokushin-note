# -*- coding: utf-8 -*-
"""Assemble the single-file learning app.
usage: python3 build/build_app.py  -> out/app_artifact.html (body-only, for the Artifact tool)
                                     out/app_standalone.html (full document)
"""
import os, re, glob, json, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, 'app')
TITLE = '北辰10月 学習ノート'

def read(p):
    return open(p, encoding='utf-8').read()

def main():
    css = read(os.path.join(APP, 'app.css'))
    shell = read(os.path.join(APP, 'shell.html'))
    js = '\n'.join(read(f) for f in sorted(glob.glob(os.path.join(APP, 'js', '*.js'))))
    data = read(os.path.join(ROOT, 'data', 'app', 'content.json'))
    assert '</script' not in data.lower() and '<!--' not in data, 'unsafe sequence in data'
    js_safe = js.replace('</script', '<\\/script')
    stamp = datetime.date.today().isoformat()
    head_common = ('<title>%s</title>\n' % TITLE +
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@500;700&display=swap">\n' +
        '<style>\n%s\n</style>\n' % css)
    body = shell + '\n<script type="application/json" id="content-data">' + data + '</script>\n<script>\n/* build %s */\n%s\n</script>\n' % (stamp, js_safe)
    os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
    with open(os.path.join(ROOT, 'out', 'app_artifact.html'), 'w', encoding='utf-8') as f:
        f.write(head_common + body)
    head_full = ('<!doctype html>\n<html lang="ja">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="apple-mobile-web-app-capable" content="yes">\n<meta name="mobile-web-app-capable" content="yes">\n<meta name="apple-mobile-web-app-status-bar-style" content="default">\n'
        '<meta name="apple-mobile-web-app-title" content="北辰ノート">\n<meta name="theme-color" content="#1f3b64">\n')
    standalone = head_full + head_common + '</head>\n<body>\n' + body + '</body>\n</html>\n'
    with open(os.path.join(ROOT, 'out', 'app_standalone.html'), 'w', encoding='utf-8') as f:
        f.write(standalone)
    # published site (GitHub Pages etc.): docs/index.html with manifest + icons
    site = (head_full + '<link rel="manifest" href="manifest.webmanifest">\n<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">\n'
            '<link rel="icon" type="image/png" sizes="32x32" href="icons/favicon-32.png">\n' + head_common + '</head>\n<body>\n' + body + '</body>\n</html>\n')
    os.makedirs(os.path.join(ROOT, 'docs'), exist_ok=True)
    with open(os.path.join(ROOT, 'docs', 'index.html'), 'w', encoding='utf-8') as f:
        f.write(site)
    print('artifact   %d KB  out/app_artifact.html' % (len(head_common + body) // 1024))
    print('standalone %d KB  out/app_standalone.html' % (len(standalone) // 1024))
    print('site       %d KB  docs/index.html' % (len(site) // 1024))

if __name__ == '__main__':
    main()
