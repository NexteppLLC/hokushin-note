/* ===== Progress view ===== */
const Progress = (() => {
  function planStats(upToToday) {
    const today = todayISO(); let total = 0, done = 0, all = 0;
    PLAN.days.forEach(d => SUBJ_ORDER.forEach(sk => (d.tasks[sk] || []).forEach(t => { all++; const k = taskKey(d.day, sk, t.code); if (S.plan.done[k]) done++; if (d.date <= today) total++; })));
    return { total, done, all };
  }
  function streak() {
    let n = 0; let d = todayISO();
    const active = dt => { const l = S.plan.log[dt]; return !!(l && ((l.m || 0) > 0 || (l.g || 0) > 0)) || Study.timeTotal(dt, dt) > 0; };
    if (!active(d)) d = addDays(d, -1);
    while (active(d)) { n++; d = addDays(d, -1); }
    return n;
  }
  function render() {
    const main = $('#main');
    const ps = planStats(), history = Study.totals();
    let items = 0, graded = 0, ok = 0, ng = 0, units = 0, unitsDone = 0;
    const per = DATA.subjects.map(s => { const st = subjectStats(s); items += st.items; graded += st.graded; ok += st.ok; ng += st.ng; units += st.units; unitsDone += st.unitsDone; return { s, st }; });
    main.innerHTML = '<h1 class="vh">進捗</h1>' +
      '<div class="stat-grid">' +
        (ps.total ? '<div class="stat"><div class="sl">計画の達成率（今日まで）</div><div class="sv num">' + pct(ps.done, ps.total) + '<small>%</small></div><div class="ss num">' + ps.done + ' / ' + ps.total + ' 項目（全期間 ' + ps.all + '）</div></div>'
                  : '<div class="stat"><div class="sl">計画の達成率</div><div class="sv num">' + pct(ps.done, ps.all) + '<small>%</small></div><div class="ss num">開始前　' + ps.done + ' / ' + ps.all + ' 項目</div></div>') +
        '<div class="stat"><div class="sl">取り組み済みの単元</div><div class="sv num">' + pct(unitsDone, units) + '<small>%</small></div><div class="ss num">' + unitsDone + ' / ' + units + ' 単元</div></div>' +
        '<div class="stat"><div class="sl">問題の進み</div><div class="sv num">' + pct(graded, items) + '<small>%</small></div><div class="ss num">' + graded + ' / ' + items + ' 問を採点</div></div>' +
        '<div class="stat"><div class="sl">最新の自己採点（○の割合）</div><div class="sv num">' + pct(ok, graded) + '<small>%</small></div><div class="ss num">○ ' + ok + '　×△ ' + ng + '</div></div>' +
        '<div class="stat"><div class="sl">連続学習</div><div class="sv num">' + streak() + '<small>日</small></div><div class="ss">予定・採点・実際の学習時間を記録した日</div></div>' +
      '</div>' +
      '<div class="study-summary">' + historyCards(history) + '</div>' +
      '<p class="sm muted">初見・後日再テストは改修後に記録した自己申告・自己採点です。解き直しの○は後日再テストの○に含めません。改修前の記録 ' + history.legacy + '問は保持し、初見・後日再テストの率から除いています。最新の自己採点には改修前の採点も含みます。「取り組み済み」は習得の判定ではありません。</p>' +
      '<h2 class="sh">教科ごと</h2><div class="prog-subj">' + per.map(({ s, st }) => subjCard(s, st)).join('') + '</div>' +
      '<h2 class="sh">実際の学習時間（手入力）</h2><div class="card">' + timePanel() + chart('actual') + '</div>' +
      '<h2 class="sh">完了した予定に設定された時間（直近14日）</h2><div class="card">' + chart('planned') + '<p class="sm muted">予定のチェックに応じた時間です。実際に勉強した時間とは別に表示しています。</p></div>';
    $$('[data-units]').forEach(b => b.onclick = () => openUnits(b.dataset.units));
    $$('[data-weak]').forEach(b => b.onclick = () => openWeak(b.dataset.weak));
    $$('[data-due]').forEach(b => b.onclick = () => openDue(b.dataset.due || null));
    $('#study-time-form').onsubmit = e => { e.preventDefault(); if (Study.addTime($('#study-time-date').value, Number($('#study-time-minutes').value))) { toast('実際の学習時間を記録しました'); render(); } else toast('日付と1〜720分の整数を確認してください。'); };
    $$('[data-time-cancel]').forEach(b => b.onclick = () => { Study.cancelTime(b.dataset.timeCancel); render(); });
  }
  function historyCards(h) {
    const rate = (ok, all) => all ? pct(ok, all) + '%' : '—';
    return '<div><span>初見の○率</span><b>' + rate(h.firstOk, h.first) + '</b><small>○ ' + h.firstOk + ' / ' + h.first + '問</small></div>' +
      '<div><span>後日再テストの○率</span><b>' + rate(h.retestOk, h.retest) + '</b><small>○ ' + h.retestOk + ' / ' + h.retest + '回</small></div>' +
      '<div><span>復習時期の問題</span><b>' + h.due + '問</b><button data-due="">後日再テストを開く</button></div>';
  }
  function timePanel() {
    const today = todayISO(), minutes = Study.timeTotal(today, today);
    const recent = (S.plan.studyTime || []).filter(x => !x.cancelledAt).slice(-5).reverse();
    return '<p>今日の実際の学習時間：<b class="num">' + minutes + '分</b>（手入力）</p>' +
      '<form id="study-time-form" class="row"><label>日付 <input type="date" id="study-time-date" required max="' + today + '" value="' + today + '"></label><label>時間 <input type="number" id="study-time-minutes" min="1" max="720" step="1" required placeholder="分" style="width:90px"></label><button type="submit" class="primary">記録する</button></form>' +
      '<div class="study-time-recent">' + recent.map(x => '<span>' + esc(fmtDate(x.date)) + ' ' + x.minutes + '分 <button class="small" data-time-cancel="' + esc(x.id) + '">取り消す</button></span>').join('') + '</div>';
  }
  function subjCard(s, st) {
    const row = (l, a, b, cls) => '<div class="pr"><span>' + l + '</span><span class="bar ' + (cls || s.key) + '"><i style="width:' + pct(a, b) + '%"></i></span><span class="v num">' + pct(a, b) + '%</span></div>';
    return '<div class="ps"><div class="psh"><span class="dot" style="background:var(--c-' + s.key + ')"></span>' + esc(s.name) + '<span class="grow"></span><span class="sm muted num">×△ ' + st.ng + '</span></div>' +
      row('取り組み済みの単元', st.unitsDone, st.units) + row('問題の進み', st.graded, st.items) + row('最新の自己採点', st.ok, st.graded, 'ok') +
      '<div class="psb"><button data-units="' + s.id + '">単元一覧</button><button data-weak="' + s.id + '">直しリスト（' + st.ng + '）</button><button data-due="' + s.id + '">後日再テスト（' + Study.totals([s]).due + '）</button></div></div>';
  }
  function chart(kind) {
    const today = todayISO(); const days = []; let max = 0;
    for (let i = 13; i >= 0; i--) { const d = addDays(today, -i); const m = kind === 'actual' ? Study.timeTotal(d, d) : ((S.plan.log[d] && S.plan.log[d].m) || 0); days.push({ d, m }); if (m > max) max = m; }
    const top = Math.max(60, Math.ceil(max / 60) * 60);
    return '<div class="chart" role="img" aria-label="直近14日の学習時間">' + days.map((x, i) => '<div class="cbar ' + (x.d === today ? 'today' : '') + '" title="' + fmtDate(x.d) + '：' + x.m + '分"><span class="cv">' + ((x.m && (x.m === max || x.d === today)) ? x.m : '') + '</span><i style="height:' + pct(x.m, top) + '%"></i></div>').join('') + '</div>' +
      '<div class="chart-x">' + days.map(x => '<span>' + +x.d.slice(8) + '</span>').join('') + '</div><div class="sm muted" style="margin-top:6px">単位：分。目盛りの上限 ' + top + ' 分。</div>';
  }
  function openUnits(sid) {
    const s = SUBJ[sid];
    let html = '<div class="ulist">'; let chap = null;
    s.units.forEach(u => { if (u.chapter !== chap) { chap = u.chapter; html += '<div class="chap">' + esc(chap || '') + '</div>'; } const st = unitStats(u);
      html += '<div class="ul" data-u="' + esc(u.ukey) + '"><span class="code">' + esc(u.code || '') + '</span><span>' + esc(u.title) + '</span><span class="bar ' + s.key + '">' + (st.total ? '<i style="width:' + pct(st.graded, st.total) + '%"></i>' : '') + '</span><span class="st">' + (st.done ? '<span class="pill ok">取り組み済み</span>' : (st.total ? '<span class="num">' + st.graded + '/' + st.total + '</span>' : (st.viewed ? '<span class="pill">閲覧</span>' : ''))) + '</span></div>'; });
    html += '</div>';
    const m = openModal(s.name + '　単元一覧', html);
    $$('.ul', m).forEach(x => x.onclick = () => { m.close(); Learn.open(x.dataset.u); });
  }
  function weakItems(sid) {
    const out = [];
    const subs = sid ? [SUBJ[sid]] : DATA.subjects;
    subs.forEach(s => { const items = progOf(s).items; s.units.forEach(u => u.items.forEach(it => { const r = items[it.key]; if (r && Study.validGrade(r.g) && r.g < 2) out.push({ it, u, s, r }); })); });
    out.sort((a, b) => a.r.g - b.r.g || b.r.t - a.r.t);
    return out;
  }
  function openWeak(sid) {
    const list = weakItems(sid);
    const s = sid ? SUBJ[sid] : null;
    const body = el('<div class="weak"></div>');
    const run = Study.session('review', 'weak');
    function draw() {
      const l = weakItems(sid);
      if (!l.length) { body.innerHTML = '<div class="emptybox">×・△の問題はありません。よくできています！</div>'; return; }
      body.innerHTML = '<div class="row" style="margin-bottom:8px"><span class="muted sm">× を先に、あとは新しい順。答えを確認して解き直します。この場の採点は「解き直し」として記録します。</span><span class="grow"></span><button class="primary" data-a="cards">カードで解き直す（' + l.length + '問）</button></div>' +
        l.slice(0, 200).map(({ it, u, s: ss, r }) => '<div class="witem item ' + 'g' + r.g + '" data-key="' + esc(it.key) + '" data-sid="' + ss.id + '"><div class="wh"><span class="pill ' + ss.key + '">' + esc(ss.short) + '</span><span class="lnk" data-u="' + esc(u.ukey) + '" data-ci="' + it.ci + '">' + esc(unitLabel(u)) + '</span><span>' + esc(it.label) + (it.n ? ' ' + it.n : '') + '</span><span class="grow"></span><span>' + (r.g === 0 ? '×' : '△') + '</span></div>' +
          '<div class="cbody ' + (ss.ruby ? (S.settings.ruby ? 'ruby' : 'noruby') : '') + '" style="margin-top:4px">' + questionContextHTML(it.context, it.contextTitle) + it.q + '<div class="ia" hidden>' + (it.a || '') + '</div></div>' +
          '<div class="study-record-note">' + Study.noteHTML(it.key) + '</div><div class="ictl" style="margin-left:0"><button data-act="ans">答えを見て学ぶ</button><span class="gr"><button class="gbtn g2" data-g="2">○</button><button class="gbtn g1 ' + (r.g === 1 ? 'on' : '') + '" data-g="1">△</button><button class="gbtn g0 ' + (r.g === 0 ? 'on' : '') + '" data-g="0">×</button></span></div></div>').join('') + (l.length > 200 ? '<div class="emptybox">200件まで表示</div>' : '');
      $('[data-a="cards"]', body).onclick = () => Cards.start(l.map(({ it, s: ss }) => Object.assign(studyCard(it, ss.id), { label: ss.short + '・' + studyCard(it, ss.id).label })), { title: (s ? s.name : '全教科') + '　直しカード', mode: 'review', onEnd: draw });
      $$('.lnk', body).forEach(x => x.onclick = () => { m.close(); Learn.open(x.dataset.u, +x.dataset.ci); });
      $$('[data-act="ans"]', body).forEach(b => b.onclick = () => { const ia = $('.ia', b.closest('.witem')); if (ia.hidden) Study.seen(b.closest('.witem').dataset.key); ia.hidden = !ia.hidden; });
      $$('[data-g]', body).forEach(b => b.onclick = () => { const w = b.closest('.witem'); setGrade(w.dataset.sid, w.dataset.key, +b.dataset.g, { session: run }); if (+b.dataset.g === 2) { w.style.opacity = '.4'; setTimeout(draw, 350); } else draw(); });
    }
    const m = openModal((s ? s.name : '全教科') + '　直しリスト', body, { wide: true, onClose: () => { if (App.view === 'progress') render(); if (App.view === 'learn') Learn.render(); } });
    draw();
  }
  function openDue(sid) {
    const list = Study.dueItems(sid), subject = sid ? SUBJ[sid] : null;
    const body = el('<div class="study-due"></div>');
    const title = (subject ? subject.name : '全教科') + '　後日再テスト';
    function draw() {
      const due = Study.dueItems(sid), batch = due.slice(0, 20);
      body.innerHTML = '<p>' + (due.length ? '復習時期の問題は ' + due.length + '問です。20問ずつ取り組めます。' : '今は復習時期の問題はありません。') + '</p><p class="sm muted">前回の学習から最低24時間あけます。後日の○が続くと次の復習は1日→3日→7日へ進みます。同日の解き直しで間隔は進みません。</p>' +
        (batch.length ? '<button class="primary" data-a="retest">後日再テスト（' + batch.length + '問）</button>' : '') +
        due.slice(0, 100).map(({ it, u, s, review }) => '<div class="study-due-row"><span class="pill ' + s.key + '">' + esc(s.short) + '</span><span>' + esc(unitLabel(u)) + ' ' + esc(it.numberLabel || it.n || '') + '</span><small>' + review.days + '日後の復習</small><button class="small" data-history="' + esc(it.key) + '">記録</button></div>').join('');
      const start = $('[data-a="retest"]', body); if (start) start.onclick = () => Cards.start(batch.map(({ it, s }) => studyCard(it, s.id)), { title, mode: 'retest', onEnd: draw });
      $$('[data-history]', body).forEach(b => b.onclick = () => Study.history(b.dataset.history));
    }
    openModal(title, body, { wide: true, onClose: () => { if (App.view === 'progress') render(); } }); draw();
  }
  return { render, openWeak, openUnits, weakItems, openDue };
})();
