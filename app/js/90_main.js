/* ===== app shell: routing & boot ===== */
const App = (() => {
  const views = { today: Today, schedule: Schedule, learn: Learn, progress: Progress, notes: NotesView, settings: Settings };
  const api = { view: 'today' };
  function show(v) {
    api.view = v;
    $$('#tabs button').forEach(b => b.classList.toggle('active', b.dataset.view === v));
    if (v !== 'learn' && Ink.isPen()) Ink.setPenMode(false);
    HL.hide();
    views[v].render();
    S.settings.view = v; markDirty('settings/main');
    if (v !== 'learn') window.scrollTo(0, 0);
  }
  function applyFs() { document.body.classList.remove('fs-s', 'fs-l', 'fs-xl'); const f = S.settings.fs || 'm'; if (f !== 'm') document.body.classList.add('fs-' + f); }
  function countdown() { const d = diffDays(todayISO(), PLAN.test_day); $('#countdown').textContent = (EDITIONS.length > 1 ? '' : ED.short + '　') + (d > 0 ? 'あと ' + d + ' 日' : (d === 0 ? '本番当日' : '終了')); }
  function renderEdSelect() {
    const sel = $('#sel-ed'); if (!sel) return;
    if (EDITIONS.length < 2) { sel.hidden = true; return; }
    sel.hidden = false;
    sel.innerHTML = EDITIONS.map(E => '<option value="' + E.id + '"' + (E.id === ED.id ? ' selected' : '') + '>' + esc(E.short || E.name) + '</option>').join('');
    sel.onchange = e => api.setEdition(e.target.value);
  }
  api.setEdition = function (id, silent) {
    setEdition(id); S.settings.edition = ED.id; markDirty('settings/main');
    countdown(); renderEdSelect();
    if (!silent) { show(api.view === 'learn' ? 'today' : api.view); toast(ED.name + ' に切りかえました'); }
  };
  async function boot() {
    await loadState();
    applyFs();
    document.body.classList.toggle('finger', !!S.settings.fingerDraw);
    countdown(); renderEdSelect();
    $$('#tabs button').forEach(b => b.onclick = () => show(b.dataset.view));
    $('#btn-timer').onclick = () => Timer.toggle();
    show('today');
    if (!S.settings.seenIntro) {
      S.settings.seenIntro = true; markDirty('settings/main');
      setTimeout(() => openModal('はじめに', '<div class="help">' +
        '<p><b>北辰10月 学習ノート</b>へようこそ。10月11日の第5回北辰テストまで、このアプリ1つで計画・教材・問題・メモをまとめて進められます。</p>' +
        '<h3>1. 「今日」で予定を見る</h3><p>教科ごとの今日の予定が出ます。<b>開く ›</b> でその単元にジャンプ。終わったらチェック。</p>' +
        '<h3>2. 「学ぶ」で読んで解く</h3><p>科目と単元をプルダウンで選びます。要点を読んだら一問一答・演習へ。<b>答え</b>を見て、自分で <b>○△×</b> をつけます。</p>' +
        '<h3>3. 書き込む・付箋を貼る</h3><p><b>書き込み</b> をオンにすると Apple Pencil で教材の上に直接書けます（指はスクロール）。文章を長押しで選ぶと<b>マーカー</b>や<b>付箋</b>。全部「ノート」タブに集まります。</p>' +
        '<h3>4. ×は「直しリスト」へ</h3><p>「進捗」の直しリストに自動で集まるので、カードでまとめて解き直せます。</p>' +
        '<p class="muted sm">データはこのiPadの中に保存されます。週に1回「設定 → 書き出す」でバックアップしておくと安心です。</p></div>',
        { footer: '<button class="primary" data-ok>はじめる</button>' }).querySelector('[data-ok]').onclick = function () { this.closest('.modal-bg').remove(); }, 400);
    }
    // weekly backup reminder
    const lb = S.settings.lastBackup || 0; const hasData = Object.values(S.progress).some(p => Object.keys(p.items || {}).length > 20);
    let warned = false; try { warned = !!sessionStorage.getItem('bkwarned'); } catch (e) {}
    if (hasData && Date.now() - lb > 7 * 86400e3 && !warned) { try { sessionStorage.setItem('bkwarned', '1'); } catch (e) {} setTimeout(() => toast('1週間以上バックアップしていません。「設定 → 書き出す」で保存しておきましょう'), 2500); }
    window.addEventListener('resize', () => { $$('.inkhost').forEach(h => h._ink && h._ink.render()); });
  }
  api.show = show; api.applyFs = applyFs; api.boot = boot;
  return api;
})();
(() => { let booted = false; const go = () => { if (booted) return; booted = true; App.boot(); }; if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go(); })();
