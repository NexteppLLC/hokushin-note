/* Run: node tests/test_history.js (no browser or third-party dependencies). */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
let now = Date.UTC(2026, 8, 8, 12);
class Clock extends Date { constructor(...args) { super(...(args.length ? args : [now])); } static now() { return now; } }
const fixture = { editions: [{ id: 'h5', subjects: [{ id: 'science', key: 'S', name: '理科', short: '理', units: [{ code: 'R13', codes: ['R13'], title: '回路', content: [{ t: 'ex', title: '実験', items: Array.from({length: 6}, (_, i) => ({ n: i + 1, l: '(' + (i + 1) + ')', q: '問題' + i, a: '答え' + i })) }] }], ruby: true }], plan: { days: [] } }] };
const fakeElement = () => ({ children: [], classList: { add() {} }, appendChild(x) { this.children.push(x); }, querySelector() { return {}; }, style: {} });
const ctx = vm.createContext({ console, Date: Clock, setTimeout() {}, clearTimeout() {},
  document: { getElementById: () => ({ textContent: JSON.stringify(fixture) }), addEventListener() {},
    createElement: () => ({ set innerHTML(value) { this.content = { firstElementChild: Object.assign(fakeElement(), { outerHTML: value }) }; } }) },
  window: { addEventListener() {} }
});
function load(file) { vm.runInContext(fs.readFileSync(path.join(root, 'app/js', file), 'utf8'), ctx, {filename:file}); }
load('00_core.js'); load('05_history.js'); load('20_hl.js'); load('80_settings.js');
vm.runInContext("markDirty = () => {}; logActivity = () => {}; flush = async () => {}; toast = () => {}; confirmBox = async () => true; Store.clear = async () => {}; const App = { applyFs() {}, show() {} };", ctx);
const run = code => vm.runInContext(code, ctx);
const json = code => JSON.parse(run('JSON.stringify(' + code + ')'));
const key = n => 'h5:science/R13#0:' + n;
run(`const firstKey = '${key(1)}', previewKey = '${key(2)}', legacyKey = '${key(3)}', reasonKey = '${key(4)}';`);

