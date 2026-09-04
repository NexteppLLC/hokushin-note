/* ===== Schedule view: the whole 34-day plan on one page ===== */
const Schedule = (() => {
  const st = { filter: 'all', compact: false };
  function weekOf(date) { // Monday-based week index from plan start
    return Math.floor(diffDays(PLAN.start, date) / 7);
  }
  function render() {
    const main = $('#main');
    const today = todayISO();
    // totals
    const tot = {}; SUBJ_ORDER.forEach(sk => tot[sk] = { m: 0, d: 0, n: 0, nd: 0 });
    let daysDone = 0;
    PLAN.days.forEach(d => { const ds = dayStats(d); if (ds.total && ds.done === ds.total) daysDone++; SUBJ_ORDER.forEach(sk => (d.tasks[sk] || []).forEach(t => { tot[sk].m += t.minutes; tot[sk].n++; if (S.plan.done[taskKey(d.day, sk, t.code)]) { tot[sk].d += t.minutes; tot[sk].nd++; } })); });
    const allM = SUBJ_ORDER.reduce((a, k) => a + tot[k].m, 0), allD = SUBJ_ORDER.reduce((a, k) => a + tot[k].d, 0);
    const first = PLAN.days[0], last = PLAN.days[PLAN.days.length - 1];
    let html = '<h1 class="vh">全日程表　<span class="muted" style="font-size:14px;font-weight:500">' + esc(ED.name) + '：' + fmtDate(first.date) + '（' + first.weekday + '）〜' + fmtDate(last.date) + '（' + last.weekday + '）の' + PLAN.days.length + '日間・試験 ' + fmtDate(PLAN.test_day) + '（' + wdOf(PLAN.test_day) + '）</span></h1>' +
      '<div class="card"><div class="row" style="gap:14px">' +
        '<div><div class="sm muted">計画全体</div><div class="num" style="font-family:var(--font-ui);font-size:22px;font-weight:700;color:var(--ai)">' + Math.round(allM / 60) + '<small class="muted" style="font-size:13px"> 時間</small> <span class="muted sm">（完了 ' + Math.round(allD / 60 * 10) / 10 + ' 時間・' + pct(allD, allM) + '%）</span></div></div>' +
        '<div><div class="sm muted">終えた日</div><div class="num" style="font-family:var(--font-ui);font-size:22px;font-weight:700;color:var(--ai)">' + daysDone + '<small class="muted" style="font-size:13px"> / ' + PLAN.days.length + ' 日</small></div></div>' +
        '<span class="grow"></span>' +
        SUBJ_ORDER.map(sk => '<div class="sm" style="min-width:110px"><span class="pill ' + sk + '">' + esc(SUBJ_BY_KEY[sk].short) + '</span> <span class="num">' + Math.round(tot[sk].m / 60 * 10) / 10 + 'h</span><div class="bar ' + sk + '" style="margin-top:4px"><i style="width:' + pct(tot[sk].d, tot[sk].m) + '%"></i></div><div class="muted num" style="font-size:11px">' + tot[sk].nd + '/' + tot[sk].n + ' 項目</div></div>').join('') +
      '</div>' +
      '<div class="row" style="margin-top:10px"><div class="seg" id="sc-filter">' + [['all', 'すべて'], ['todo', '未完了だけ'], ['future', '今日から']].map(([k, l]) => '<button data-f="' + k + '" class="' + (st.filter === k ? 'active' : '') + '">' + l + '</button>').join('') + '</div>' +
        '<button id="sc-today">今日へ</button><span class="grow"></span><span class="sm muted">チェックで完了、「開く」で教材へ。休日は8時間（青）、平日は4時間の予定です。</span></div></div>';
    let lastWeek = -1;
    PLAN.days.forEach(d => {
      if (st.filter === 'future' && d.date < today) return;
      const ds = dayStats(d);
      if (st.filter === 'todo' && ds.total && ds.done === ds.total) return;
      const w = weekOf(d.date);
      if (w !== lastWeek) { lastWeek = w; const wdays = PLAN.days.filter(x => weekOf(x.date) === w); const wm = wdays.reduce((a, x) => a + dayStats(x).tm, 0); const wd = wdays.reduce((a, x) => a + dayStats(x).tmDone, 0); html += '<h2 class="sh sc-week">第' + (w + 1) + '週　' + fmtDate(wdays[0].date) + '〜' + fmtDate(wdays[wdays.length - 1].date) + '<span class="muted num" style="font-weight:500;margin-left:10px">' + Math.round(wm / 60 * 10) / 10 + ' 時間（完了 ' + pct(wd, wm) + '%）</span></h2>'; }
      const isToday = d.date === today;
      html += '<div class="sday card ' + (d.is_holiday ? 'hol' : '') + (isToday ? ' today' : '') + (ds.total && ds.done === ds.total ? ' alldone' : '') + '" id="sd-' + d.date + '">' +
        '<div class="sd-head"><span class="sd-day">Day ' + d.day + '</span><span class="sd-date">' + fmtDate(d.date) + '（' + d.weekday + '）</span><span class="pill ' + (d.is_holiday ? 'ok' : '') + '">' + (d.is_holiday ? '休日 8h' : '平日 4h') + '</span>' + (d.holiday ? '<span class="pill mid">' + esc(d.holiday) + '</span>' : '') + (isToday ? '<span class="pill" style="background:var(--ai);color:#fff">今日</span>' : '') +
        (d.note ? '<span class="sd-note">' + esc(d.note) + '</span>' : '') + '<span class="grow"></span><span class="sd-prog"><span class="bar ok"><i style="width:' + pct(ds.tmDone, ds.tm) + '%"></i></span><span class="num sm">' + ds.done + '/' + ds.total + '・' + ds.tmDone + '/' + ds.tm + '分</span></span></div>' +
        '<div class="sd-grid">' + SUBJ_ORDER.map(sk => { const tasks = (d.tasks[sk] || []).filter(t => st.filter !== 'todo' || !S.plan.done[taskKey(d.day, sk, t.code)]); if (!tasks.length) return ''; const tm = (d.tasks[sk] || []).reduce((a, t) => a + t.minutes, 0); return '<div class="sd-col ' + sk + '"><div class="sd-sh"><span class="pill ' + sk + '">' + esc(SUBJ_BY_KEY[sk].short) + '</span><span>' + esc(SUBJ_BY_KEY[sk].name) + '</span><span class="muted num">' + tm + '分</span></div>' + tasks.map(t => Today.taskRow(d, sk, t, false)).join('') + '</div>'; }).join('') + '</div></div>';
    });
    html += '<div class="sday card test"><div class="sd-head"><span class="sd-day">本番</span><span class="sd-date">' + fmtDate(PLAN.test_day) + '（' + wdOf(PLAN.test_day) + '）</span><span class="pill" style="background:var(--ai);color:#fff">' + esc(ED.name) + '</span><span class="sd-note">受験票・筆記用具・時計・昼食を前日に用意。新しいことはやらず、直しノートを見て早く寝る。</span></div></div>';
    main.innerHTML = '<div class="sched">' + html + '</div>';
    $$('#sc-filter button').forEach(b => b.onclick = () => { st.filter = b.dataset.f; render(); });
    $('#sc-today').onclick = () => { const t = today < PLAN.start ? PLAN.start : (today > PLAN.days[PLAN.days.length - 1].date ? PLAN.days[PLAN.days.length - 1].date : today); const e = $('#sd-' + t); if (e) e.scrollIntoView({ behavior: 'smooth', block: 'start' }); };
    Today.bindTasks(main, row => {
      // update this day's header and the task row without re-rendering everything
      const day = Today.dayOf(row.dataset.date); const ds = dayStats(day); const card = row.closest('.sday');
      row.classList.toggle('done', !!S.plan.done[row.dataset.k]); $('.chk i', row).textContent = S.plan.done[row.dataset.k] ? '✓' : '';
      $('.sd-prog .bar i', card).style.width = pct(ds.tmDone, ds.tm) + '%'; $('.sd-prog .num', card).textContent = ds.done + '/' + ds.total + '・' + ds.tmDone + '/' + ds.tm + '分';
      card.classList.toggle('alldone', ds.total && ds.done === ds.total);
    });
  }
  return { render, state: st };
})();
