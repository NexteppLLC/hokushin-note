/* ===== Optional item-level schedule sync for parent dashboard ===== */
const TaskProgressSync = (() => {
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
      schemaVersion: 2,
      app: 'hokushin-note',
      editionId: ED.id,
      editionName: ED.name,
      testDay: PLAN.test_day,
      clientUpdatedAt: Date.now(),
      deviceId: (typeof CloudSync !== 'undefined' && CloudSync.deviceId) ? CloudSync.deviceId() : '',
      writerRole: 'student-device',
      days,
      privacy: { scheduleItems: true, questions: false, answers: false, notes: false, handwriting: false }
    };
  }
  // A single coordinator sends both documents, including manual sync, retries,
  // foreground wake-up and the periodic timer. Never write schedule independently.
  function syncNow(quiet) { return CloudSync.syncNow(quiet); }
  return { buildSchedule, syncNow };
})();
