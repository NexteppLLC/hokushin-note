/* ===== 北辰10月 学習ノート — core ===== */
'use strict';
const $ = (sel, root) => (root || document).querySelector(sel);
const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const el = (html) => { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstElementChild; };
const pad2 = n => String(n).padStart(2, '0');
const todayISO = () => { const d = new Date(); return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()); };
const fmtDate = iso => { const [y, m, d] = iso.split('-').map(Number); return m + '月' + d + '日'; };
const WD = ['日', '月', '火', '水', '木', '金', '土'];
const wdOf = iso => { const [y, m, d] = iso.split('-').map(Number); return WD[new Date(y, m - 1, d).getDay()]; };
const addDays = (iso, n) => { const [y, m, d] = iso.split('-').map(Number); const dt = new Date(y, m - 1, d + n); return dt.getFullYear() + '-' + pad2(dt.getMonth() + 1) + '-' + pad2(dt.getDate()); };
const diffDays = (a, b) => { const [y1, m1, d1] = a.split('-').map(Number); const [y2, m2, d2] = b.split('-').map(Number); return Math.round((new Date(y2, m2 - 1, d2) - new Date(y1, m1 - 1, d1)) / 86400000); };
const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const pct = (a, b) => b ? Math.round(a / b * 100) : 0;

/* ---- data: editions (教材セット) ---- */
const DATA = JSON.parse(document.getElementById('content-data').textContent);
const EDITIONS = DATA.editions;                 // [{id, name, short, test_day, start, subjects, plan}]
const EDITIONS_BY_ID = {};
const SUBJ_ORDER = ['E', 'M', 'J', 'S', 'H'];
EDITIONS.forEach(E => {
  EDITIONS_BY_ID[E.id] = E;
  E.SUBJ = {}; E.SUBJ_BY_KEY = {}; E.DAY_BY_DATE = {};
  E.plan.days.forEach(d => { E.DAY_BY_DATE[d.date] = d; });
  E.subjects.forEach(s => {
    s.ed = E.id;
    E.SUBJ[s.id] = s; E.SUBJ_BY_KEY[s.key] = s;
    s.byCode = {}; s.byKey = {};
    s.units.forEach((u, i) => {
      u.ed = E.id; u.subject = s.id; u.idx = i;
      u.ukey = E.id + ':' + s.id + '/' + (u.code && !s.byCode[u.code] ? u.code : 'x' + i);
      if (u.code && !s.byCode[u.code]) s.byCode[u.code] = u;
      (u.codes || []).forEach(c => { if (!s.byCode[c]) s.byCode[c] = u; });
      s.byKey[u.ukey] = u;
      u.items = [];  // gradable items {key, ci, n, q, a, label}
      u.content.forEach((c, ci) => {
        c.ci = ci;
        if (c.t === 'ex') {
          if (c.items) c.items.forEach(it => u.items.push({ key: u.ukey + '#' + ci + ':' + it.n, ci, n: it.n, q: it.q, a: it.a, label: c.title, numberLabel: it.l || String(it.n), context: (c.externalContext || '') + (c.context || ''), contextTitle: c.contextTitle || '' }));
          else if (c.kanji) c.kanji.forEach(part => part.items.forEach(it => u.items.push({ key: u.ukey + '#' + ci + ':' + part.kind + ':' + it.n, ci, n: it.n, q: it.q, a: it.a, label: c.title + '・' + part.kind, numberLabel: String(it.n), context: c.externalContext || '', contextTitle: c.contextTitle || '', kanji: part.kind })));
          else u.items.push({ key: u.ukey + '#' + ci + ':all', ci, n: 0, q: c.q, a: c.a, label: c.title, context: c.externalContext || '', contextTitle: c.contextTitle || '', whole: true });
        } else if (c.vocab) {
          c.vocab.forEach(v => u.items.push({ key: u.ukey + '#v' + ci + ':' + v.n, ci, n: v.n, q: '<b>' + esc(v.word) + '</b> <span class="muted sm">' + esc(v.pos) + '</span>', a: esc(v.meaning), label: '単語', vocab: v }));
        }
      });
    });
    // Separated answer-only units remain in their original slots. Match their exact
    // rendered answer text to existing questions so viewing them is never a first attempt.
    const answerIndex = new Map();
    s.units.forEach(u => u.content.forEach(c => { if (c.t === 'ex' && c.a) {
      const key = (c.atitle || '') + '\n' + c.a;
      const list = answerIndex.get(key) || [];
      list.push(...u.items.filter(it => it.ci === c.ci).map(it => it.key)); answerIndex.set(key, list);
    } }));
    s.units.forEach(u => u.content.forEach(c => { if (c.t === 'a') c.answerKeys = answerIndex.get((c.title || '') + '\n' + c.html) || []; }));
  });
});
/* current edition — these globals are re-pointed by setEdition() */
let ED = EDITIONS[EDITIONS.length - 1], SUBJ = ED.SUBJ, SUBJ_BY_KEY = ED.SUBJ_BY_KEY, PLAN = ED.plan, DAY_BY_DATE = ED.DAY_BY_DATE;
function setEdition(id) {
  const E = EDITIONS_BY_ID[id] || EDITIONS[EDITIONS.length - 1];
  ED = E; SUBJ = E.SUBJ; SUBJ_BY_KEY = E.SUBJ_BY_KEY; PLAN = E.plan; DAY_BY_DATE = E.DAY_BY_DATE;
  DATA.subjects = E.subjects;
  return E;
}
function defaultEdition() {
  const t = todayISO();
  const live = EDITIONS.find(E => E.start <= t && t <= E.test_day);
  if (live) return live.id;
  const next = EDITIONS.find(E => t < E.start);
  return (next || EDITIONS[EDITIONS.length - 1]).id;
}
DATA.subjects = ED.subjects;

