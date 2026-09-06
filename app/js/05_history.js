/* ===== Attempts, delayed review, and actual study time ===== */
const Study = (() => {
  const DAY = 86400000;
  const REVISION = 'visual-2026-09-v1';
  const MODES = { first: '初見', review: '解き直し', retest: '後日再テスト' };
  const REASONS = { knowledge: '知識', visual: '図表', conditions: '条件', calculation: '計算', writing: '記述', time: '時間' };
  const validGrade = g => g === 0 || g === 1 || g === 2;
  const symbol = g => ({ 0: '×', 1: '△', 2: '○' }[g] || '取消');
  const stamp = t => { const d = new Date(t); return Number.isFinite(d.getTime()) ? (d.getMonth() + 1) + '/' + d.getDate() + ' ' + pad2(d.getHours()) + ':' + pad2(d.getMinutes()) : '日時不明'; };

  function migrateRecord(rec) {
    if (!rec || typeof rec !== 'object') return false;
    if (Array.isArray(rec.attempts)) return false;
    // Preserve every old field, including the old latest grade and timestamp.
    if (!rec.legacy && (validGrade(rec.g) || rec.t)) rec.legacy = JSON.parse(JSON.stringify(rec));
    rec.attempts = []; rec.historyVersion = 1;
    return true;
  }
  function migrateAll(obj) {
    const changed = [];
    Object.entries(obj.progress || {}).forEach(([key, doc]) => {
      let dirty = false;
      Object.values(doc.items || {}).forEach(rec => { if (migrateRecord(rec)) dirty = true; });
      if (dirty) changed.push(key);
    });
    return changed;
  }
  function item(key, create) {
    const items = progOf(key).items;
    if (!items[key] && create) items[key] = { attempts: [], historyVersion: 1 };
    const rec = items[key];
    if (rec && migrateRecord(rec)) markDirty('progress/' + progKey(key));
    return rec;
  }
  function effective(rec) {
    const map = new Map();
    (rec && rec.attempts || []).forEach(event => { if (event && event.attemptId) map.set(event.attemptId, event); });
    // Map insertion order is the original attempt order. Stable sorting keeps that
    // order when two attempts completed within the same millisecond; a later
    // correction timestamp must never make an older attempt become the latest.
    return Array.from(map.values()).filter(a => validGrade(a.g)).sort((a, b) => a.at - b.at);
  }
  function syncLatest(rec) {
    const attempts = effective(rec);
    const latest = attempts[attempts.length - 1];
    if (latest) {
      rec.g = latest.g; rec.t = latest.t; rec.reason = latest.reason || '';
    } else if (rec.legacy && validGrade(rec.legacy.g)) {
      rec.g = rec.legacy.g; rec.t = rec.legacy.t; rec.reason = rec.legacy.reason || '';
    } else {
      delete rec.g; delete rec.t; delete rec.reason;
    }
  }
  function session(mode, source) { return { id: uid(), mode: mode || 'auto', source: source || 'learn', createdAt: Date.now(), date: todayISO(), reasons: {} }; }
  function current(key, run) {
    if (!run) return null;
    const rec = item(key);
    const events = rec && rec.attempts || [];
    const id = run.id + ':' + key;
    for (let i = events.length - 1; i >= 0; i--) if (events[i].attemptId === id) return events[i];
    return null;
  }
  function completion(key, run) {
    const rec = item(key);
    return run && rec && (rec.completions || []).find(x => x.attemptId === run.id + ':' + key) || null;
  }
  function finish(key, run) {
    if (!run) return null;
    const existing = completion(key, run); if (existing) return existing;
    const at = Date.now(), selected = modeFor(key, run, at);
    const rec = item(key, true); rec.completions = rec.completions || [];
    const done = { attemptId: run.id + ':' + key, at, mode: selected.mode, revision: REVISION, source: run.source };
    rec.completions.push(done); rec.review = schedule(rec);
    markDirty('progress/' + progKey(key));
    return done;
  }
  function lastExposure(rec) {
    if (!rec) return 0;
    let t = Math.max(Number(rec.lastSeenAt) || 0, Number(rec.legacy && rec.legacy.t) || 0);
    (rec.attempts || []).forEach(a => { t = Math.max(t, Number(a.at) || 0, Number(a.t) || 0); });
    (rec.completions || []).forEach(a => { t = Math.max(t, Number(a.at) || 0); });
    return t;
  }
  function hasSeen(rec) { return !!(rec && (rec.lastSeenAt || rec.legacy || (rec.attempts || []).length || (rec.completions || []).length)); }
  function modeFor(key, run, now) {
    const previous = current(key, run);
    if (previous) return { mode: previous.mode, message: '' };
    const done = completion(key, run);
    if (done) return { mode: done.mode, message: '' };
    const rec = item(key), wanted = run && run.mode || 'auto';
    if (wanted === 'review') return { mode: 'review', message: '' };
    if (wanted === 'retest') {
      const last = lastExposure(rec);
      if (hasSeen(rec) && last && now - last >= DAY) return { mode: 'retest', message: '' };
      return { mode: 'review', message: '前回の採点・答えの閲覧から24時間未満のため、解き直しとして記録しました。' };
    }
    if (!hasSeen(rec)) return { mode: 'first', message: '' };
    return { mode: 'review', message: wanted === 'first' ? '以前の採点や答えの閲覧があるため、解き直しとして記録しました。' : '' };
  }
  function seen(key) {
    const rec = item(key, true);
    rec.lastSeenAt = Date.now();
    rec.review = schedule(rec);
    markDirty('progress/' + progKey(key));
  }
  function record(key, g, opts) {
    opts = opts || {};
    if (g != null && !validGrade(g)) return { changed: false };
    const run = opts.session || session(opts.mode || 'review', opts.source);
    const old = current(key, run);
    if (g == null && !old) return { changed: false };
    const now = Date.now();
    const selection = modeFor(key, run, now);
    const done = completion(key, run) || (g != null ? finish(key, run) : null);
    const reason = Object.prototype.hasOwnProperty.call(opts, 'reason') ? opts.reason : (run.reasons[key] || (old && old.reason) || '');
    const cleanReason = Object.prototype.hasOwnProperty.call(REASONS, reason) ? reason : '';
    // Re-rendering and repeated clicks for the same result produce no extra event.
    if (old && old.g === g && (old.reason || '') === cleanReason) return { changed: false, event: old, mode: old.mode };
    const rec = item(key, true);
    const event = { id: uid(), attemptId: run.id + ':' + key, revision: REVISION,
      kind: old ? 'correction' : 'attempt', mode: selection.mode, g,
      at: old ? old.at : (done ? done.at : now), completedAt: done ? done.at : null, t: now, source: run.source || 'learn', reason: cleanReason };
    rec.attempts.push(event);
    // An old run can still receive a reason/grade correction after a newer run.
    // Rebuild compatibility fields from the newest effective attempt, not this event.
    // Cancelling the newest attempt reveals the previous attempt (or legacy grade).
    syncLatest(rec);
    rec.review = schedule(rec);
    markDirty('progress/' + progKey(key)); logActivity();
    return { changed: true, event, mode: selection.mode, message: selection.message };
  }
  function setReason(key, reason, run) {
    if (!run) return;
    run.reasons[key] = Object.prototype.hasOwnProperty.call(REASONS, reason) ? reason : '';
    const a = current(key, run);
    if (a) record(key, a.g, { session: run, reason: run.reasons[key] });
  }
  function schedule(rec) {
    const attempts = effective(rec).filter(a => a.revision === REVISION);
    let step = 0;
    attempts.forEach(a => { if (a.g < 2) step = 0; else if (a.mode === 'retest') step = Math.min(2, step + 1); });
    const last = lastExposure(rec);
    const days = [1, 3, 7][step];
    return { days, due: last ? last + days * DAY : null, eligibleAt: last ? last + DAY : null };
  }
  function totals(subjects, now) {
    now = now == null ? Date.now() : now;
    const out = { first: 0, firstOk: 0, retest: 0, retestOk: 0, legacy: 0, due: 0 };
    (subjects || DATA.subjects).forEach(s => s.units.forEach(u => u.items.forEach(it => {
      const rec = item(it.key); if (!rec) return;
      const attempts = effective(rec).filter(a => a.revision === REVISION);
      attempts.forEach(a => { if (a.mode === 'first') { out.first++; if (a.g === 2) out.firstOk++; } else if (a.mode === 'retest') { out.retest++; if (a.g === 2) out.retestOk++; } });
      if (rec.legacy) out.legacy++;
      const due = schedule(rec).due; if (due && due <= now) out.due++;
    })));
    return out;
  }
  function dueItems(sid, now) {
    now = now == null ? Date.now() : now;
    const out = [];
    (sid ? [SUBJ[sid]] : DATA.subjects).forEach(s => s.units.forEach(u => u.items.forEach(it => {
      const rec = item(it.key); if (!rec) return;
      const review = schedule(rec);
      if (review.due && review.due <= now) out.push({ it, u, s, r: rec, review });
    })));
    return out.sort((a, b) => a.review.due - b.review.due);
  }
  function noteHTML(key) {
    const rec = item(key); if (!rec) return '';
    const attempts = effective(rec).filter(a => a.revision === REVISION);
    if (!attempts.length && rec.legacy) return '<span class="study-legacy">改修前の記録</span>';
    const a = attempts[attempts.length - 1];
    return a ? '<span class="study-record">' + esc(MODES[a.mode] || '練習') + ' ' + symbol(a.g) + ' · ' + esc(stamp(a.at)) + '</span>' : '';
  }
  function reasonHTML(key, run) {
    const rec = item(key), a = current(key, run);
    const selected = run && run.reasons[key] || a && a.reason || '';
    return '<select class="study-reason" data-reason aria-label="失点理由（任意）"><option value="">失点理由（任意）</option>' +
      Object.entries(REASONS).map(([k, v]) => '<option value="' + k + '"' + (k === selected ? ' selected' : '') + '>' + v + '</option>').join('') + '</select>';
  }
  function history(key) {
    const rec = item(key);
    let html = '<p class="sm muted">○△×は自己採点です。採点の訂正は同じ1回として集計します。</p>';
    if (rec && rec.legacy) html += '<p class="study-legacy">改修前の記録：' + symbol(rec.legacy.g) + ' · ' + esc(stamp(rec.legacy.t)) + '（初見・後日再テストの集計対象外）</p>';
    const all = rec && rec.attempts || [];
    html += all.length ? '<div class="study-history">' + all.slice().reverse().map(a => '<div><span>' + esc(stamp(a.t)) + '</span><b>' + symbol(a.g) + '</b><span>' + esc(MODES[a.mode] || '練習') + (a.kind === 'correction' ? '・訂正' : '') + (a.reason ? '・' + esc(REASONS[a.reason] || '') : '') + '</span></div>').join('') + '</div>' : '<p>改修後の採点はまだありません。</p>';
    openModal('学習記録', html);
  }
  function modeOptions(selected) {
    return [['auto', '初見・直し（自動）'], ['review', '解き直し'], ['retest', '後日再テスト']].map(([k, label]) => '<option value="' + k + '"' + (selected === k ? ' selected' : '') + '>' + label + '</option>').join('');
  }
  const help = '紙やノートに解答して「解答を終えた・答え合わせ」→○△×で自己採点。先に「答えを見て学ぶ」を選ぶと解き直しです。後日再テストは前回の学習から24時間以上あけます。初見・正答率は自己申告の記録です。';
  function addTime(date, minutes) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !Number.isFinite(minutes) || !Number.isInteger(minutes) || minutes < 1 || minutes > 720 || date > todayISO()) return false;
    const d = new Date(date + 'T12:00:00'); if (!Number.isFinite(d.getTime()) || d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()) !== date) return false;
    S.plan.studyTime = S.plan.studyTime || [];
    S.plan.studyTime.push({ id: uid(), date, minutes, recordedAt: Date.now(), source: 'manual' });
    markDirty('plan/main'); return true;
  }
  function cancelTime(id) {
    const entry = (S.plan.studyTime || []).find(x => x.id === id);
    if (entry) { entry.cancelledAt = Date.now(); markDirty('plan/main'); }
  }
  function timeTotal(from, to) { return (S.plan.studyTime || []).filter(x => !x.cancelledAt && x.date >= from && x.date <= to).reduce((sum, x) => sum + x.minutes, 0); }
  return { DAY, REVISION, MODES, REASONS, validGrade, migrateAll, effective, session, current, completion, finish, modeFor, seen, record, setReason, schedule, totals, dueItems, noteHTML, reasonHTML, history, modeOptions, help, addTime, cancelTime, timeTotal };
})();
