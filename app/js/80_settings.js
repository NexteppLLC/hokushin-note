/* ===== Settings, backup / restore, help ===== */
const Settings = (() => {
  function render() {
    const main = $('#main');
    const lb = S.settings.lastBackup ? new Date(S.settings.lastBackup) : null;
    const sw = (on) => '<button class="switch ' + (on ? 'on' : '') + '" role="switch" aria-checked="' + on + '"></button>';
    main.innerHTML = '<h1 class="vh">設定</h1><div class="card">' +
      '<div class="set-row"><div class="sl"><b>バックアップ</b><small>採点履歴・初見/後日再テスト・復習日・実際の学習時間・進捗・付箋・マーカー・手書きをまとめて1つのファイル（JSON）にします。ファイル保存ができない場合は自動で「コピー」に切りかわるので、メモアプリなどに貼り付けて保存してください。' + (lb ? '最終バックアップ：' + (lb.getMonth() + 1) + '/' + lb.getDate() + ' ' + pad2(lb.getHours()) + ':' + pad2(lb.getMinutes()) : 'まだバックアップしていません') + '</small></div><button class="primary" id="bk-save">書き出す</button><button id="bk-copy">コピー</button></div>' +
      '<div class="set-row"><div class="sl"><b>復元</b><small>バックアップファイルを読み込んで、いまのデータと置きかえます（合体ではありません）。</small></div><label class="row" style="gap:6px"><input type="file" id="bk-file" accept=".json,application/json" hidden><button id="bk-load">ファイルを選ぶ</button></label><button id="bk-paste">貼り付けて復元</button></div>' +
      '<div class="set-row"><div class="sl"><b>指でも書く</b><small>オンにすると、ペンモードや計算スペースで指でも線が引けます（スクロールは余白か2本指で）。</small></div>' + sw(S.settings.fingerDraw).replace('class="switch', 'id="sw-finger" class="switch') + '</div>' +
      '<div class="set-row"><div class="sl"><b>ふりがな（理科・社会）</b><small>漢字の上のふりがなを表示／非表示にします。</small></div>' + sw(S.settings.ruby).replace('class="switch', 'id="sw-ruby" class="switch') + '</div>' +
      '<div class="set-row"><div class="sl"><b>文字の大きさ</b></div><div class="seg" id="seg-fs">' + [['s', '小'], ['m', '標準'], ['l', '大'], ['xl', '特大']].map(([k, l]) => '<button data-fs="' + k + '" class="' + ((S.settings.fs || 'm') === k ? 'active' : '') + '">' + l + '</button>').join('') + '</div></div>' +
      '<div class="set-row"><div class="sl"><b>データの保存先</b><small>この端末（' + (Store.mode() === 'idb' ? 'ブラウザの内部データベース' : (Store.mode() === 'ls' ? 'ブラウザの簡易ストレージ' : 'メモリのみ・閉じると消えます')) + '）に保存。ホーム画面に追加して使うと消えにくくなります。</small></div></div>' +
      '<div class="set-row"><div class="sl"><b>すべてのデータを消す</b><small>進捗・付箋・書き込みを全部消して最初の状態に戻します。</small></div><button id="bk-reset" style="color:var(--ng)">初期化</button></div>' +
      '</div>' +
      '<h2 class="sh">使い方</h2><div class="card help">' +
      '<h3>毎日の流れ</h3><p>1. 「今日」を開く → 教科ごとの予定が出ます。<b>開く ›</b> で教材にジャンプ。<br>2. 要点を読む → 紙やノートで問題を解く → <b>解答を終えた・答え合わせ</b> → <b>○△×</b> を自分でつける。<br>3. 終わったら「今日」のチェックを入れる（または教材の上の「この予定を完了にする」）。</p>' +
      '<h3>書き込み（Apple Pencil）</h3><p>「学ぶ」の <b>書き込み</b> をオンにすると、教材の上にペンで直接書けます。指はそのままスクロールに使えます。各問題の <b>✎ 書く</b> は計算スペース、<b>ノート</b> は単元ごとの自由帳です。ペンの色・太さ・マーカー・消しゴムは画面下のバーで切りかえます。</p>' +
      '<h3>マーカーと付箋</h3><p>文章を長押しして選ぶと、色のボタンが出ます。<b>付箋にする</b> で、その文を引用した付箋を作れます。付箋はブロックの下や単元の上に貼られ、「ノート」タブに全部まとまります。</p>' +
      '<h3>初見・解き直し・後日再テスト</h3><p>初めて自力で解いた問題は初見として記録します。以前の学習や先に答えを見た記録があると解き直しです。<b>後日再テスト</b>は前回の学習から24時間以上あけ、解答を終えてから答え合わせします。自己申告の記録なので、採点は解説の条件まで確認してください。○△×の訂正履歴も保存します。</p><p>改修前の採点は<b>改修前の記録</b>として残し、新しい初見・後日再テストの○率に含めません。</p>' +
      '<h3>直しリスト</h3><p>×や△をつけた問題は「進捗 → 直しリスト」に自動で集まります。<b>カードで解き直す</b> で一気に復習し、○に直せば直しリストから消えますが、後日再テストの対象は残ります。</p>' +
      '<h3>バックアップ</h3><p>週に1回くらい「書き出す」でファイルを保存しておくと安心です（iPadの「ファイル」やiCloud Driveに保存できます）。別の端末で見たいときは、そのファイルを「復元」で読み込みます。</p>' +
      '</div>';
    $('#bk-save').onclick = exportBackup;
    $('#bk-copy').onclick = copyBackup;
    $('#bk-load').onclick = () => $('#bk-file').click();
    $('#bk-file').onchange = e => { const f = e.target.files[0]; if (!f) return; const r = new FileReader(); r.onload = () => importBackup(r.result); r.readAsText(f); };
    $('#bk-paste').onclick = () => { const body = el('<div><p class="sm muted">バックアップの文字（JSON）をここに貼り付けてください。</p><textarea rows="8" id="paste-area" placeholder="{ ... }"></textarea></div>'); const m = openModal('貼り付けて復元', body, { footer: '<button class="primary" data-ok>復元する</button>', sticky: true }); $('[data-ok]', m).onclick = () => { const t = $('#paste-area', body).value; m.close(); importBackup(t); }; };
    $('#sw-finger').onclick = () => { S.settings.fingerDraw = !S.settings.fingerDraw; document.body.classList.toggle('finger', S.settings.fingerDraw); markDirty('settings/main'); render(); };
    $('#sw-ruby').onclick = () => { S.settings.ruby = !S.settings.ruby; markDirty('settings/main'); render(); };
    $$('#seg-fs button').forEach(b => b.onclick = () => { S.settings.fs = b.dataset.fs; App.applyFs(); markDirty('settings/main'); render(); });
    $('#bk-reset').onclick = async () => { if (await confirmBox('本当にすべてのデータを消しますか？ この操作は取り消せません。')) { if (await confirmBox('最終確認：進捗・付箋・書き込みが全部消えます。よろしいですか？')) { await Store.clear(); location.reload(); } } };
  }
  function backupJSON() {
    return JSON.stringify({ app: 'hokushin-note', v: 3, studyRevision: Study.REVISION, exported: new Date().toISOString(), progress: S.progress, plan: S.plan, notes: S.notes, settings: S.settings, hl: S.hl, ink: S.ink, nb: S.nb });
  }
  function fname() { const d = new Date(); return 'hokushin_backup_' + d.getFullYear() + pad2(d.getMonth() + 1) + pad2(d.getDate()) + '.json'; }
  async function exportBackup() {
    const json = backupJSON();
    let ok = false;
    let framed = false; try { framed = window.top !== window.self; } catch (e) { framed = true; }
    try {
      if (window.claude && typeof window.claude.use === 'function') {
        const dl = await Promise.race([window.claude.use('downloads'), new Promise(r => setTimeout(() => r(null), 3000))]);
        if (dl) { try { await dl.save({ filename: fname(), data: json }); ok = true; } catch (e) { if (e && e.code === 'declined') { toast('保存をキャンセルしました'); return; } } }
      }
    } catch (e) { /* fall through */ }
    if (!ok && framed) { copyBackup(); return; }
    if (!ok) {
      try {
        const blob = new Blob([json], { type: 'application/json' });
        const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = fname(); document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 2000);
        ok = true;
        toast('ダウンロードが始まらない場合は「コピー」を使ってください');
      } catch (e) { ok = false; }
    }
    if (ok) { S.settings.lastBackup = Date.now(); markDirty('settings/main'); setTimeout(render, 600); }
    else copyBackup();
  }
  async function copyBackup() {
    const json = backupJSON();
    try { await navigator.clipboard.writeText(json); toast('バックアップをコピーしました。メモ帳などに貼り付けて保存してください'); S.settings.lastBackup = Date.now(); markDirty('settings/main'); setTimeout(render, 600); return; } catch (e) {}
    const body = el('<div><p class="sm muted">全部選んでコピーし、メモ帳などに貼り付けて保存してください（' + Math.round(json.length / 1024) + ' KB）。</p><textarea rows="10" readonly></textarea></div>');
    $('textarea', body).value = json;
    openModal('バックアップ（コピー用）', body);
    setTimeout(() => { const ta = $('textarea', body); ta.focus(); ta.select(); }, 100);
  }
  async function importBackup(text) {
    let obj;
    try { obj = JSON.parse(text); } catch (e) { toast('読み込めませんでした（ファイルの形式が違います）'); return; }
    if (!obj || obj.app !== 'hokushin-note' || !obj.progress || (obj.v && obj.v > 3)) { toast('このアプリのバックアップではないようです'); return; }
    const when = obj.exported ? new Date(obj.exported) : null;
    if (!(await confirmBox('バックアップ（' + (when ? (when.getMonth() + 1) + '/' + when.getDate() + ' ' + pad2(when.getHours()) + ':' + pad2(when.getMinutes()) : '日時不明') + '）で、いまのデータを置きかえます。よろしいですか？'))) return;
    await Store.clear();
    S.progress = obj.progress || {}; S.plan = Object.assign({ done: {}, log: {} }, obj.plan || {}); S.notes = Object.assign({ list: [] }, obj.notes || {}); S.settings = Object.assign(S.settings, obj.settings || {}); S.hl = obj.hl || {}; S.ink = obj.ink || {}; S.nb = obj.nb || {};
    if (!obj.v || obj.v < 2) migrateV1(S);
    Study.migrateAll(S);
    EDITIONS.forEach(E => E.subjects.forEach(s => progOf(s)));
    setEdition(S.settings.edition && EDITIONS_BY_ID[S.settings.edition] ? S.settings.edition : defaultEdition());
    Object.keys(S.progress).forEach(k => markDirty('progress/' + k));
    markDirty('plan/main'); markDirty('notes/all'); markDirty('settings/main');
    Object.keys(S.hl).forEach(k => markDirty('hl/' + k)); Object.keys(S.ink).forEach(k => markDirty('ink/' + k)); Object.keys(S.nb).forEach(k => markDirty('nb/' + k));
    await flush();
    toast('復元しました'); App.applyFs(); App.show('today');
  }
  return { render, exportBackup, importBackup, backupJSON };
})();

