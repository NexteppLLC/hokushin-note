/* ===== flashcards (カード練習) ===== */
const Cards = (() => {
  function start(items, opts) {
    opts = opts || {};
    if (!items.length) { toast('カードにする問題がありません'); return; }
    const order = items.slice();
    if (opts.shuffle) order.sort(() => Math.random() - 0.5);
    let i = 0, revealed = false, res = { 2: 0, 1: 0, 0: 0 }, again = [], reverse = false;
    let mode = opts.mode || 'auto', run = Study.session(mode, 'cards'), grade = null;
    const scratches = {};
    const body = el('<div class="fc"></div>');
    const m = openModal(opts.title || 'カード練習', body, { sticky: true, onClose: () => { if (opts.onEnd) opts.onEnd(); if (typeof Progress !== 'undefined' && App.view === 'progress') Progress.render(); } });
    function draw() {
      if (i >= order.length) {
        body.innerHTML = '<div class="fc-done"><div class="big">' + res[2] + ' / ' + order.length + '</div><div>○ ' + res[2] + '　△ ' + res[1] + '　× ' + res[0] + '</div><p class="muted">今回の自己採点です。後日再テストは24時間以上あけて取り組みます。</p>' +
          '<div class="row" style="justify-content:center;margin-top:12px">' + (again.length ? '<button class="primary" data-a="again">×△を今すぐ解き直す（' + again.length + '問）</button>' : '') + '<button data-a="close">閉じる</button></div></div>';
        $('[data-a="close"]', body).onclick = () => m.close();
        const ag = $('[data-a="again"]', body); if (ag) ag.onclick = () => { order.splice(0, order.length, ...again); again = []; i = 0; res = { 2: 0, 1: 0, 0: 0 }; mode = 'review'; run = Study.session(mode, 'cards'); grade = null; revealed = false; draw(); };
        return;
      }
      const it = order[i], ruby = it.ruby ? (S.settings.ruby ? 'ruby' : 'noruby') : '';
      const f = reverse ? it.a : it.q, b = reverse ? it.q : it.a;
      if (reverse) Study.seen(it.key); // The usual answer is visible even without grading.
      const attempt = Study.current(it.key, run), completed = Study.completion(it.key, run);
      const activeMode = attempt ? attempt.mode : completed ? completed.mode : Study.modeFor(it.key, run, Date.now()).mode;
      body.innerHTML = '<div class="fc-prog"><span class="num">' + (i + 1) + ' / ' + order.length + '</span><span class="bar grow"><i style="width:' + pct(i, order.length) + '%"></i></span>' +
        '<select data-a="mode" aria-label="練習の種類">' + Study.modeOptions(mode) + '</select>' +
        (opts.reverse ? '<button class="small" data-a="flip">' + (reverse ? '意味→単語' : '単語→意味') + '</button>' : '') + '<button class="small" data-a="shuffle"' + (grade != null ? ' disabled' : '') + '>シャッフル</button></div>' +
        '<p class="sm muted">' + Study.help + '</p>' +
        '<div class="fc-context cbody ' + ruby + '">' + questionContextHTML(it.context, it.contextTitle) + '</div>' +
        '<div class="fc-card cbody ' + ruby + '"><div class="lab">' + esc(it.label || '') + '</div><div class="ff">' + f + '</div>' +
        '<div class="fa" ' + (revealed ? '' : 'hidden') + '>' + (b || '<span class="muted">（解答なし）</span>') + '</div></div>' +
        '<div class="study-record-note">今回：' + esc(Study.MODES[activeMode]) + '（自己申告） ' + Study.noteHTML(it.key) + '</div>' +
        '<div class="fc-scratch inkhost"><div class="sc-tools"><button data-sc="clear">消す</button></div></div>' +
        '<div class="fc-ctl">' + (revealed ? '<span class="gr">' + [[2, '○'], [1, '△'], [0, '×']].map(([g, label]) => '<button class="gbtn g' + g + (grade === g ? ' on' : '') + '" data-g="' + g + '">' + label + '</button>').join('') + '</span>' + Study.reasonHTML(it.key, run) + (grade == null ? '' : '<button class="primary" data-a="next">次へ</button>') :
          '<button class="primary" data-a="finish">解答を終えた・答え合わせ</button><button data-a="study">答えを見て学ぶ</button>') + '<button class="small" data-a="history">記録</button></div>';
      const scratchKey = run.id + ':' + i + ':' + (it.key || 'free');
      Ink.attach($('.fc-scratch', body), () => scratches[scratchKey], d => { scratches[scratchKey] = d; }, { always: true });
      $('[data-sc="clear"]', body).onclick = () => $('.fc-scratch', body)._ink.clear();
      const reveal = finish => { if (finish) Study.finish(it.key, run); Study.seen(it.key); revealed = true; draw(); };
      const finish = $('[data-a="finish"]', body); if (finish) finish.onclick = () => reveal(true);
      const study = $('[data-a="study"]', body); if (study) study.onclick = () => reveal(false);
      $$('[data-g]', body).forEach(bt => bt.onclick = () => {
        const result = setGrade(it.sid, it.key, +bt.dataset.g, { session: run });
        grade = +bt.dataset.g; if (result.message) toast(result.message); draw();
      });
      const next = $('[data-a="next"]', body); if (next) next.onclick = () => { res[grade]++; if (grade < 2) again.push(it); i++; revealed = false; grade = null; draw(); };
      const reason = $('[data-reason]', body); if (reason) reason.onchange = e => Study.setReason(it.key, e.target.value, run);
      $('[data-a="history"]', body).onclick = () => Study.history(it.key);
      $('[data-a="mode"]', body).onchange = e => { mode = reverse ? 'review' : e.target.value; run = Study.session(mode, 'cards'); revealed = false; grade = null; draw(); };
      $('[data-a="shuffle"]', body).onclick = () => { const rest = order.slice(i).sort(() => Math.random() - 0.5); order.splice(i, rest.length, ...rest); revealed = false; grade = null; draw(); };
      const fl = $('[data-a="flip"]', body); if (fl) fl.onclick = () => { reverse = !reverse; if (reverse) mode = 'review'; revealed = false; grade = null; run = Study.session(mode, 'cards'); draw(); };
    }
    draw();
  }
  return { start };
})();

