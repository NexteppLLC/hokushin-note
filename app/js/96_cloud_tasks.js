/* ===== Optional item-level schedule sync for parent dashboard ===== */
const TaskProgressSync = (() => {
  const CONFIG_KEY = 'hn-cloud-config-v1';
  let auth = null, db = null, ready = false, timer = null, debounce = null;

  function configured() {
    try {
      const c = JSON.parse(localStorage.getItem(CONFIG_KEY) || 'null');
      return !!(c && c.apiKey && c.projectId);
    } catch (e) { return false; }
  }
  function stopTimer() { if (timer) clearInterval(timer); timer = null; }
  function buildSchedule() {
    const days = PLAN.days.map(d => {
      const tasks = [];
      SUBJ_ORDER.forEach(sk => {
        const s = SUBJ_BY_KEY[sk];
        (d.tasks[sk] || []).forEach(t => {
          const k = taskKey(d.day, sk, t.code);
          tasks.push({
            key: k,
            subjectKey: sk,
            subjectId: s.id,
            subjectName: s.name,
            subjectShort: s.short || s.name,
            code: t.code,
            title: t.title,
            minutes: Number(t.minutes) || 0,
            done: !!S.plan.done[k]
          });
        });
      });
      return {
        day: d.day,
        date: d.date,
        weekday: d.weekday,
        isHoliday: !!d.is_holiday,
        holiday: d.holiday || '',
        tasks
      };
    });
    return {
      schemaVersion: 1,
      app: 'hokushin-note',
      editionId: ED.id,
      editionName: ED.name,
      testDay: PLAN.test_day,
      clientUpdatedAt: Date.now(),
      days,
      privacy: { scheduleItems: true, questions: false, answers: false, notes: false, handwriting: false }
    };
  }
  async function syncNow(quiet) {
    if (!ready || !auth || !auth.currentUser || !db) return false;
    try {
      const doc = buildSchedule();
      doc.syncedAt = firebase.firestore.FieldValue.serverTimestamp();
      await db.collection('users').doc(auth.currentUser.uid).collection('hokushin').doc('schedule').set(doc, { merge: false });
      return true;
    } catch (e) {
      console.warn('TaskProgressSync failed', e);
      if (!quiet && typeof toast === 'function') toast('項目別進捗の同期に失敗しました：' + e.message);
      return false;
    }
  }
  function schedule() {
    if (!ready || !auth || !auth.currentUser) return;
    clearTimeout(debounce);
    debounce = setTimeout(() => syncNow(true), 8000);
  }
  function init() {
    if (!configured() || !window.firebase || !firebase.apps || !firebase.apps.length) return;
    try {
      auth = firebase.auth();
      db = firebase.firestore();
      ready = true;
      auth.onAuthStateChanged(u => {
        stopTimer();
        if (u) {
          setTimeout(() => syncNow(true), 1200);
          timer = setInterval(() => syncNow(true), 60000);
        }
      });
    } catch (e) { console.warn('TaskProgressSync init failed', e); }
  }
  return { init, schedule, syncNow, buildSchedule };
})();

// Add item-level sync without changing the existing local-save or summary-sync behavior.
const _taskLocalFlush = flush;
flush = async function () { const r = await _taskLocalFlush(); TaskProgressSync.schedule(); return r; };
const _taskAppBoot = App.boot;
App.boot = async function () { await _taskAppBoot(); TaskProgressSync.init(); };
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') TaskProgressSync.syncNow(true);
});