run("progOf(legacyKey).items[legacyKey] = {g:2,t:1,custom:{keep:'yes'}}; Study.migrateAll(S);");
assert.deepEqual(json('progOf(legacyKey).items[legacyKey].legacy'), {g:2,t:1,custom:{keep:'yes'}});
assert.equal(json('Study.totals()').first, 0, 'legacy grades excluded');
run("const initial = Study.session('auto','test'); Study.finish(firstKey,initial); Study.seen(firstKey); setGrade('science',firstKey,0,{session:initial});");
assert.equal(json('Study.effective(progOf(firstKey).items[firstKey])')[0].mode, 'first', 'completion before answer preserves first mode');
run("setGrade('science',firstKey,0,{session:initial});");
assert.equal(json('progOf(firstKey).items[firstKey].attempts').length, 1, 'identical redraw/repeated submit is idempotent');
run("setGrade('science',firstKey,2,{session:initial});");
assert.equal(json('progOf(firstKey).items[firstKey].attempts').length, 2, 'correction retained in append-only event log');
assert.equal(json('Study.effective(progOf(firstKey).items[firstKey])').length, 1, 'correction is one attempt');
assert.deepEqual(json('[Study.totals().first, Study.totals().firstOk]'), [1,1]);
run("setGrade('science',firstKey,null,{session:initial});");
assert.equal(json('Study.totals()').first, 0, 'cancelled attempt not counted');
run("setGrade('science',firstKey,2,{session:initial});");
now += 5 * 60000;
run("const retry = Study.session('auto','test'); Study.finish(firstKey,retry); Study.seen(firstKey); setGrade('science',firstKey,2,{session:retry});");
assert.equal(json('Study.effective(progOf(firstKey).items[firstKey])').at(-1).mode, 'review');
assert.equal(json('Study.totals()').retest, 0);
now += 86400000 - 1;
run("const tooEarly = Study.session('retest','test'); Study.finish(firstKey,tooEarly); Study.seen(firstKey); setGrade('science',firstKey,2,{session:tooEarly});");
assert.equal(json('Study.effective(progOf(firstKey).items[firstKey])').at(-1).mode, 'review', '23h59m59.999s cannot pass delayed test');
assert.equal(json('Study.totals()').retest, 0);
now += 86400000;
run("const delayed = Study.session('retest','test'); Study.finish(firstKey,delayed); Study.seen(firstKey); setGrade('science',firstKey,2,{session:delayed});");
assert.equal(json('Study.effective(progOf(firstKey).items[firstKey])').at(-1).mode, 'retest', '24 hours exactly qualifies');
assert.equal(json('Study.schedule(progOf(firstKey).items[firstKey])').days, 3);
now += 3 * 86400000;
assert(json('Study.dueItems()').some(x => x.it.key === key(1)), '3-day due item appears');
run("const delayedAgain = Study.session('retest','test'); Study.finish(firstKey,delayedAgain); Study.seen(firstKey); setGrade('science',firstKey,2,{session:delayedAgain});");
assert.equal(json('Study.schedule(progOf(firstKey).items[firstKey])').days, 7);
run("const sameDay = Study.session('review','test'); Study.finish(firstKey,sameDay); Study.seen(firstKey); setGrade('science',firstKey,2,{session:sameDay});");
assert.equal(json('Study.totals()').retest, 2, 'same-day correction cannot raise retest count');
assert.equal(json('Study.schedule(progOf(firstKey).items[firstKey])').days, 7);
run("const failed = Study.session('review','test'); setGrade('science',firstKey,0,{session:failed});");
assert.equal(json('Study.schedule(progOf(firstKey).items[firstKey])').days, 1);
run("Study.seen(previewKey); const previewRun = Study.session('auto','test'); Study.finish(previewKey,previewRun); setGrade('science',previewKey,2,{session:previewRun});");
assert.equal(json('Study.effective(progOf(previewKey).items[previewKey])')[0].mode, 'review', 'preview before response completion excludes first');
run("const reasonRun = Study.session('auto','test'); Study.setReason(reasonKey,'visual',reasonRun); Study.finish(reasonKey,reasonRun); Study.seen(reasonKey); setGrade('science',reasonKey,0,{session:reasonRun}); Study.setReason(reasonKey,'conditions',reasonRun);");
assert.equal(json('Study.effective(progOf(reasonKey).items[reasonKey])')[0].reason, 'conditions');
assert.equal(json('Study.effective(progOf(reasonKey).items[reasonKey])').length, 1);
// A correction to Learn's old run cannot overwrite a later Cards result.
run("const crossKey = 'h5:science/R13#0:5'; const learnRun = Study.session('auto','learn'); setGrade('science',crossKey,0,{session:learnRun});");
now += 1000;
run("const cardRun = Study.session('review','cards'); setGrade('science',crossKey,2,{session:cardRun}); const cardTimestamp = progOf(crossKey).items[crossKey].t;");
now += 1000;
run("Study.setReason(crossKey,'visual',learnRun);");
assert.equal(run('progOf(crossKey).items[crossKey].g'),2,'old Learn reason correction cannot replace newer Cards circle');
assert.equal(run('progOf(crossKey).items[crossKey].t'),run('cardTimestamp'),'latest timestamp comes from newest effective attempt');
assert.equal(json('Study.effective(progOf(crossKey).items[crossKey])')[0].reason,'visual');
assert.equal(json('Study.effective(progOf(crossKey).items[crossKey])').length,2);
run("setGrade('science',crossKey,null,{session:cardRun});");
assert.equal(run('progOf(crossKey).items[crossKey].g'),0,'cancelling latest restores previous effective cross');
run("setGrade('science',crossKey,null,{session:learnRun});");
assert.equal(run('progOf(crossKey).items[crossKey].g'),undefined,'no grade when all attempts cancelled and no legacy');
assert.equal(json('progOf(crossKey).items[crossKey].attempts').length,5,'cancellation retains all original/correction events');
// With a legacy result, cancellation returns to the exact old grade/time.
run("const legacyRetry = Study.session('review','test'); setGrade('science',legacyKey,0,{session:legacyRetry}); setGrade('science',legacyKey,null,{session:legacyRetry});");
assert.equal(run('progOf(legacyKey).items[legacyKey].g'),2);
assert.equal(run('progOf(legacyKey).items[legacyKey].t'),1);
assert.deepEqual(json('progOf(legacyKey).items[legacyKey].legacy'),{g:2,t:1,custom:{keep:'yes'}});
// Equal completion times still use original attempt order, not correction time.
run("const tieKey = 'h5:science/R13#0:6'; const tieOlder = Study.session('auto','learn'); setGrade('science',tieKey,0,{session:tieOlder}); const tieNewer = Study.session('review','cards'); setGrade('science',tieKey,2,{session:tieNewer});");
now += 1000;
run("Study.setReason(tieKey,'conditions',tieOlder);");
assert.equal(run('progOf(tieKey).items[tieKey].g'),2,'same-millisecond attempts are not reordered by older correction');
assert.equal(json('Study.effective(progOf(tieKey).items[tieKey])').at(-1).attemptId,run('tieNewer.id + ":" + tieKey'));
run("setGrade('science',tieKey,null,{session:tieOlder});");
assert.equal(run('progOf(tieKey).items[tieKey].g'),2,'cancelling an old run preserves newer result');
assert(run("Study.addTime(todayISO(),40)"));
assert(!run("Study.addTime(todayISO(),-1)"));
assert(!run("Study.addTime('2026-02-30',40)"));
assert.equal(run('Study.timeTotal(todayISO(),todayISO())'), 40);
run("Study.cancelTime(S.plan.studyTime[0].id)");
assert.equal(run('Study.timeTotal(todayISO(),todayISO())'), 0);
assert.equal(json('S.plan.studyTime').length, 1, 'cancelled manual time remains in backup');

