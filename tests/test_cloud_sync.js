/* node tests/test_cloud_sync.js — no credentials or live Firestore writes */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const now=Date.UTC(2026,8,20,4), storage=new Map([
 ['hn-cloud-config-v1',JSON.stringify({apiKey:'test',projectId:'test'})],
 ['hn-cloud-writer-v1','1'],['hn-cloud-device-id-v1','student']]);
const rows=new Map(),calls=[];let rejectCommit=false,requests=0,txCallback=null;
const ref=path=>({path,collection:n=>ref(path+'/'+n),doc:n=>ref(path+'/'+n)});
const db={collection:n=>ref(n),async runTransaction(fn){requests++;if(txCallback)await txCallback();const batch=[];await fn({get:async r=>({exists:rows.has(r.path),data:()=>rows.get(r.path)}),set:(r,data)=>batch.push([r.path,data])});if(rejectCommit)throw Object.assign(new Error('test denied'),{code:'permission-denied'});for(const [path,data]of batch)rows.set(path,data);calls.push(batch);}};
const auth={currentUser:{uid:'family'},setPersistence:async()=>{},onAuthStateChanged(fn){fn(this.currentUser)}};
function firestore(){return db;}firestore.FieldValue={serverTimestamp:()=>({seconds:now/1000})};
function authAPI(){return auth;}authAPI.Auth={Persistence:{LOCAL:'local'}};
const firebase={apps:[{}],app:()=>({}),auth:authAPI,firestore};
const progress={graded:120,done:40};
const S={settings:{},progress:{},plan:{done:{'h5|1:E:G1':1}}};
const fixture={console:{warn(){}},Date,Promise,setTimeout:()=>1,clearTimeout(){},setInterval:()=>1,clearInterval(){},
 window:{firebase,addEventListener(){},dispatchEvent(){}},document:{addEventListener(){}},firebase,
 localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},
 $:()=>null,uid:()=>String(Math.random()),toast:()=>{},flush:async()=>true,Settings:{render(){}},App:{boot:async()=>{}},
 S,DATA:{subjects:[{id:'english',key:'E',name:'英語'}]},ED:{id:'h5',name:'第5回'},SUBJ_ORDER:['E'],SUBJ_BY_KEY:{E:{id:'english',name:'英語'}},
 PLAN:{test_day:'2026-10-11',days:[{day:1,date:'2026-09-20',weekday:'日',tasks:{E:[{code:'G1',title:'文法',minutes:10}]}}]},
 todayISO:()=> '2026-09-20',addDays:()=> '2026-09-14',taskKey:(d,sk,c)=>`h5|${d}:${sk}:${c}`,
 subjectStats:()=>({items:3900,graded:progress.graded,ok:100,ng:20,units:348,unitsDone:progress.done}),Study:{totals:()=>({}),timeTotal:()=>0}
};
const ctx=vm.createContext(fixture),run=code=>vm.runInContext(code,ctx);
for(const file of ['95_cloud.js','96_cloud_tasks.js'])run(fs.readFileSync('app/js/'+file,'utf8'));
const current='users/family/hokushin/current',schedule='users/family/hokushin/schedule';
(async()=>{
 await run('CloudSync.init()');
 assert.equal(await run('CloudSync.syncNow(false)'),true);
 assert.equal(calls[0].length,4,'summary, schedule and both dated snapshots must commit together');
 assert.equal(rows.get(current).syncId,rows.get(schedule).syncId);
 assert.equal(rows.get(schedule).days[0].tasks[0].done,true,'manual sync must include latest checkboxes');
 // Other device with fewer records cannot replace the stored data.
 storage.set('hn-cloud-device-id-v1','parent');progress.graded=119;
 assert.equal(await run('CloudSync.syncNow(true)'),false);assert.equal(calls.length,1);
 storage.set('hn-cloud-device-id-v1','student');progress.graded=120;
 // Schedule guard prevents independent overwrite even if summary would pass.
 const oldSchedule=rows.get(schedule);rows.set(schedule,{...oldSchedule,deviceId:'other',days:[{tasks:[{done:true},{done:true}]}]});
 assert.equal(await run('TaskProgressSync.syncNow(true)'),false);assert.equal(calls.length,1);
 rows.set(schedule,oldSchedule);
 // Failed commit cannot replace either current doc or its dated snapshot.
 rejectCommit=true;progress.graded=121;
 assert.equal(await run('CloudSync.syncNow(true)'),false);assert.equal(rows.get(current).overall.graded,120);assert.equal(calls.length,1);
 rejectCommit=false;
 // Overlapping timers share one flight; sender is rechecked after async reads.
 let release;txCallback=()=>new Promise(r=>release=r);const before=requests;
 const p1=run('CloudSync.syncNow(true)'),p2=run('TaskProgressSync.syncNow(false)');assert.equal(requests,before+1);
 storage.delete('hn-cloud-writer-v1');release();assert.equal(await p1,false);assert.equal(await p2,false);assert.equal(calls.length,1);
 assert.equal(await run('CloudSync.syncNow(false)'),false);assert.equal(requests,before+1);
 txCallback=null;storage.set('hn-cloud-writer-v1','1');
 assert.equal(await run('CloudSync.syncNow(false)'),true);assert.equal(rows.get(current).overall.graded,121);
 // Exercise the published parent's date/freshness logic against an old snapshot.
 const html=fs.readFileSync('docs/parent.html','utf8');const script=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m=>m[1]).filter(Boolean).join('\n').replace(/\ninit\(\);/,'\n');
 class Clock extends Date{constructor(...args){super(...(args.length?args:[now]));}static now(){return now;}}
 const elements=new Map();const parent=vm.createContext({Date:Clock,console,setInterval(){},document:{querySelector:s=>{if(!elements.has(s))elements.set(s,{});return elements.get(s);},querySelectorAll:()=>[],addEventListener(){}},window:{addEventListener(){}},localStorage:{getItem:()=>null}});
 vm.runInContext(script,parent);const pr=s=>vm.runInContext(s,parent);
 pr(`summary={editionId:'h5',editionName:'第5回',today:'2026-09-18',clientUpdatedAt:${now-2*86400000},overall:{graded:4},actualStudy:{todayMinutes:50},plan:{},syncId:'a'};summaryCached=false;schedule={editionId:'h5',syncId:'a',days:[{date:'2026-09-20',tasks:[{done:true}]}]};scheduleCached=false;`);
 assert.equal(pr('todayKey()'),'2026-09-20');assert.equal(pr('filteredDays()[0].date'),'2026-09-20');
 assert.equal(pr('staleSummary()'),true);assert(pr('freshnessHTML()').includes('最新の記録が届いていない可能性'));
 assert(pr('summaryHTML(summary)').includes('<span>今日の実学習</span><b>—</b>'),'old daily minutes must not appear as today');
 pr('updateConnection()');assert.equal(elements.get('#conn').textContent,'更新待ち（古い記録）');
 pr("schedule.syncId='b'");assert.equal(pr('matchingSchedule()'),false);assert(pr('taskSectionHTML()').includes('同じ更新時点'));
 pr("summaryCached=true;updateConnection()");assert.equal(elements.get('#conn').textContent,'サーバー確認待ち');
 console.log('PASS: atomic manual/automatic sync, regression guards, failure retention, overlap, writer revocation, stale dates and mismatched/cached dashboard.');
})().catch(e=>{console.error(e);process.exitCode=1});