/* ===== per-unit handwriting notebook (自由帳) ===== */
const Notebook = (() => {
  const PW = 1000, PH = 1300;
  function open(u) {
    const doc = S.nb[u.ukey] = S.nb[u.ukey] || { pages: [{ strokes: [] }] };
    let page = 0;
    const body = el('<div class="nb-wrap"></div>');
    const m = openModal('手書きノート　' + unitLabel(u), body, { wide: true, sticky: true, footer: '<button data-a="prev">‹ 前のページ</button><span class="num" data-a="pg"></span><button data-a="next">次のページ ›</button><button data-a="add">＋ ページ追加</button><span class="grow"></span><button data-a="undo">↶ 戻す</button><button data-a="clear">このページを消す</button><button data-a="tools" class="primary">ペン設定</button>', onClose: () => { if (App.view === 'learn') Learn.render(); } });
    $('.mb', m).style.padding = '0'; $('.mb', m).style.display = 'flex'; $('.mb', m).style.flexDirection = 'column';
    const wasPen = Ink.isPen();
    function draw() {
      body.innerHTML = '';
      const pg = el('<div class="nb-page"></div>');
      const w = Math.min(body.clientWidth - 20, 900); pg.style.width = w + 'px'; pg.style.height = Math.round(w * PH / PW) + 'px';
      body.appendChild(pg);
      Ink.attach(pg, () => doc.pages[page], d => { doc.pages[page] = d; markDirty('nb/' + u.ukey); }, { always: true, fixedW: PW });
      $('[data-a="pg"]', m).textContent = (page + 1) + ' / ' + doc.pages.length;
    }
    draw();
    $('[data-a="prev"]', m).onclick = () => { if (page > 0) { page--; draw(); } };
    $('[data-a="next"]', m).onclick = () => { if (page < doc.pages.length - 1) { page++; draw(); } };
    $('[data-a="add"]', m).onclick = () => { doc.pages.push({ strokes: [] }); page = doc.pages.length - 1; markDirty('nb/' + u.ukey); draw(); };
    $('[data-a="undo"]', m).onclick = () => { const pg = $('.nb-page', body); pg._ink.undo(); };
    $('[data-a="clear"]', m).onclick = async () => { if (await confirmBox('このページの書き込みを全部消しますか？')) { const pg = $('.nb-page', body); pg._ink.clear(); } };
    $('[data-a="tools"]', m).onclick = () => { const bar = $('#pen-toolbar'); bar.hidden = !bar.hidden; if (!bar.hidden) Ink.renderBar(); };
    // pen toolbar (colors/width) is useful here too
    $('#pen-toolbar').hidden = false; Ink.renderBar();
    const origClose = m.close;
    m.close = () => { if (!wasPen) $('#pen-toolbar').hidden = true; origClose(); };
    $('.mx', m).onclick = m.close;
  }
  return { open };
})();