function unitByKey(ukey) {
  if (!ukey) return null;
  const edid = ukey.split(':')[0]; const E = EDITIONS_BY_ID[edid]; if (!E) return null;
  const sid = ukey.slice(edid.length + 1).split('/')[0];
  return E.SUBJ[sid] && E.SUBJ[sid].byKey[ukey];
}
function subjOf(u) { return EDITIONS_BY_ID[u.ed].SUBJ[u.subject]; }
function unitLabel(u) { return (u.code ? u.code + '　' : '') + u.title; }
function edLabel(u) { const E = EDITIONS_BY_ID[u.ed]; return E ? (E.short || E.name) : u.ed; }

// Question context is kept separate from the question/answer, so reverse cards and
// repeated displays never duplicate it or accidentally put it on the answer side.
function questionContextHTML(context, title) {
  if (!context && !title) return '';
  return '<section class="exercise-context" aria-label="共通資料">' +
    (title ? '<div class="ex-title">' + esc(title) + '</div>' : '') + (context || '') + '</section>';
}
function studyCard(it, sid) {
  return { key: it.key, q: it.q, a: it.a, context: it.context || '', contextTitle: it.contextTitle || '',
    label: it.label + (it.numberLabel ? '　' + it.numberLabel : ''), sid, ruby: SUBJ[sid].ruby };
}

/* ---- storage (IndexedDB key-value, localStorage fallback, memory fallback) ---- */
const Store = (() => {
  let db = null, mode = 'idb', mem = {};
  function open() {
    return new Promise((res) => {
      try {
        const req = indexedDB.open('hokushin-note', 1);
        req.onupgradeneeded = () => { req.result.createObjectStore('kv'); };
        req.onsuccess = () => { db = req.result; res(); };
        req.onerror = () => { mode = 'ls'; res(); };
        req.onblocked = () => { mode = 'ls'; res(); };
      } catch (e) { mode = 'ls'; res(); }
    });
  }
  function lsGet(k) { try { const v = localStorage.getItem('hn:' + k); return v == null ? undefined : JSON.parse(v); } catch (e) { return mem[k]; } }
  function lsSet(k, v) { try { localStorage.setItem('hn:' + k, JSON.stringify(v)); } catch (e) { mode = 'mem'; mem[k] = v; } }
  function lsDel(k) { try { localStorage.removeItem('hn:' + k); } catch (e) {} delete mem[k]; }
  function lsKeys(prefix) { const out = []; try { for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (k.startsWith('hn:' + prefix)) out.push(k.slice(3)); } } catch (e) {} Object.keys(mem).forEach(k => { if (k.startsWith(prefix) && !out.includes(k)) out.push(k); }); return out; }
  function tx(m) { return db.transaction('kv', m).objectStore('kv'); }
  const api = {
    open,
    mode: () => mode,
    get(k) { if (mode !== 'idb') return Promise.resolve(lsGet(k)); return new Promise((res) => { try { const r = tx('readonly').get(k); r.onsuccess = () => res(r.result); r.onerror = () => res(undefined); } catch (e) { res(lsGet(k)); } }); },
    set(k, v) { if (mode !== 'idb') { lsSet(k, v); return Promise.resolve(); } return new Promise((res, rej) => { try { const r = tx('readwrite').put(v, k); r.onsuccess = () => res(); r.onerror = () => rej(r.error); } catch (e) { rej(e); } }); },
    del(k) { if (mode !== 'idb') { lsDel(k); return Promise.resolve(); } return new Promise((res) => { try { const r = tx('readwrite').delete(k); r.onsuccess = () => res(); r.onerror = () => res(); } catch (e) { res(); } }); },
    keys(prefix) { if (mode !== 'idb') return Promise.resolve(lsKeys(prefix)); return new Promise((res) => { try { const r = tx('readonly').getAllKeys(IDBKeyRange.bound(prefix, prefix + '￿')); r.onsuccess = () => res(r.result); r.onerror = () => res([]); } catch (e) { res([]); } }); },
    async getAll(prefix) { const ks = await api.keys(prefix); const out = {}; for (const k of ks) out[k] = await api.get(k); return out; },
    async clear() { if (mode !== 'idb') { lsKeys('').forEach(lsDel); mem = {}; return; } return new Promise((res) => { try { const r = tx('readwrite').clear(); r.onsuccess = () => res(); r.onerror = () => res(); } catch (e) { res(); } }); }
  };
  return api;
})();