/* ===== study timer ===== */
const Timer = (() => {
  let remain = 0, total = 0, running = false, tick = null, mode = 'down', elapsed = 0, alarmed = false;
  const box = () => $('#timer-box');
  function fmt(s) { s = Math.max(0, Math.round(s)); return pad2(Math.floor(s / 60)) + ':' + pad2(s % 60); }
  function render() {
    const b = box(); if (b.hidden) return;
    b.innerHTML = '<div class="tv ' + (alarmed ? 'alarm' : '') + '">' + (mode === 'down' ? fmt(remain) : fmt(elapsed)) + '</div>' +
      '<div class="tp">' + [8, 10, 15, 20, 40, 50].map(m => '<button data-set="' + m + '">' + m + '分</button>').join('') + '<button data-set="0">ストップウォッチ</button></div>' +
      '<div class="tc"><button class="primary" data-a="start">' + (running ? '一時停止' : 'スタート') + '</button><button data-a="reset">リセット</button><button data-a="close">閉じる</button></div>';
    $$('[data-set]', b).forEach(x => x.onclick = () => { const m = +x.dataset.set; stop(); alarmed = false; if (m === 0) { mode = 'up'; elapsed = 0; } else { mode = 'down'; total = remain = m * 60; } render(); });
    $('[data-a="start"]', b).onclick = () => { if (running) stop(); else start(); render(); };
    $('[data-a="reset"]', b).onclick = () => { stop(); alarmed = false; remain = total; elapsed = 0; render(); };
    $('[data-a="close"]', b).onclick = () => { b.hidden = true; };
  }
  function start() { if (mode === 'down' && remain <= 0) return; running = true; alarmed = false; let last = Date.now(); tick = setInterval(() => { const now = Date.now(); const dt = (now - last) / 1000; last = now; if (mode === 'down') { remain -= dt; if (remain <= 0) { remain = 0; stop(); alarmed = true; beep(); toast('時間です！'); } } else elapsed += dt; const tv = $('.tv', box()); if (tv) { tv.textContent = mode === 'down' ? fmt(remain) : fmt(elapsed); tv.classList.toggle('alarm', alarmed); } if (!running) render(); }, 250); }
  function stop() { running = false; clearInterval(tick); tick = null; }
  function beep() { try { const ac = new (window.AudioContext || window.webkitAudioContext)(); [0, 0.3, 0.6].forEach(t => { const o = ac.createOscillator(), g = ac.createGain(); o.connect(g); g.connect(ac.destination); o.frequency.value = 880; g.gain.setValueAtTime(0.25, ac.currentTime + t); g.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + t + 0.25); o.start(ac.currentTime + t); o.stop(ac.currentTime + t + 0.26); }); } catch (e) {} }
  function toggle() { const b = box(); b.hidden = !b.hidden; if (!b.hidden) { if (!total && mode === 'down') { total = remain = 40 * 60; } render(); } }
  return { toggle };
})();
