/* ===== Notes view: everything the student wrote, in one place ===== */
const NotesView = (() => {
  const st = { sid: '', kind: '', q: '' };
  function entries() {
    const out = [];
    Notes.all().forEach(n => { const u = n.ukey ? unitByKey(n.ukey) : null; out.push({ kind: 'note', t: n.u || n.t, n, u, sid: u ? u.subject : '', text: (n.quote ? n.quote + ' ' : '') + n.text }); });
    Object.entries(S.hl).forEach(([ukey, list]) => { const u = unitByKey(ukey); if (!u) return; list.forEach(h => out.push({ kind: 'hl', t: h.t || 0, h, u, ukey, sid: u.subject, text: h.txt || '' })); });
    Object.entries(S.nb).forEach(([ukey, doc]) => { const u = unitByKey(ukey); if (!u || !doc.pages) return; const pages = doc.pages.filter(p => p.strokes && p.strokes.length).length; if (pages) out.push({ kind: 'nb', t: 0, u, ukey, sid: u.subject, pages, text: '手書きノート' }); });
    Object.entries(S.ink).forEach(([ukey, doc]) => { const u = unitByKey(ukey); if (!u) return; const blocks = Object.values(doc.blocks || {}).filter(b => b.strokes && b.strokes.length).length; const sc = Object.values(doc.scratch || {}).filter(b => b.strokes && b.strokes.length).length; if (blocks || sc) out.push({ kind: 'ink', t: 0, u, ukey, sid: u.subject, blocks, sc, text: '書き込み' }); });
    return out;
  }
  function render() {
    const main = $('#main');
    main.innerHTML = '<h1 class="vh">まとめノート</h1><div class="card"><div class="nfilter">' +
      '<select id="nf-sid"><option value="">全教科</option>' + DATA.subjects.map(s => '<option value="' + s.id + '"' + (st.sid === s.id ? ' selected' : '') + '>' + esc(s.name) + '</option>').join('') + '</select>' +
      '<select id="nf-kind"><option value="">すべての種類</option><option value="note"' + (st.kind === 'note' ? ' selected' : '') + '>付箋</option><option value="hl"' + (st.kind === 'hl' ? ' selected' : '') + '>マーカー</option><option value="nb"' + (st.kind === 'nb' ? ' selected' : '') + '>手書きノート</option><option value="ink"' + (st.kind === 'ink' ? ' selected' : '') + '>教材への書き込み</option></select>' +
      '<input type="search" id="nf-q" placeholder="付箋・マーカーの文字を検索" value="' + esc(st.q) + '">' +
      '<button class="primary" id="nf-add">＋ 付箋</button></div>' +
      '<div class="nlist" id="nlist"></div></div>';
    $('#nf-sid').onchange = e => { st.sid = e.target.value; list(); };
    $('#nf-kind').onchange = e => { st.kind = e.target.value; list(); };
    let t; $('#nf-q').addEventListener('input', e => { st.q = e.target.value; clearTimeout(t); t = setTimeout(list, 150); });
    $('#nf-add').onclick = () => Notes.create({});
    list();
  }
  function list() {
    const box = $('#nlist'); if (!box) return;
    let es = entries();
    if (st.sid) es = es.filter(e => e.sid === st.sid);
    if (st.kind) es = es.filter(e => e.kind === st.kind);
    if (st.q.trim()) { const q = st.q.trim().toLowerCase(); es = es.filter(e => (e.text || '').toLowerCase().includes(q)); }
    const order = { note: 0, hl: 1, nb: 2, ink: 3 };
    es.sort((a, b) => (order[a.kind] - order[b.kind]) || (b.t - a.t));
    if (!es.length) { box.innerHTML = '<div class="emptybox">まだありません。「学ぶ」で文章を長押しして選ぶとマーカーや付箋がつけられます。<br>ペン（書き込み）で書いたものもここに集まります。</div>'; return; }
    const counts = es.reduce((a, e) => { a[e.kind] = (a[e.kind] || 0) + 1; return a; }, {});
    box.innerHTML = '<div class="sm muted" style="margin-bottom:8px">付箋 ' + (counts.note || 0) + '　マーカー ' + (counts.hl || 0) + '　手書きノート ' + (counts.nb || 0) + '　書き込みのある単元 ' + (counts.ink || 0) + '</div>' + es.map(e => {
      const ulink = e.u ? '<span class="lnk" data-u="' + esc(e.u.ukey) + '" data-ci="' + (e.kind === 'note' ? (e.n.ci == null ? '' : e.n.ci) : (e.kind === 'hl' ? e.h.b : '')) + '"><span class="pill ' + subjOf(e.u).key + '">' + esc(subjOf(e.u).short) + '</span> ' + (EDITIONS.length > 1 ? '<span class="pill">' + esc(edLabel(e.u)) + '</span> ' : '') + esc(unitLabel(e.u)) + '</span>' : '<span class="pill">全体</span>';
      if (e.kind === 'note') { const d = new Date(e.n.u || e.n.t); return '<div class="ni"><span class="nbar" style="background:var(--note-' + e.n.c + ')"></span><div><div class="nmeta"><span>付箋</span>' + ulink + '<span>' + (d.getMonth() + 1) + '/' + d.getDate() + '</span><span class="grow"></span><button class="small" data-edit="' + e.n.id + '">編集</button></div>' + (e.n.quote ? '<div class="nq">「' + esc(e.n.quote) + '」</div>' : '') + '<div class="ntext">' + esc(e.n.text) + '</div></div></div>'; }
      if (e.kind === 'hl') return '<div class="ni"><span class="nbar" style="background:' + HL.COLORS[e.h.c] + '"></span><div><div class="nmeta"><span>マーカー</span>' + ulink + '<span class="grow"></span><button class="small" data-hldel="' + esc(e.ukey) + '|' + e.h.b + '|' + e.h.s + '|' + e.h.e + '">消す</button></div><div class="ntext"><mark class="hl-' + e.h.c + '">' + esc(e.h.txt) + '</mark></div></div></div>';
      if (e.kind === 'nb') return '<div class="ni"><span class="nbar" style="background:var(--ai-2)"></span><div><div class="nmeta"><span>手書きノート</span>' + ulink + '<span class="grow"></span><button class="small" data-nb="' + esc(e.ukey) + '">開く</button></div><div class="ntext">' + e.pages + ' ページ</div></div></div>';
      return '<div class="ni"><span class="nbar" style="background:var(--ink-3)"></span><div><div class="nmeta"><span>教材への書き込み</span>' + ulink + '</div><div class="ntext">' + (e.blocks ? e.blocks + ' か所に書き込み' : '') + (e.sc ? (e.blocks ? '、' : '') + e.sc + ' 問に計算メモ' : '') + '</div></div></div>';
    }).join('');
    $$('.lnk', box).forEach(x => x.onclick = () => Learn.open(x.dataset.u, x.dataset.ci === '' ? null : +x.dataset.ci));
    $$('[data-nb]', box).forEach(x => x.onclick = () => Notebook.open(unitByKey(x.dataset.nb)));
    $$('[data-hldel]', box).forEach(x => x.onclick = () => { const [uk, b, s, e] = x.dataset.hldel.split('|'); HL.removeRange(uk, +b, +s, +e); list(); });
  }
  return { render, refresh: () => { if (App.view === 'notes') list(); } };
})();
