/* ===== Today view: the daily plan ===== */
const Today = (() => {
  const st = { date: null, showCal: false, ed: null };
  let start = PLAN.start, testDay = PLAN.test_day;
  function dayOf(date) { return DAY_BY_DATE[date] || null; }
  function render() {
    const today = todayISO();
    start = PLAN.start; testDay = PLAN.test_day;
    if (st.ed !== ED.id) { st.ed = ED.id; st.date = null; }
    if (!st.date) st.date = today < start ? start : (today > PLAN.days[PLAN.days.length - 1].date ? PLAN.days[PLAN.days.length - 1].date : today);
    const day = dayOf(st.date);
    const main = $('#main');
    const toTest = diffDays(today, testDay);
    let banner = '';
    if (today < start) banner = '<div class="banner">学習計画は <b>' + fmtDate(start) + '（' + wdOf(start) + '）</b> からスタート（あと' + diffDays(today, start) + '日）。それまでに「学ぶ」で各教科の「0 この教材の使い方」と、英語の <b>G0 スタート診断テスト</b> をやっておくとスムーズです。</div>';
    else if (today === testDay) banner = '<div class="banner">今日は' + esc(ED.name) + '当日！ 落ち着いて。持ち物・時間を確認して、直しノート（進捗 → 直しリスト）をさっと見直そう。</div>';
    else if (today > testDay) banner = '<div class="banner">' + fmtDate(testDay) + 'の' + esc(ED.name) + 'はおつかれさま。「進捗」で全体をふり返り、× の問題を解き直して次につなげよう。' + (EDITIONS.indexOf(ED) < EDITIONS.length - 1 ? '次の教材セットは画面上の「教材セット」から選べます。' : '') + '</div>';
    const late = lateTasks(today);
    main.innerHTML = '<div class="card">' +
      '<div class="today-head"><div><div class="today-date">' + fmtDate(st.date) + '（' + wdOf(st.date) + '）' + (day ? '<span class="dn">Day ' + day.day + ' / ' + PLAN.days.length + (day.is_holiday ? '　休日 8時間' : '　平日 4時間') + (day.holiday ? '　' + esc(day.holiday) : '') + '</span>' : '') + '</div>' +
      (day && day.note ? '<div class="today-note">' + esc(day.note) + '</div>' : '') + '</div>' +
      '<div class="today-nav"><button class="icon" data-nav="-1" aria-label="前日">‹</button><button data-nav="0">今日</button><button class="icon" data-nav="1" aria-label="翌日">›</button><button data-nav="cal" class="' + (st.showCal ? 'primary' : '') + '">カレンダー</button></div></div>' +
      (day ? (() => { const ds = dayStats(day); return '<div class="today-prog"><div class="bar ok"><i style="width:' + pct(ds.tmDone, ds.tm) + '%"></i></div><div class="num sm"><b>' + ds.done + '/' + ds.total + '</b> 項目　' + ds.tmDone + '/' + ds.tm + ' 分</div></div>'; })() : '') +
      (st.showCal ? calendar() : '') +
      '</div>' + banner +
      (day ? '<div class="subj-grid">' + SUBJ_ORDER.map(sk => subjCard(day, sk)).join('') + '</div>' : '<div class="emptybox">この日は計画の範囲外です</div>') +
      (late.length ? '<details class="late"><summary>前日までの未完了（' + late.length + '件）</summary><div class="card" style="padding:4px 8px">' + late.map(t => taskRow(t.day, t.sk, t.task, true)).join('') + '</div></details>' : '') +
      '<div class="card" style="margin-top:12px"><div class="row"><span class="sm muted">' + esc(ED.name) + '（' + fmtDate(testDay) + '）まで</span><b class="num" style="font-size:22px;color:var(--ai)">' + (toTest >= 0 ? toTest + ' 日' : '終了') + '</b><span class="grow"></span>' + weekSummary(today) + '</div></div>';
    bind(day);
  }
  function weekSummary(today) {
    let m = 0, d = 0; for (let i = 0; i < 7; i++) { const dt = addDays(today, -i); const l = S.plan.log[dt]; if (l && l.m) { m += l.m; d++; } }
    return '<span class="sm muted">この7日間：学習 ' + d + ' 日・' + m + ' 分（完了した予定の合計）</span>';
  }
  function calendar() {
    const today = todayISO();
    let html = '<div class="cal">';
    const first = PLAN.days[0].date; const [y, mo, dd] = first.split('-').map(Number); const wd = new Date(y, mo - 1, dd).getDay();
    for (let i = 0; i < wd; i++) html += '<span></span>';
    PLAN.days.forEach(d => { const ds = dayStats(d); html += '<button class="cd ' + (d.is_holiday ? 'hol' : '') + (d.date === st.date ? ' sel' : '') + (d.date === today ? ' today' : '') + '" data-date="' + d.date + '"><div class="d">' + +d.date.slice(8) + '<span class="dy"> ' + d.weekday + '</span></div><div class="dy">Day' + d.day + '</div><div class="cb"><i style="width:' + pct(ds.done, ds.total) + '%"></i></div></button>'; });
    html += '<button class="cd test" data-date="' + testDay + '"><div class="d">' + +testDay.slice(8) + ' <span class="dy">' + wdOf(testDay) + '</span></div><div class="dy">試験当日</div></button></div>';
    return html;
  }
  function subjCard(day, sk) {
    const s = SUBJ_BY_KEY[sk]; const tasks = day.tasks[sk] || [];
    const tm = tasks.reduce((a, t) => a + t.minutes, 0);
    return '<div class="subj-card ' + sk + '"><div class="sc-head"><span class="pill ' + sk + '">' + esc(s.short) + '</span><span class="sname">' + esc(s.name) + '</span><span class="smin num">' + tm + '分</span></div>' + tasks.map(t => taskRow(day, sk, t, false)).join('') + '</div>';
  }
  function taskRow(day, sk, t, showDay) {
    const k = taskKey(day.day, sk, t.code); const done = !!S.plan.done[k];
    const r = resolveTask(sk, t.code);
    return '<div class="task ' + (done ? 'done' : '') + '" data-k="' + k + '" data-day="' + day.day + '" data-sk="' + sk + '" data-code="' + esc(t.code) + '" data-min="' + t.minutes + '" data-date="' + day.date + '">' +
      '<button class="chk" aria-label="完了"><i>' + (done ? '✓' : '') + '</i></button>' +
      '<div><div class="tt"><span class="code">' + (showDay ? '<span class="pill ' + sk + '">' + esc(SUBJ_BY_KEY[sk].short) + '</span> Day' + day.day + ' ' : '') + esc(t.code) + '</span>' + esc(t.title) + '</div><div class="tm num">' + t.minutes + '分' + (r.review ? '　（直し）' : '') + '</div></div>' +
      '<button class="open" data-open="1">' + (r.unit ? '開く ›' : '直しリスト ›') + '</button></div>';
  }
  function lateTasks(today) {
    const out = [];
    PLAN.days.forEach(d => { if (d.date >= today || d.date >= st.date) return; SUBJ_ORDER.forEach(sk => (d.tasks[sk] || []).forEach(t => { if (!S.plan.done[taskKey(d.day, sk, t.code)]) out.push({ day: d, sk, task: t }); })); });
    return out.slice(-40);
  }
  function bind(day) {
    $$('[data-nav]').forEach(b => b.onclick = () => {
      const v = b.dataset.nav;
      if (v === 'cal') { st.showCal = !st.showCal; render(); return; }
      if (v === '0') { const t = todayISO(); st.date = t < start ? start : t; render(); return; }
      const nd = addDays(st.date, +v); if (DAY_BY_DATE[nd] || nd === testDay) { st.date = nd; render(); }
    });
    $$('.cal .cd').forEach(b => b.onclick = () => { st.date = b.dataset.date; render(); });
    bindTasks($('#main'), render);
  }
  /** wire up .task rows inside root; onChange is called after a check toggles */
  function bindTasks(root, onChange) {
    $$('.task', root).forEach(row => {
      const k = row.dataset.k, sk = row.dataset.sk, code = row.dataset.code, min = +row.dataset.min, date = row.dataset.date, dnum = +row.dataset.day;
      $('.chk', row).onclick = () => {
        if (S.plan.done[k]) { delete S.plan.done[k]; S.plan.log[date] && (S.plan.log[date].m = Math.max(0, (S.plan.log[date].m || 0) - min)); }
        else { S.plan.done[k] = Date.now(); S.plan.log[date] = S.plan.log[date] || { m: 0, g: 0 }; S.plan.log[date].m = (S.plan.log[date].m || 0) + min; }
        markDirty('plan/main'); onChange(row);
      };
      $('[data-open]', row).onclick = () => {
        const r = resolveTask(sk, code); const dObj = PLAN.days[dnum - 1];
        const t = (dObj.tasks[sk] || []).find(x => x.code === code);
        if (r.unit) Learn.open(r.unit.ukey, null, { day: dnum, sk, code, title: t.title, minutes: min, date });
        else Progress.openWeak(SUBJ_BY_KEY[sk].id);
      };
    });
  }
  return { render, state: st, taskRow, bindTasks, dayOf };
})();
