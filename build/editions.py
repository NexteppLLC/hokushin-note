# -*- coding: utf-8 -*-
"""Edition (教材セット) helpers shared by the build scripts.

An edition is one study package (e.g. h5 = 第5回北辰). Its sources live in src/<id>/, its
data in data/<id>/ and its PDFs in deliver/<id>/. editions.json lists them in order.
"""
import os, sys, json, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load():
    with open(os.path.join(ROOT, 'editions.json'), encoding='utf-8') as f:
        return json.load(f)['editions']


def by_id(eid):
    for e in load():
        if e['id'] == eid:
            return e
    raise SystemExit('unknown edition: %s (see editions.json)' % eid)


def latest():
    return load()[-1]


def resolve(argv):
    """Pull an edition out of argv: '--edition h6' or a leading positional id. Returns (edition, rest)."""
    args = list(argv)
    if '--edition' in args:
        i = args.index('--edition')
        eid = args[i + 1]
        del args[i:i + 2]
        return by_id(eid), args
    ids = {e['id'] for e in load()}
    if args and args[0] in ids:
        return by_id(args[0]), args[1:]
    return latest(), args


def src_dir(ed, *parts):
    return os.path.join(ROOT, 'src', ed['id'], *parts)


def data_dir(ed, *parts):
    p = os.path.join(ROOT, 'data', ed['id'], *parts)
    os.makedirs(os.path.dirname(p) if parts else p, exist_ok=True)
    return p


def out_dir(ed, *parts):
    p = os.path.join(ROOT, 'out', ed['id'], *parts)
    os.makedirs(os.path.dirname(p) if parts else p, exist_ok=True)
    return p


def deliver_dir(ed, *parts):
    p = os.path.join(ROOT, 'deliver', ed['id'], *parts)
    os.makedirs(os.path.dirname(p) if parts else p, exist_ok=True)
    return p


def import_module(ed, name):
    """Import src/<edition>/<name>.py (e.g. plan_data, kanji_data)."""
    path = src_dir(ed, name + '.py')
    spec = importlib.util.spec_from_file_location(ed['id'] + '_' + name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def find_src(ed, rel):
    """Resolve a source-relative path: edition dir first, then the shared src/ dir."""
    for cand in (src_dir(ed, rel), os.path.join(ROOT, 'src', rel)):
        if os.path.exists(cand):
            return cand
    raise FileNotFoundError(rel)