/* ===== full-text search ===== */
const Search = (() => {
  let index = null;
  const strip = h => String(h || '').replace(/<rt>.*?<\/rt>/g, '').replace(/<\/(?:p|li|tr|td|th|div|h\d|br|table|ul|ol)>/g, ' ').replace(/<br\s*\/?>/g, ' ').replace(/<[^>]+>/g, '').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/\s+/g, ' ').trim();
  function build() {
    index = [];
    DATA.subjects.forEach(s => s.units.forEach(u => u.content.forEach(c => {
      let text = '';
      if (c.t === 'ex') text = strip(c.q) + ' ' + strip(c.a) + ' ' + (c.items ? c.items.map(it => strip(it.q) + ' ' + strip(it.a)).join(' ') : '') + (c.kanji ? c.kanji.map(p => p.items.map(it => strip(it.q) + ' ' + it.a).join(' ')).join(' ') : '');
      else if (c.t === 'h3') text = c.title;
      else text = (c.title || '') + ' ' + strip(c.html);
      if (text.trim()) index.push({ ukey: u.ukey, ci: c.ci, text, sid: s.id });
    })));
    index.ed = ED.id;
  }
  function open(q0) {
    if (!index || index.ed !== ED.id) build();
    const body = el('<div><div class="row"><input type="search" id="q" placeholder="例：オームの法則、関ヶ原、不定詞" style="flex:1" value="' + esc(q0 || '') + '"><select id="qs"><option value="">全教科</option>' + DATA.subjects.map(s => '<option value="' + s.id + '">' + esc(s.name) + '</option>').join('') + '</select></div><div class="search-res" id="res"><div class="emptybox">キーワードを入力してください（2文字以上）</div></div></div>');
    const m = openModal('教材を検索', body, { sticky: false });
    const run = () => {
      const q = $('#q', body).value.trim(); const sid = $('#qs', body).value; const res = $('#res', body);
      if (q.length < 2) { res.innerHTML = '<div class="emptybox">キーワードを入力してください（2文字以上）</div>'; return; }
      const ql = q.toLowerCase(); const hits = [];
      for (const e of index) { if (sid && e.sid !== sid) continue; const p = e.text.toLowerCase().indexOf(ql); if (p >= 0) { hits.push({ e, p }); if (hits.length >= 80) break; } }
      if (!hits.length) { res.innerHTML = '<div class="emptybox">見つかりませんでした</div>'; return; }
      res.innerHTML = hits.map(({ e, p }) => { const u = unitByKey(e.ukey); const s = SUBJ[e.sid]; const a = Math.max(0, p - 30), b = Math.min(e.text.length, p + q.length + 50); const snip = esc(e.text.slice(a, p)) + '<b>' + esc(e.text.slice(p, p + q.length)) + '</b>' + esc(e.text.slice(p + q.length, b));
        return '<div class="sr-item" data-u="' + esc(e.ukey) + '" data-ci="' + e.ci + '"><div class="sm"><span class="pill ' + s.key + '">' + esc(s.name) + '</span> ' + esc(unitLabel(u)) + '</div><div class="snip">' + (a > 0 ? '…' : '') + snip + (b < e.text.length ? '…' : '') + '</div></div>'; }).join('') + (hits.length >= 80 ? '<div class="emptybox">80件まで表示</div>' : '');
      $$('.sr-item', res).forEach(x => x.onclick = () => { m.close(); Learn.open(x.dataset.u, +x.dataset.ci); });
    };
    let t; $('#q', body).addEventListener('input', () => { clearTimeout(t); t = setTimeout(run, 200); });
    $('#qs', body).onchange = run;
    if (q0) run();
    setTimeout(() => $('#q', body).focus(), 50);
  }
  return { open };
})();