/* ---- state ---- */
const S = {
  progress: {},   // '<edition>:<subject>' -> {items:{key:{g,t}}, units:{ukey:{v,d}}}
  plan: { done: {}, log: {} },   // done: '<edition>|day:sk:code' -> ts ; log: date -> {m, g}
  notes: { list: [] },
  settings: { fingerDraw: false, fs: 'm', ruby: true, penColor: '#1b1f26', penWidth: 2.5, tool: 'pen', view: 'today', last: {}, lastBackup: 0, name: '', edition: '' },
  hl: {},   // ukey -> [{b,s,e,c,txt}]
  ink: {},  // ukey -> { blocks:{ci:{w,strokes}}, scratch:{itemKey:{w,strokes}} }
  nb: {},   // ukey -> {pages:[{strokes}]}
  loaded: false
};
const dirty = new Set(); let saveTimer = null;
function markDirty(path) { dirty.add(path); setStatus('…'); clearTimeout(saveTimer); saveTimer = setTimeout(flush, 400); }
async function flush() {
  const paths = Array.from(dirty); dirty.clear();
  for (const p of paths) {
    const col = p.split('/')[0];
    let v;
    if (col === 'progress') v = S.progress[p.slice(9)];
    else if (col === 'plan') v = S.plan;
    else if (col === 'notes') v = S.notes;
    else if (col === 'settings') v = S.settings;
    else if (col === 'hl') v = S.hl[p.slice(3)];
    else if (col === 'ink') v = S.ink[p.slice(4)];
    else if (col === 'nb') v = S.nb[p.slice(3)];
    try { if (v === undefined) await Store.del(p); else await Store.set(p, JSON.parse(JSON.stringify(v))); }
    catch (e) { console.warn('save failed', p, e); setStatus('保存失敗'); toast('保存できませんでした（容量不足の可能性）'); return; }
  }
  setStatus('保存済み'); setTimeout(() => { if ($('#save-status').textContent === '保存済み') setStatus(''); }, 1500);
}
function setStatus(t) { const e = $('#save-status'); if (e) e.textContent = t; }
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden' && dirty.size) { clearTimeout(saveTimer); flush(); } });
window.addEventListener('pagehide', () => { if (dirty.size) { clearTimeout(saveTimer); flush(); } });

