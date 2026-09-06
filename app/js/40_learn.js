/* ===== Learn view: subject/unit dropdowns, knowledge blocks, exercises, ink, notes ===== */
const Learn = (() => {
  const st = { sid: 'english', ukey: null, tab: 'all', onlyNg: false, task: null, scrollTo: null, mode: 'auto', run: null, runUnit: null };
  const GR = [[2, '○'], [1, '△'], [0, '×']];
  const inkDoc = ukey => { S.ink[ukey] = S.ink[ukey] || { blocks: {}, scratch: {} }; S.ink[ukey].blocks = S.ink[ukey].blocks || {}; S.ink[ukey].scratch = S.ink[ukey].scratch || {}; return S.ink[ukey]; };

  function ensure() {
    const okKey = k => { const u = k && unitByKey(k); return u && u.ed === ED.id; };
    if (okKey(st.ukey)) { st.sid = unitByKey(st.ukey).subject; return; }
    const last = S.settings.last || {};
    if (okKey(last.ukey)) { st.ukey = last.ukey; st.sid = unitByKey(last.ukey).subject; return; }
    st.sid = 'english'; st.ukey = SUBJ.english.units[0].ukey;
  }
  function statusMark(u) { const s = unitStats(u); return s.done ? '✓ ' : (s.graded > 0 ? '◐ ' : ''); }
  function unitOptions(s, sel) {
    let html = '', chap = null, open = false;
    s.units.forEach(u => {
      if (u.chapter !== chap) { if (open) html += '</optgroup>'; chap = u.chapter; html += '<optgroup label="' + esc(chap || '') + '">'; open = true; }
      html += '<option value="' + esc(u.ukey) + '"' + (u.ukey === sel ? ' selected' : '') + '>' + esc(statusMark(u) + unitLabel(u)) + '</option>';
    });
    if (open) html += '</optgroup>';
    return html;
  }
  function render() {
    ensure();
    const s = SUBJ[st.sid], u = unitByKey(st.ukey);
    if (!st.run || st.runUnit !== u.ukey || st.run.date !== todayISO()) { st.run = Study.session(st.mode, 'learn'); st.runUnit = u.ukey; }
    S.settings.last = { ukey: st.ukey }; markDirty('settings/main');
    const rec = progOf(u).units[u.ukey] = progOf(u).units[u.ukey] || {};
    if (!rec.v || Date.now() - rec.v > 3600e3) { rec.v = Date.now(); markDirty('progress/' + progKey(u)); }
    const stat = unitStats(u);
    const main = $('#main');
    const hasEx = u.content.some(c => c.t === 'ex' || c.t === 'q' || c.vocab);
    main.innerHTML = '' +
      '<div class="learn-ctl">' +
        '<div class="row1">' +
          '<select class="subj" id="sel-subj" aria-label="科目">' + DATA.subjects.map(x => '<option value="' + x.id + '"' + (x.id === s.id ? ' selected' : '') + '>' + esc(x.name) + '</option>').join('') + '</select>' +
          '<select class="unit" id="sel-unit" aria-label="単元">' + unitOptions(s, u.ukey) + '</select>' +
          '<button class="icon" id="btn-prev" aria-label="前の単元" ' + (u.idx === 0 ? 'disabled' : '') + '>‹</button>' +
          '<button class="icon" id="btn-next" aria-label="次の単元" ' + (u.idx === s.units.length - 1 ? 'disabled' : '') + '>›</button>' +
          '<button class="icon" id="btn-search" aria-label="検索" title="検索">' + svgIcon('search') + '</button>' +
        '</div>' +
        '<div class="row2">' +
          '<div class="seg" id="seg-tab">' + [['all', 'すべて'], ['points', '要点'], ['ex', '演習']].map(([k, l]) => '<button data-tab="' + k + '" class="' + (st.tab === k ? 'active' : '') + '"' + (k === 'ex' && !hasEx ? ' disabled' : '') + '>' + l + '</button>').join('') + '</div>' +
          '<div class="tools">' +
            '<button data-act="pen" class="' + (Ink.isPen() ? 'on' : '') + '">' + svgIcon('pen') + '<span>書き込み</span></button>' +
            '<button data-act="note">' + svgIcon('note') + '<span>付箋</span></button>' +
            '<button data-act="nb">' + svgIcon('book') + '<span>ノート' + ((S.nb[u.ukey] && S.nb[u.ukey].pages && S.nb[u.ukey].pages.some(p => p.strokes && p.strokes.length)) ? ' ●' : '') + '</span></button>' +
            (stat.total ? '<button data-act="cards">' + svgIcon('cards') + '<span>カード</span></button>' : '') +
            '<button data-act="done" class="' + (rec.d ? 'on' : '') + '">' + svgIcon('check') + '<span>' + (rec.d ? '取り組み済み' : '取り組み済みにする') + '</span></button>' +
          '</div>' +
        '</div>' +
      '</div>' +
      (st.task ? '<div class="banner" id="task-banner">今日の予定：<b>' + esc(st.task.code + '　' + st.task.title) + '</b>（' + st.task.minutes + '分）　<button class="small primary" id="task-done">' + (S.plan.done[taskKey(st.task.day, st.task.sk, st.task.code)] ? '完了ずみ ✓' : 'この予定を完了にする') + '</button></div>' : '') +
      '<div class="unit-head"><span class="uc">' + esc(u.code || '—') + '</span><span class="ut">' + esc(u.title) + '</span><span class="uch">' + esc(u.chapter || '') + '</span>' +
        (stat.total ? '<span class="uprog"><span class="bar ' + s.key + '"><i style="width:' + pct(stat.graded, stat.total) + '%"></i></span><span class="num">' + stat.graded + '/' + stat.total + '問　○' + stat.ok + '</span>' + (stat.ng ? '<button class="small" data-act="onlyng">' + (st.onlyNg ? '全部表示' : '×△だけ') + '</button>' : '') + '</span>' : '') +
      '</div>' +
      (stat.total ? '<div class="study-toolbar"><label>練習の種類 <select id="study-mode">' + Study.modeOptions(st.mode) + '</select></label><button class="small" id="study-restart">新しく解き始める</button><p class="sm muted">' + Study.help + '</p></div>' : '') +
      '<div id="unit-notes" class="notes-wrap"></div>' +
      '<div id="content"></div>' +
      '<div class="unit-nav">' +
        (u.idx > 0 ? '<button data-goto="' + esc(s.units[u.idx - 1].ukey) + '">‹ ' + esc(unitLabel(s.units[u.idx - 1])) + '</button>' : '<span></span>') +
        (u.idx < s.units.length - 1 ? '<button data-goto="' + esc(s.units[u.idx + 1].ukey) + '">' + esc(unitLabel(s.units[u.idx + 1])) + ' ›</button>' : '<span></span>') +
      '</div>';
    renderContent(u);
    refreshNotes();
    if (stat.total) {
      $('#study-mode').onchange = e => { st.mode = e.target.value; st.run = Study.session(st.mode, 'learn'); render(); };
      $('#study-restart').onclick = () => { st.run = Study.session(st.mode, 'learn'); render(); toast('新しい解答を記録します。答えは閉じました。'); };
    }
    // events
    $('#sel-subj').onchange = e => { st.sid = e.target.value; st.ukey = SUBJ[st.sid].units[0].ukey; st.task = null; render(); window.scrollTo(0, 0); };
    $('#sel-unit').onchange = e => { st.ukey = e.target.value; st.task = null; render(); window.scrollTo(0, 0); };
    $('#btn-prev').onclick = () => { if (u.idx > 0) { st.ukey = s.units[u.idx - 1].ukey; st.task = null; render(); window.scrollTo(0, 0); } };
    $('#btn-next').onclick = () => { if (u.idx < s.units.length - 1) { st.ukey = s.units[u.idx + 1].ukey; st.task = null; render(); window.scrollTo(0, 0); } };
    $('#btn-search').onclick = () => Search.open();
    $$('#seg-tab button').forEach(b => b.onclick = () => { st.tab = b.dataset.tab; render(); });
    $$('.unit-nav [data-goto]').forEach(b => b.onclick = () => { st.ukey = b.dataset.goto; st.task = null; render(); window.scrollTo(0, 0); });
    $$('.tools [data-act], .unit-head [data-act]').forEach(b => b.onclick = () => {
      const a = b.dataset.act;
      if (a === 'pen') Ink.setPenMode(!Ink.isPen());
      else if (a === 'note') Notes.create({ ukey: u.ukey });
      else if (a === 'nb') Notebook.open(u);
      else if (a === 'cards') Cards.start(u.items.map(it => studyCard(it, u.subject)), { title: unitLabel(u) + '　カード練習', ukey: u.ukey, mode: st.mode });
      else if (a === 'done') toggleDone(u);
      else if (a === 'onlyng') { st.onlyNg = !st.onlyNg; render(); }
    });
    if (st.task) $('#task-done').onclick = () => { const k = taskKey(st.task.day, st.task.sk, st.task.code); if (!S.plan.done[k]) { S.plan.done[k] = Date.now(); addMinutes(st.task.date, st.task.minutes); markDirty('plan/main'); toast('予定を完了にしました'); $('#task-done').textContent = '完了ずみ ✓'; } };
    if (st.scrollTo != null) { const target = $('.cblock[data-ci="' + st.scrollTo + '"]'); if (target) setTimeout(() => target.scrollIntoView({ behavior: 'smooth', block: 'start' }), 60); st.scrollTo = null; }
  }
  function addMinutes(date, m) { S.plan.log[date] = S.plan.log[date] || { m: 0, g: 0 }; S.plan.log[date].m = (S.plan.log[date].m || 0) + m; }
  function toggleDone(u) {
    const rec = progOf(u).units[u.ukey] = progOf(u).units[u.ukey] || {};
    if (rec.d) { delete rec.d; toast('取り組み済みを取り消しました'); } else { rec.d = Date.now(); toast('取り組み済みにしました'); }
    markDirty('progress/' + progKey(u)); render();
  }
  function visible(c) {
    if (st.tab === 'points') return c.t !== 'ex' && c.t !== 'q';
    if (st.tab === 'ex') return ['ex', 'q', 'h3', 'passage', 'dialog', 'data'].includes(c.t) || !!c.vocab;
    return true;
  }
  function renderContent(u) {
    const box = $('#content'); box.innerHTML = '';
    const list = u.content.filter(visible);
    if (!list.length) { box.innerHTML = '<div class="emptybox">この単元には' + (st.tab === 'ex' ? '演習' : '要点') + 'がありません</div>'; return; }
    list.forEach(c => { const e = renderBlock(u, c); box.appendChild(e); afterInsert(u, c, e); });
  }
  function rubyCls(u) { return 'cbody ' + (SUBJ[u.subject].ruby ? (S.settings.ruby ? 'ruby' : 'noruby') : ''); }
  function renderBlock(u, c) {
    const ci = c.ci;
    if (c.t === 'h3') return el('<div class="cblock t-h3" data-ci="' + ci + '" data-ukey="' + esc(u.ukey) + '"><div class="h3t">' + esc(c.title) + '</div></div>');
    const head = (title, extra) => '<div class="chead">' + (title ? '<span class="ct">' + esc(title) + '</span>' : '') + '<span class="cbtn">' + (extra || '') + '<button data-act="bnote" title="この部分に付箋">付箋</button></span></div>';
    if (c.t === 'ex') {
      const items = u.items.filter(it => it.ci === ci);
      const legacyCount = items.filter(it => { const rec = progOf(u).items[it.key]; return rec && rec.legacy && !Study.effective(rec).length; }).length;
      const graded = items.filter(it => gradeOf(u.subject, it.key) != null).length, ok = items.filter(it => gradeOf(u.subject, it.key) === 2).length;
      const extra = (items.length > 1 ? '<button data-act="cards" title="カードで練習">カード</button>' : '') + '<button data-act="showall">答えを全部' + '</button>';
      let body = '';
      if (c.kanji) {
        body = c.kanji.map(part => '<div class="ex-title" style="margin:6px 0 2px">' + esc(part.kind) + '（' + part.items.length + '問）<span class="muted sm">　' + (part.kind === '読み' ? '線の漢字の読みをひらがなで' : 'カタカナを漢字に') + '。解答後にタップで答え合わせ</span></div><div class="kanji-grid">' +
          part.items.map(it => { const key = u.ukey + '#' + ci + ':' + part.kind + ':' + it.n; const g = gradeOf(u.subject, key); return '<div class="kitem ' + (g == null ? '' : 'g' + g) + '" data-key="' + esc(key) + '"><span class="kn num">' + it.n + '</span><span class="kq">' + it.q + '</span><span class="kbot"><span class="ka hid">' + esc(it.a) + '</span><span class="kg">' + GR.map(([gv, gl]) => '<button class="gbtn g' + gv + (g === gv ? ' on' : '') + '" data-g="' + gv + '">' + gl + '</button>').join('') + '</span></span></div>'; }).join('') + '</div>').join('');
      } else if (c.items) {
        body = (c.items.map(it => { const key = u.ukey + '#' + ci + ':' + it.n; const g = gradeOf(u.subject, key); if (st.onlyNg && (g == null || g === 2)) return ''; return itemHTML(u, key, it.l, it.q, it.a, g); }).join('') || '<div class="emptybox">×・△の問題はありません</div>');
      } else {
        const key = u.ukey + '#' + ci + ':all'; const g = gradeOf(u.subject, key);
        body = '<div class="ex-whole item ' + (g == null ? '' : 'g' + g) + '" data-key="' + esc(key) + '">' + (c.parts ? c.parts.map(p => '<div class="ex-title">' + esc(p.title) + '</div><div>' + p.html + '</div>').join('') : '<div>' + c.q + '</div>') +
          '<div class="ia" hidden>' + (c.atitle ? '<div class="ex-title sm">' + esc(c.atitle) + '</div>' : '') + c.a + '</div>' +
          '<div class="ictl" style="margin-left:0"><button data-act="ans">解答を終えた・答え合わせ</button><button data-act="study" class="small">答えを見て学ぶ</button><span class="gr">' + GR.map(([gv, gl]) => '<button class="gbtn g' + gv + (g === gv ? ' on' : '') + '" data-g="' + gv + '">' + gl + '</button>').join('') + '</span>' + Study.reasonHTML(key, st.run) + '<button data-act="history" class="small">記録</button><button data-act="scratch" class="small">✎ 書く</button></div><div class="study-record-note">' + Study.noteHTML(key) + '</div><div class="scratch" style="margin-left:0" hidden><div class="sc-tools"><button data-sc="undo">戻す</button><button data-sc="clear">全消し</button><button data-sc="more">＋</button></div></div></div>';
      }
      const e = el('<div class="cblock t-ex" data-ci="' + ci + '" data-ukey="' + esc(u.ukey) + '">' + head(c.title || '演習', extra) +
        (legacyCount ? '<div class="study-legacy sm">改修前の採点 ' + legacyCount + '問を表示しています。初見・後日再テストの率には含めません。</div>' : '') +
        (items.length > 1 ? '<div class="ex-tools" style="padding:0 14px"><span class="exscore num" style="margin-left:0">採点 ' + graded + '/' + items.length + '　○ ' + ok + '</span></div>' : '') +
        (c.items && c.context ? '<div class="shared-material ' + rubyCls(u) + '">' + questionContextHTML(c.context) + '</div>' : '') +
        '<div class="' + rubyCls(u) + '" data-ci="' + ci + '">' + body + '</div></div>');
      return e;
    }
    // knowledge block
    const cls = 'cblock t-' + c.t;
    const vocabBtn = c.vocab ? '<button data-act="vcards">単語カードで練習（' + c.vocab.length + '語）</button>' : '';
    const title = c.title || (c.t === 'text' ? '' : ({ box: '要点', point: 'ポイント', note: 'メモ', warn: '注意', tip: 'コツ', summary: 'まとめ', goal: '目標', step: '手順', script: 'スクリプト', passage: '本文', dialog: '会話', rule: 'ルール', check: 'チェック', data: '資料', plan: '計画', memo: 'メモ', ex: '例', q: '問題', sub: '' }[c.t] || ''));
    return el('<div class="' + cls + '" data-ci="' + ci + '" data-ukey="' + esc(u.ukey) + '">' + head(title, vocabBtn) + '<div class="' + rubyCls(u) + '" data-ci="' + ci + '">' + c.html + '</div></div>');
  }
  function itemHTML(u, key, label, q, a, g) {
    return '<div class="item ' + (g == null ? '' : 'g' + g) + '" data-key="' + esc(key) + '">' +
      '<div class="iq"><span class="no">' + esc(label) + '</span><div class="qt">' + q + '</div></div>' +
      '<div class="ia" hidden>' + (a || '<span class="muted">（解答は下の解答欄を参照）</span>') + '</div>' +
      '<div class="ictl"><button data-act="ans">解答を終えた・答え合わせ</button><button data-act="study" class="small">答えを見て学ぶ</button><span class="gr">' + GR.map(([gv, gl]) => '<button class="gbtn g' + gv + (g === gv ? ' on' : '') + '" data-g="' + gv + '">' + gl + '</button>').join('') + '</span>' + Study.reasonHTML(key, st.run) + '<button data-act="history" class="small">記録</button><button data-act="scratch" class="small">✎ 書く</button></div><div class="study-record-note">' + Study.noteHTML(key) + '</div>' +
      '<div class="scratch" hidden><div class="sc-tools"><button data-sc="undo">戻す</button><button data-sc="clear">全消し</button><button data-sc="more">＋</button></div></div></div>';
  }
  /* after a block element is in the DOM: highlights, table wrappers, ink, anchored notes, scratch pads */
  function afterInsert(u, c, e) {
    if (c.t === 'a') (c.answerKeys || []).forEach(key => Study.seen(key));
    if (c.vocab) u.items.filter(it => it.ci === c.ci).forEach(it => Study.seen(it.key));
    const body = $('.cbody[data-ci]', e);
    if (body) {
      $$('table', e).forEach(t => { if (!t.parentElement.classList.contains('twrap')) { const w = document.createElement('div'); w.className = 'twrap'; t.parentNode.insertBefore(w, t); w.appendChild(t); } });
      const highlights = HL.apply(body, u.ukey, c.ci);
      if (highlights.skipped) e.appendChild(el('<div class="study-legacy sm">本文の変更で位置を確認できないマーカー ' + highlights.skipped + '件は非表示にしています。保存データは残っています。</div>'));
      attachBlockInk(u, c, e);
      // restore scratch pads that have ink
      $$('.item', e).forEach(item => { const sk = item.dataset.key; const d = inkDoc(u.ukey).scratch[sk]; if (d && d.strokes && d.strokes.length) openScratch(u, item, true); });
    }
    if (c.t !== 'h3') {
      const anchored = Notes.forUnit(u.ukey).filter(n => n.ci === c.ci);
      if (anchored.length) { const w = el('<div class="notes-wrap note-block"></div>'); w.innerHTML = anchored.map(n => Notes.render(n)).join(''); e.after(w); }
    }
  }
  function attachBlockInk(u, c, e) {
    const source = JSON.stringify({ layout: 'study-2026-v3', t: c.t, title: c.title, q: c.q, a: c.a, html: c.html, items: c.items, context: c.context, parts: c.parts, kanji: c.kanji });
    let hash = 2166136261; for (let i = 0; i < source.length; i++) hash = Math.imul(hash ^ source.charCodeAt(i), 16777619);
    const layout = 'v3:' + (hash >>> 0).toString(16);
    const current = () => inkDoc(u.ukey).blocks[c.ci];
    const old = current();
    const incompatible = old && old.layout !== layout && (old.strokes || []).length;
    const archives = old && old.previousLayouts || [];
    if (incompatible || archives.length) {
      const note = el('<div class="study-legacy sm">以前の書き込みは保存されています。本文位置が変わるため重ねずに表示します。<button class="small" data-old-ink>以前の書き込みを見る</button></div>');
      e.appendChild(note);
      $('[data-old-ink]', note).onclick = () => {
        const record = current(), saved = [];
        if (record && record.layout !== layout && (record.strokes || []).length) saved.push(record);
        saved.push(...(record && record.previousLayouts || []));
        const body = el('<div><p class="sm muted">元の座標の書き込みです。改修前の本文位置は再現していません。</p></div>');
        const previews = [];
        saved.forEach((snapshot, index) => {
          let h = 160; (snapshot.strokes || []).forEach(st => { for (let i = 1; i < st.p.length; i += 2) h = Math.max(h, st.p[i] + 25); });
          const view = el('<div class="ink-preview" aria-label="以前の書き込み ' + (index + 1) + '"></div>');
          view.style.width = Math.min(snapshot.w || 700, 700) + 'px'; view.style.maxWidth = '100%';
          view.style.aspectRatio = (snapshot.w || 700) + ' / ' + h;
          body.appendChild(view);
          const copy = JSON.parse(JSON.stringify(snapshot));
          previews.push({ view, copy, width: snapshot.w || 700 });
        });
        openModal('以前の書き込み', body, { wide: true });
        previews.forEach(({ view, copy, width }) => Ink.attach(view, () => copy, () => {}, { fixedW: width }));
      };
    }
    Ink.attach(e, () => { const rec = current(); return rec && rec.layout === layout ? rec : { w: 0, strokes: [] }; }, d => {
      const rec = current();
      if (rec && rec !== d && rec.layout !== layout) {
        d.previousLayouts = (rec.previousLayouts || []).slice();
        if ((rec.strokes || []).length) { const snapshot = Object.assign({}, rec); delete snapshot.previousLayouts; d.previousLayouts.push(snapshot); }
      }
      d.layout = layout; inkDoc(u.ukey).blocks[c.ci] = d; markDirty('ink/' + u.ukey);
    });
  }
  function openScratch(u, item, restore) {
    const sc = $('.scratch', item); if (!sc) return;
    if (!sc.hidden && !restore) { sc.hidden = true; return; }
    sc.hidden = false;
    if (!sc._ink) {
      const sk = item.dataset.key;
      const d = inkDoc(u.ukey).scratch[sk];
      if (d && d.h) sc.style.height = d.h + 'px';
      Ink.attach(sc, () => inkDoc(u.ukey).scratch[sk], dd => { inkDoc(u.ukey).scratch[sk] = dd; dd.h = sc.clientHeight; markDirty('ink/' + u.ukey); }, { always: true });
    }
  }
  function rerenderBlock(ukey, ci) {
    const u = unitByKey(ukey); if (!u || u.ukey !== st.ukey) return;
    const old = $('.cblock[data-ci="' + ci + '"]'); if (!old) return;
    const c = u.content[ci];
    const e = renderBlock(u, c);
    // remove anchored notes block that follows
    if (old.nextElementSibling && old.nextElementSibling.classList.contains('note-block')) old.nextElementSibling.remove();
    old.replaceWith(e); afterInsert(u, c, e);
  }
  function refreshNotes() {
    const box = $('#unit-notes'); if (!box) return;
    const u = unitByKey(st.ukey); if (!u) return;
    const free = Notes.forUnit(u.ukey).filter(n => n.ci == null);
    box.innerHTML = free.map(n => Notes.render(n)).join('') + (free.length ? '' : '');
    // anchored notes: re-render each block's note strip
    $$('.note-block').forEach(x => x.remove());
    $$('.cblock', $('#content')).forEach(e => { const ci = +e.dataset.ci; const anchored = Notes.forUnit(u.ukey).filter(n => n.ci === ci); if (anchored.length) { const w = el('<div class="notes-wrap note-block"></div>'); w.innerHTML = anchored.map(n => Notes.render(n)).join(''); e.after(w); } });
  }
  /* delegated events inside content */
  document.addEventListener('click', e => {
    const content = e.target.closest('#content'); if (!content) return;
    const u = unitByKey(st.ukey); if (!u) return;
    const card = e.target.closest('.cblock');
    const b = e.target.closest('button');
    const kitem = e.target.closest('.kitem');
    if (kitem && !b) { const ka = $('.ka', kitem); if (ka.classList.contains('hid')) { Study.finish(kitem.dataset.key, st.run); Study.seen(kitem.dataset.key); } ka.classList.toggle('hid'); return; }
    if (kitem && b && b.closest('.ka')) { return; }
    if (!b) return;
    const item = e.target.closest('.item, .kitem');
    if (b.dataset.g != null && item) {
      const key = item.dataset.key; const g = +b.dataset.g;
      const attempt = Study.current(key, st.run);
      const result = setGrade(u.subject, key, attempt && attempt.g === g ? null : g, { session: st.run });
      if (result.message) toast(result.message);
      const ng = gradeOf(u.subject, key);
      item.classList.remove('g0', 'g1', 'g2'); if (ng != null) item.classList.add('g' + ng);
      $$('.gbtn', item).forEach(x => x.classList.toggle('on', +x.dataset.g === ng));
      const ia = $('.ia', item); if (ia && ng != null) { ia.hidden = false; Study.seen(key); }
      const ka = $('.ka', item); if (ka && ng != null) { ka.classList.remove('hid'); Study.seen(key); }
      const note = $('.study-record-note', item); if (note) note.innerHTML = Study.noteHTML(key);
      updateScores(u, card);
      return;
    }
    if (b.dataset.act === 'history' && item) { Study.history(item.dataset.key); return; }
    if ((b.dataset.act === 'ans' || b.dataset.act === 'study') && item) {
      const ia = $('.ia', item); if (!ia) return;
      if (ia.hidden) {
        if (b.dataset.act === 'ans') { const done = Study.finish(item.dataset.key, st.run); if (st.mode === 'retest' && done.mode !== 'retest') toast('24時間条件を満たさないため、今回は解き直しです。'); }
        Study.seen(item.dataset.key); ia.hidden = false;
      } else ia.hidden = true;
      return;
    }
    if (b.dataset.act === 'scratch' && item) { openScratch(u, item); return; }
    if (b.dataset.sc) { const sc = b.closest('.scratch'); if (b.dataset.sc === 'undo') sc._ink && sc._ink.undo(); else if (b.dataset.sc === 'clear') sc._ink && sc._ink.clear(); else if (b.dataset.sc === 'more') { sc.style.height = (sc.clientHeight + 120) + 'px'; if (sc._ink) { const sk = item.dataset.key; const d = inkDoc(u.ukey).scratch[sk]; if (d) { d.h = sc.clientHeight; markDirty('ink/' + u.ukey); } sc._ink.render(); } } return; }
    if (b.dataset.act === 'bnote' && card) { Notes.create({ ukey: u.ukey, ci: +card.dataset.ci }); return; }
    if (b.dataset.act === 'showall' && card) { const ias = $$('.ia', card); const anyHidden = ias.some(x => x.hidden) || $$('.ka', card).some(x => x.classList.contains('hid')); if (anyHidden) $$('.item, .kitem', card).forEach(x => Study.seen(x.dataset.key)); ias.forEach(x => x.hidden = !anyHidden); $$('.ka', card).forEach(x => x.classList.toggle('hid', !anyHidden)); b.textContent = anyHidden ? '答えを隠す' : '答えを全部'; return; }
    if (b.dataset.act === 'cards' && card) { const ci = +card.dataset.ci; const items = u.items.filter(it => it.ci === ci); Cards.start(items.map(it => studyCard(it, u.subject)), { title: unitLabel(u) + '　' + (u.content[ci].title || 'カード'), ukey: u.ukey, mode: st.mode, onEnd: () => rerenderBlock(u.ukey, ci) }); return; }
    if (b.dataset.act === 'vcards' && card) { const ci = +card.dataset.ci; const items = u.items.filter(it => it.ci === ci); Cards.start(items.map(it => ({ key: it.key, q: it.q, a: it.a, label: it.label, sid: u.subject, ruby: false })), { title: unitLabel(u) + '　単語カード', ukey: u.ukey, reverse: true, mode: st.mode, onEnd: () => rerenderBlock(u.ukey, ci) }); return; }
  });
  document.addEventListener('change', e => {
    const select = e.target.closest('#content [data-reason]');
    const item = select && select.closest('.item');
    if (item) Study.setReason(item.dataset.key, select.value, st.run);
  });
  function updateScores(u, card) {
    if (!card) return;
    const ci = +card.dataset.ci; const items = u.items.filter(it => it.ci === ci);
    const graded = items.filter(it => gradeOf(u.subject, it.key) != null).length, ok = items.filter(it => gradeOf(u.subject, it.key) === 2).length;
    const sc = $('.exscore', card); if (sc) sc.textContent = '採点 ' + graded + '/' + items.length + '　○ ' + ok;
    const stat = unitStats(u);
    const up = $('.unit-head .uprog'); if (up) { $('.bar i', up).style.width = pct(stat.graded, stat.total) + '%'; $('.num', up).textContent = stat.graded + '/' + stat.total + '問　○' + stat.ok; }
    const opt = $('#sel-unit option[value="' + u.ukey.replace(/"/g, '\\"') + '"]'); if (opt) opt.textContent = statusMark(u) + unitLabel(u);
    if (stat.total && stat.graded === stat.total && !(progOf(u).units[u.ukey] || {}).d) { toast('全問採点ずみ！お疲れさま'); }
  }
  function open(ukey, ci, task) {
    const u = unitByKey(ukey); if (!u) { toast('単元が見つかりません'); return; }
    if (u.ed !== ED.id) App.setEdition(u.ed, true);
    st.sid = u.subject; st.ukey = ukey; st.task = task || null; st.scrollTo = ci == null ? null : ci; st.tab = 'all'; st.onlyNg = false;
    App.show('learn');
    if (ci == null) window.scrollTo(0, 0);
  }
  return { render, open, rerenderBlock, refreshNotes, state: st };
})();