assert.deepEqual(json("HL.resolveAnchor('資料が追加。同じ本文です。',{s:0,e:7,txt:'同じ本文です。'})"), {s:6,e:13});
assert.equal(run("HL.resolveAnchor('同じ文と同じ文',{s:99,e:103,txt:'同じ文'})"), null, 'ambiguous old highlight is hidden');
assert.equal(run("HL.resolveAnchor('異なる本文',{s:0,e:2,txt:'昔の本文'})"), null);
assert.deepEqual(json("HL.resolveAnchor('前置き A  B C',{s:99,e:110,txt:'A B C'})"), {s:4,e:10});
assert.equal(run("HL.resolveAnchor('本文',{s:0,e:2})"), null, 'unverifiable offsets not applied');

const learnSource = fs.readFileSync(path.join(root,'app/js/40_learn.js'),'utf8').replace('return { render, open, rerenderBlock, refreshNotes, state: st };','return { render, open, rerenderBlock, refreshNotes, state: st, testAttach: attachBlockInk };');
vm.runInContext("const inkCalls=[]; const Ink={ attach(host,get,change){inkCalls.push({get,change});}, isPen(){return false;} };",ctx);
vm.runInContext(learnSource,ctx);
ctx.host = fakeElement();
run("const inkUnit=SUBJ.science.byCode.R13; S.ink[inkUnit.ukey]={blocks:{0:{w:100,strokes:[{p:[10,20,30,40],c:'#000',w:2}]}}}; const inkBefore=JSON.stringify(S.ink[inkUnit.ukey].blocks[0]); Learn.testAttach(inkUnit,inkUnit.content[0],host);");
assert.equal(run('JSON.stringify(S.ink[inkUnit.ukey].blocks[0])'),run('inkBefore'),'viewing old ink cannot mutate old data');
assert.equal(json('inkCalls.at(-1).get().strokes').length,0,'old strokes not silently overlaid on changed text');
run("inkCalls.at(-1).change({w:100,strokes:[{p:[1,2,3,4],c:'#000',w:2}]});");
assert.equal(json('S.ink[inkUnit.ukey].blocks[0].previousLayouts').length,1);
assert.equal(JSON.stringify(json('S.ink[inkUnit.ukey].blocks[0].previousLayouts[0]')),run('inkBefore'),'new drawing retains original snapshot');

(async () => {
  const backup = JSON.parse(run('Settings.backupJSON()'));
  assert.equal(backup.v,3);
  const savedHistory = JSON.stringify(backup.progress);
  ctx.backupText = JSON.stringify(backup);
  await run('Settings.importBackup(backupText)');
  assert.equal(JSON.stringify(json('S.progress')),savedHistory,'v3 round-trip preserves all events/completions/legacy metadata');
  const old = {app:'hokushin-note',v:2,progress:{'h5:science':{items:{[key(5)]:{g:1,t:2,extra:'preserve'}},units:{'h5:science/R13':{d:3}}}},plan:{done:{},log:{},custom:'keep'},notes:{list:[{id:'note'}]},hl:{'h5:science/R13':[{b:0,s:0,e:2,txt:'本文'}]},ink:{test:{strokes:[1]}},nb:{test:{pages:[]}}};
  ctx.oldBackup = JSON.stringify(old);
  await run('Settings.importBackup(oldBackup)');
  assert.deepEqual(json(`S.progress['h5:science'].items['${key(5)}'].legacy`),{g:1,t:2,extra:'preserve'});
  assert.equal(run('Study.totals().first'),0);
  assert.equal(run('S.plan.custom'),'keep');
  assert.deepEqual(json('S.hl'),old.hl); assert.deepEqual(json('S.ink'),old.ink); assert.deepEqual(json('S.nb'),old.nb);
  const back = JSON.parse(run('Settings.backupJSON()')); assert.equal(back.v,3); assert(back.progress['h5:science'].items[key(5)].legacy);
  console.log('PASS: completion/preview distinction, append-only corrections/latest-result reconciliation, legacy exclusion, 24h boundary, 1/3/7-day review, optional reasons, manual time, v2/v3 backup, safe highlights, preserved old ink.');
})().catch(error => { console.error(error); process.exitCode=1; });