/* v1 (single edition, no prefixes) -> v2 keys. Returns true when anything changed. */
const V1_ED = 'h5';
function migrateV1(obj) {
  let changed = false;
  const isV2 = k => /^[A-Za-z0-9_-]+:[a-z]+\//.test(k);
  const fixKey = k => { if (k && !isV2(k)) { changed = true; return V1_ED + ':' + k; } return k; };
  // progress docs keyed by subject only
  Object.keys(obj.progress || {}).forEach(k => {
    if (/^[A-Za-z0-9_-]+:[a-z]+$/.test(k)) return;
    const doc = obj.progress[k]; const items = {}, units = {};
    Object.entries(doc.items || {}).forEach(([ik, v]) => { items[fixKey(ik)] = v; });
    Object.entries(doc.units || {}).forEach(([uk, v]) => { units[fixKey(uk)] = v; });
    obj.progress[V1_ED + ':' + k] = { items, units }; delete obj.progress[k]; changed = true;
  });
  if (obj.plan && obj.plan.done) { const d = {}; Object.entries(obj.plan.done).forEach(([k, v]) => { if (k.includes('|')) d[k] = v; else { d[V1_ED + '|' + k] = v; changed = true; } }); obj.plan.done = d; }
  if (obj.notes && obj.notes.list) obj.notes.list.forEach(n => { if (n.ukey && !isV2(n.ukey)) { n.ukey = V1_ED + ':' + n.ukey; changed = true; } });
  ['hl', 'ink', 'nb'].forEach(col => { const m = obj[col] || {}; Object.keys(m).forEach(k => { if (!isV2(k)) { m[V1_ED + ':' + k] = m[k]; delete m[k]; changed = true; } }); });
  if (obj.ink) Object.values(obj.ink).forEach(doc => { if (doc && doc.scratch) { const sc = {}; Object.entries(doc.scratch).forEach(([k, v]) => { sc[fixKey(k)] = v; }); doc.scratch = sc; } });
  if (obj.settings && obj.settings.last && obj.settings.last.ukey) obj.settings.last.ukey = fixKey(obj.settings.last.ukey);
  return changed;
}

