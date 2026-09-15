/* Failure/recovery regression tests. Run: node tests/test_storage.js */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const core = fs.readFileSync('app/js/00_core.js', 'utf8');
const fixture = { editions: [{ id: 'h5', subjects: [], plan: { days: [] } }] };
function context(extra = {}) {
  const status = {textContent: ''};
  const ctx = vm.createContext({console: {warn(){}}, setTimeout(){return 1;}, clearTimeout(){},
    document: { getElementById(){return {textContent:JSON.stringify(fixture)};},
      querySelector(s){return s === '#save-status' ? status : null;}, addEventListener(){} },
    window: {addEventListener(){}}, ...extra});
  vm.runInContext(core, ctx);
  vm.runInContext("showSaveError = e => setStatus(e.name);", ctx);
  return {ctx, status, run:s=>vm.runInContext(s,ctx)};
}
const named = name => Object.assign(new Error(name), {name});
(async () => {
  // An oversized drawing must stay pending while smaller progress records save.
  const c = context(); const saved = new Map(); let full = true;
  c.ctx.persist = async (k,v) => {if(full && k.startsWith('ink/')) throw named('QuotaExceededError'); saved.set(k,v);};
  c.run("Store.set = persist; S.ink.a = {strokes:[1,2]}; S.progress.a = {grade:2}; S.notes.list = ['keep']; markDirty('ink/a'); markDirty('progress/a'); markDirty('notes/all');");
  assert.equal(await c.run('flush()'), false);
  assert(saved.has('progress/a') && saved.has('notes/all'));
  assert.deepEqual(Array.from(c.run('dirty')), ['ink/a']);
  assert.equal(c.status.textContent, 'QuotaExceededError');
  c.run("markDirty('settings/main')");
  assert.equal(c.status.textContent, 'QuotaExceededError', 'new edits must not hide failure');
  full = false;
  assert.equal(await c.run('flush()'), true);
  assert.equal(c.run('dirty.size'), 0);
  assert.deepEqual(Array.from(saved.get('ink/a').strokes), [1,2]);
  // Serialize flushes; an edit while a save is in flight remains pending.
  let release; let calls = 0;
  c.ctx.persist = (k,v) => {calls++; return new Promise(res=>{release=()=>{saved.set(k,v);res();};});};
  c.run("Store.set=persist; S.plan.log={v:1}; markDirty('plan/main');");
  const first = c.run('flush()'); const second = c.run('flush()');
  assert.equal(first, second); assert.equal(calls,1);
  c.run("S.plan.log.v=2; markDirty('plan/main');"); release();
  assert.equal(await first,false);
  assert(c.run("dirty.has('plan/main')"));
  const next = c.run('flush()'); release(); await next;
  assert.equal(saved.get('plan/main').log.v,2);
  // Request success is NOT commit success; a late quota abort must reject.
  let transaction, opens=0, closed=false;
  const database = {objectStoreNames:{contains:()=>true},close(){}, transaction(){
    if(closed) {closed=false; throw named('InvalidStateError');}
    transaction = {objectStore(){return {put(){return {};},delete(){return {};},clear(){return {};}}},abort(){}};
    return transaction;
  }};
  const idb = {open(){opens++; const req={result:database}; queueMicrotask(()=>req.onsuccess()); return req;}};
  const d=context({indexedDB:idb}); await d.run('Store.open()');
  let settled=false;
  const write=d.run("Store.set('progress/a',{g:2})").then(()=>{settled=true;},e=>{settled=e.name;});
  await new Promise(setImmediate);
  assert.equal(settled,false,'must wait for transaction.oncomplete');
  transaction.error=named('QuotaExceededError'); transaction.onabort(); await write;
  assert.equal(settled,'QuotaExceededError');
  assert.equal(opens,1,'quota must not trigger another connection');
  closed=true;
  const retry=d.run("Store.set('progress/a',{g:2})");
  await new Promise(setImmediate);
  assert.equal(opens,2,'closed connection must reopen');
  transaction.oncomplete(); await retry;
  // localStorage failures must never become false memory-only successes.
  const l=context({indexedDB:{open(){throw named('SecurityError');}},localStorage:{setItem(){throw named('QuotaExceededError');}}});
  await l.run('Store.open()');
  await assert.rejects(l.run("Store.set('notes/all',{})"),{name:'QuotaExceededError'});
  assert.equal(l.run('Store.mode()'),'ls');
  console.log('Storage: quota retention, other-record saves, retries, concurrent edits, transaction abort and connection recovery passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
