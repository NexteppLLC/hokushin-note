/* ===== Optional parent progress sync (Firebase) ===== */
const CloudSync = (() => {
  const CONFIG_KEY = 'hn-cloud-config-v1';
  const SDK = '10.14.1';
  let app = null, auth = null, db = null, ready = false, timer = null, debounce = null;

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      if ([...document.scripts].some(s => s.src === src)) { resolve(); return; }
      const s = document.createElement('script'); s.src = src; s.async = true;
      s.onload = resolve; s.onerror = () => reject(new Error('Firebase SDKを読み込めませんでした'));
      document.head.appendChild(s);
    });
  }
  async function loadSDK() {
    if (window.firebase && firebase.auth && firebase.firestore) return;
    await loadScript('https://www.gstatic.com/firebasejs/' + SDK + '/firebase-app-compat.js');
    await loadScript('https://www.gstatic.com/firebasejs/' + SDK + '/firebase-auth-compat.js');
    await loadScript('https://www.gstatic.com/firebasejs/' + SDK + '/firebase-firestore-compat.js');
  }
  function getConfig() { try { return JSON.parse(localStorage.getItem(CONFIG_KEY) || 'null'); } catch (e) { return null; } }
  function parseConfig(text) {
    text = (text || '').trim(); if (!text) return null;
    try { return JSON.parse(text); } catch (e) {}
    const m = text.match(/\{[\s\S]*\}/); if (!m) throw new Error('firebaseConfig が見つかりません');
    return Function('"use strict";return (' + m[0] + ')')();
  }
  function saveConfig(c) { localStorage.setItem(CONFIG_KEY, JSON.stringify(c)); }
  function clearConfig() { localStorage.removeItem(CONFIG_KEY); }
  function configured() { const c = getConfig(); return !!(c && c.apiKey && c.projectId); }
  function user() { return auth && auth.currentUser; }
  function stateLabel() {
    if (!configured()) return '未設定';
    if (!ready) return '接続準備中';
    return user() ? '同期ON' : 'ログイン待ち';
  }
  function refreshCard() {
    const e = $('#cloud-state'); if (!e) return;
    e.textContent = stateLabel();
    e.className = 'pill ' + (user() ? 'ok' : 'mid');
    const d = $('#cloud-detail');
    if (d) d.textContent = user() ? ('ログイン中：' + (user().email || user().uid)) : (configured() ? 'Firebaseにログインすると親PCへ進捗を送信します。' : 'Firebaseの設定がまだありません。');
  }
  async function init() {
    if (!configured()) { refreshCard(); return; }
    try {
      await loadSDK();
      const c = getConfig();
      app = firebase.apps.length ? firebase.app() : firebase.initializeApp(c);
      auth = firebase.auth(); db = firebase.firestore(); ready = true;
      try { await auth.setPersistence(firebase.auth.Auth.Persistence.LOCAL); } catch (e) {}
      auth.onAuthStateChanged(u => {
        refreshCard();
        stopTimer();
        if (u) { timer = setInterval(() => syncNow(true), 60000); setTimeout(() => syncNow(true), 800); }
      });
    } catch (e) { console.warn('CloudSync init failed', e); ready = false; refreshCard(); }
  }
  function stopTimer() { if (timer) clearInterval(timer); timer = null; }
  function schedule() {
    if (!user()) return;
    clearTimeout(debounce); debounce = setTimeout(() => syncNow(true), 8000);
  }
  function lastActivityAt() {
    let last = 0;
    Object.values(S.progress || {}).forEach(doc => {
      Object.values(doc.items || {}).forEach(r => {
        last = Math.max(last, Number(r.t) || 0, Number(r.lastSeenAt) || 0);
        (r.attempts || []).forEach(a => { last = Math.max(last, Number(a.at) || 0, Number(a.t) || 0); });
      });
      Object.values(doc.units || {}).forEach(r => { last = Math.max(last, Number(r.v) || 0, Number(r.d) || 0); });
    });
    Object.values((S.plan && S.plan.done) || {}).forEach(t => { last = Math.max(last, Number(t) || 0); });
    ((S.plan && S.plan.studyTime) || []).forEach(x => { last = Math.max(last, Number(x.recordedAt) || 0); });
    return last;
  }
  function buildSummary() {
    const today = todayISO();
    const subjects = {};
    let items = 0, graded = 0, ok = 0, ng = 0, units = 0, unitsDone = 0;
    DATA.subjects.forEach(s => {
      const st = subjectStats(s);
      subjects[s.id] = { name: s.name, short: s.short || s.name, key: s.key, units: st.units, unitsDone: st.unitsDone, items: st.items, graded: st.graded, ok: st.ok, ng: st.ng };
      items += st.items; graded += st.graded; ok += st.ok; ng += st.ng; units += st.units; unitsDone += st.unitsDone;
    });
    let planTotal = 0, planDone = 0, dueTotal = 0, dueDone = 0, minutesTotal = 0, minutesDone = 0;
    const bySubject = {};
    PLAN.days.forEach(d => SUBJ_ORDER.forEach(sk => (d.tasks[sk] || []).forEach(t => {
      const k = ED.id + '|' + d.day + ':' + sk + ':' + t.code;
      const done = !!S.plan.done[k];
      bySubject[sk] = bySubject[sk] || { total: 0, done: 0, minutesTotal: 0, minutesDone: 0 };
      planTotal++; minutesTotal += t.minutes || 0; bySubject[sk].total++; bySubject[sk].minutesTotal += t.minutes || 0;
      if (d.date <= today) dueTotal++;
      if (done) { planDone++; minutesDone += t.minutes || 0; bySubject[sk].done++; bySubject[sk].minutesDone += t.minutes || 0; if (d.date <= today) dueDone++; }
    })));
    const hist = Study.totals();
    return {
      schemaVersion: 1, app: 'hokushin-note', editionId: ED.id, editionName: ED.name, testDay: PLAN.test_day,
      studentName: S.settings.name || '', clientUpdatedAt: Date.now(), lastActivityAt: lastActivityAt(), today,
      overall: { items, graded, ok, ng, units, unitsDone }, subjects,
      plan: { total: planTotal, done: planDone, dueTotal, dueDone, minutesTotal, minutesDone, bySubject },
      actualStudy: { todayMinutes: Study.timeTotal(today, today), last7Minutes: Study.timeTotal(addDays(today, -6), today) },
      studyHistory: { first: hist.first, firstOk: hist.firstOk, retest: hist.retest, retestOk: hist.retestOk, due: hist.due },
      privacy: { questions: false, answers: false, notes: false, handwriting: false }
    };
  }
  async function syncNow(quiet) {
    if (!ready || !user() || !db) { if (!quiet) toast('クラウド同期は未設定または未ログインです'); return false; }
    try {
      const summary = buildSummary(); summary.syncedAt = firebase.firestore.FieldValue.serverTimestamp();
      await db.collection('users').doc(user().uid).collection('hokushin').doc('current').set(summary, { merge: false });
      try { localStorage.setItem('hn-cloud-last-sync', String(Date.now())); } catch (e) {}
      if (!quiet) toast('親PC用の進捗を同期しました');
      refreshCard(); return true;
    } catch (e) { console.warn('CloudSync sync failed', e); if (!quiet) toast('同期できませんでした：' + e.message); return false; }
  }
  async function login(email, password) {
    if (!configured()) throw new Error('先にFirebase設定を保存してください');
    if (!ready) await init();
    if (!auth) throw new Error('Firebaseに接続できません');
    await auth.signInWithEmailAndPassword(email, password); await syncNow(true);
  }
  async function logout() { if (auth) await auth.signOut(); refreshCard(); }
  function openSetup() {
    const c = getConfig();
    const body = el('<div>' +
      '<p class="sm muted">学習履歴本体はこれまで通りこの端末に保存します。クラウドへ送るのは、科目別進捗・○△×集計・予定完了率・学習時間などの要約だけです。問題文・解答・付箋・手書きは送信しません。</p>' +
      '<label class="cloud-field"><b>Firebase Web設定</b><textarea id="cloud-config" rows="7" placeholder="Firebase Console の firebaseConfig を貼り付け"></textarea></label>' +
      '<div class="row"><button id="cloud-save-config">設定を保存</button><button id="cloud-clear-config">設定を消す</button></div>' +
      '<hr><label class="cloud-field"><b>メールアドレス</b><input type="email" id="cloud-email" autocomplete="username"></label>' +
      '<label class="cloud-field"><b>パスワード</b><input type="password" id="cloud-password" autocomplete="current-password"></label>' +
      '<div class="row"><button class="primary" id="cloud-login">ログイン</button><button id="cloud-logout">ログアウト</button><button id="cloud-now">今すぐ同期</button></div>' +
      '<p class="sm muted">親PCでは <b>parent.html</b> を開き、同じFirebase設定・同じ家族用アカウントでログインします。</p>' +
      '</div>');
    $('#cloud-config', body).value = c ? JSON.stringify(c, null, 2) : '';
    const m = openModal('親PCとのクラウド同期', body, { sticky: true });
    $('#cloud-save-config', body).onclick = () => { try { const x = parseConfig($('#cloud-config', body).value); if (!x || !x.apiKey || !x.projectId) throw new Error('apiKey / projectId を確認してください'); saveConfig(x); toast('Firebase設定を保存しました。再読み込みします'); setTimeout(() => location.reload(), 500); } catch (e) { toast('保存できません：' + e.message); } };
    $('#cloud-clear-config', body).onclick = () => { clearConfig(); toast('Firebase設定を消しました。学習履歴は消えていません'); setTimeout(() => location.reload(), 500); };
    $('#cloud-login', body).onclick = async () => { try { await login($('#cloud-email', body).value.trim(), $('#cloud-password', body).value); $('#cloud-password', body).value = ''; toast('ログインしました'); m.close(); if (App.view === 'settings') Settings.render(); } catch (e) { toast('ログインできません：' + e.message); } };
    $('#cloud-logout', body).onclick = async () => { await logout(); toast('ログアウトしました'); m.close(); if (App.view === 'settings') Settings.render(); };
    $('#cloud-now', body).onclick = () => syncNow(false);
  }
  function injectSettings() {
    const main = $('#main'); if (!main || $('#cloud-sync-card')) return;
    const help = $$('.sh', main).find(x => x.textContent.indexOf('使い方') >= 0);
    const wrap = el('<div><h2 class="sh">親PCとの同期</h2><div class="card" id="cloud-sync-card"><div class="set-row"><div class="sl"><b>クラウド同期 <span id="cloud-state" class="pill mid"></span></b><small id="cloud-detail"></small><small>親PCから進捗を見るための任意機能です。端末内保存とバックアップは今まで通り残ります。</small></div><button class="primary" id="cloud-setup-btn">設定する</button><button id="cloud-sync-btn">今すぐ同期</button></div></div></div>');
    if (help) main.insertBefore(wrap, help); else main.appendChild(wrap);
    $('#cloud-setup-btn').onclick = openSetup; $('#cloud-sync-btn').onclick = () => syncNow(false); refreshCard();
  }
  return { init, schedule, syncNow, injectSettings, openSetup, buildSummary };
})();

// Existing local save remains primary. Cloud sync is an additive, debounced copy of summaries.
const _cloudLocalFlush = flush;
flush = async function () { const r = await _cloudLocalFlush(); CloudSync.schedule(); return r; };
const _cloudSettingsRender = Settings.render;
Settings.render = function () { _cloudSettingsRender(); CloudSync.injectSettings(); };
const _cloudAppBoot = App.boot;
App.boot = async function () { await _cloudAppBoot(); await CloudSync.init(); };
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') CloudSync.syncNow(true); });