async function loadState() {
  await Store.open();
  const all = await Store.getAll('');
  const oldKeys = [];
  for (const [k, v] of Object.entries(all)) {
    if (v == null) continue;
    if (k.startsWith('progress/')) S.progress[k.slice(9)] = v;
    else if (k === 'plan/main') S.plan = Object.assign({ done: {}, log: {} }, v);
    else if (k === 'notes/all') S.notes = Object.assign({ list: [] }, v);
    else if (k === 'settings/main') S.settings = Object.assign(S.settings, v);
    else if (k.startsWith('hl/')) S.hl[k.slice(3)] = v;
    else if (k.startsWith('ink/')) S.ink[k.slice(4)] = v;
    else if (k.startsWith('nb/')) S.nb[k.slice(3)] = v;
    else continue;
    if (/^(progress|hl|ink|nb)\//.test(k) && !/^(progress|hl|ink|nb)\/[A-Za-z0-9_-]+:[a-z]+/.test(k)) oldKeys.push(k);
  }
  if (migrateV1(S)) {
    for (const k of oldKeys) { try { await Store.del(k); } catch (e) {} }
    Object.keys(S.progress).forEach(k => markDirty('progress/' + k)); markDirty('plan/main'); markDirty('notes/all'); markDirty('settings/main');
    Object.keys(S.hl).forEach(k => markDirty('hl/' + k)); Object.keys(S.ink).forEach(k => markDirty('ink/' + k)); Object.keys(S.nb).forEach(k => markDirty('nb/' + k));
  }
  setEdition(S.settings.edition && EDITIONS_BY_ID[S.settings.edition] ? S.settings.edition : defaultEdition());
  EDITIONS.forEach(E => E.subjects.forEach(s => progOf(s)));
  Study.migrateAll(S).forEach(k => markDirty('progress/' + k));
  S.loaded = true;
}

/* ---- grades ---- */
/** progress doc for a unit / subject object / item key */
function progOf(x) {
  let k;
  if (typeof x === 'string') { const edid = x.split(':')[0]; const sid = x.slice(edid.length + 1).split('/')[0]; k = edid + ':' + sid; }
  else k = x.ed + ':' + (x.subject || x.id);
  if (!S.progress[k]) S.progress[k] = { items: {}, units: {} };
  if (!S.progress[k].items) S.progress[k].items = {};
  if (!S.progress[k].units) S.progress[k].units = {};
  return S.progress[k];
}
function progKey(x) { return typeof x === 'string' ? (x.split(':')[0] + ':' + x.slice(x.indexOf(':') + 1).split('/')[0]) : x.ed + ':' + (x.subject || x.id); }
function gradeOf(subjectId, key) { const it = progOf(key).items[key]; return it ? it.g : undefined; }
function setGrade(subjectId, key, g, opts) {
  return Study.record(key, g, opts);
}
function unitStats(u) {
  const doc = progOf(u); const items = doc.items;
  let total = u.items.length, graded = 0, ok = 0, ng = 0;
  u.items.forEach(it => { const r = items[it.key]; if (r && (r.g === 0 || r.g === 1 || r.g === 2)) { graded++; if (r.g === 2) ok++; else ng++; } });
  const rec = doc.units[u.ukey] || {};
  const done = !!rec.d || (total > 0 && graded === total);
  return { total, graded, ok, ng, done, viewed: !!rec.v, hasItems: total > 0 };
}
function subjectStats(s) {
  let units = 0, unitsDone = 0, items = 0, graded = 0, ok = 0, ng = 0;
  s.units.forEach(u => { if (!u.code || /^0(-|$)/.test(u.code)) return; units++; const st = unitStats(u); if (st.done) unitsDone++; items += st.total; graded += st.graded; ok += st.ok; ng += st.ng; });
  return { units, unitsDone, items, graded, ok, ng };
}
function logActivity() { const d = todayISO(); S.plan.log[d] = S.plan.log[d] || { m: 0, g: 0 }; S.plan.log[d].g = (S.plan.log[d].g || 0) + 1; markDirty('plan/main'); }

/* ---- plan helpers (current edition) ---- */
function taskKey(day, sk, code) { return ED.id + '|' + day + ':' + sk + ':' + code; }
function dayStats(day) { let total = 0, done = 0, tm = 0, tmDone = 0; SUBJ_ORDER.forEach(sk => (day.tasks[sk] || []).forEach(t => { total++; tm += t.minutes; if (S.plan.done[taskKey(day.day, sk, t.code)]) { done++; tmDone += t.minutes; } })); return { total, done, tm, tmDone }; }
function resolveTask(sk, code) {
  const s = SUBJ_BY_KEY[sk];
  if (s.byCode[code]) return { unit: s.byCode[code] };
  if (/R$/.test(code) && s.byCode[code.slice(0, -1)]) return { unit: s.byCode[code.slice(0, -1)], review: true };
  if (/^L[SRX]$/.test(code)) { const u = s.units.find(x => /^L\d/.test(x.code || '')); return { unit: u, weak: true }; }
  if (/^WX$/.test(code)) return { unit: s.byCode['W1'], weak: true };
  if (/^R2R$/.test(code)) return { unit: s.byCode['R2-1'], weak: true };
  return { weak: true };
}

/* ---- ui helpers ---- */
let toastTimer;
function toast(msg) { const t = $('#toast'); t.textContent = msg; t.classList.add('show'); clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove('show'), 2200); }
function openModal(title, bodyHTML, opts) {
  opts = opts || {};
  const root = $('#modal-root');
  const m = el('<div class="modal-bg"><div class="modal ' + (opts.wide ? 'wide' : '') + '" role="dialog" aria-modal="true"><div class="mh"><span class="mt"></span><button class="mx" aria-label="閉じる">閉じる ✕</button></div><div class="mb"></div>' + (opts.footer ? '<div class="mf"></div>' : '') + '</div></div>');
  $('.mt', m).textContent = title;
  if (typeof bodyHTML === 'string') $('.mb', m).innerHTML = bodyHTML; else $('.mb', m).appendChild(bodyHTML);
  if (opts.footer) $('.mf', m).innerHTML = opts.footer;
  const close = () => { m.remove(); if (opts.onClose) opts.onClose(); };
  $('.mx', m).addEventListener('click', close);
  m.addEventListener('click', e => { if (e.target === m && !opts.sticky) close(); });
  root.appendChild(m);
  m.close = close;
  return m;
}
function confirmBox(msg) {
  return new Promise(res => {
    const m = openModal('確認', '<p>' + esc(msg) + '</p>', { footer: '<button class="primary" data-ok>はい</button><button data-no>いいえ</button>', sticky: true });
    $('[data-ok]', m).onclick = () => { m.close(); res(true); };
    $('[data-no]', m).onclick = () => { m.close(); res(false); };
  });
}
function svgIcon(name) {
  const I = {
    pen: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/><path d="M2 2l7.6 7.6"/></svg>',
    note: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 4h14v11l-5 5H5z"/><path d="M14 20v-5h5"/></svg>',
    book: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z"/><path d="M4 20.5V5.5"/></svg>',
    check: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12l5 5L20 7"/></svg>',
    cards: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="6" width="14" height="14" rx="2"/><path d="M7 6V4a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-2"/></svg>',
    search: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>'
  };
  return I[name] || '';
}
