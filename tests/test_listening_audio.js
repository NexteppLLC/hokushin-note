/* Run after export_app.py and build_app.py: node tests/test_listening_audio.js */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const read = file => fs.readFileSync(path.join(root, file), 'utf8');
const data = JSON.parse(read('data/app/content.json'));
const ctx = vm.createContext({ document: { addEventListener() {} },
  esc: s => String(s).replace(/[&<>"']/g, c => '&#' + c.charCodeAt(0) + ';') });
vm.runInContext(read('app/js/40_learn.js').replace(
  'return { render, open, rerenderBlock, refreshNotes, state: st };',
  'return { audioHTML, render, open, rerenderBlock, refreshNotes, state: st };'
), ctx);
const expected = Array.from({ length: 8 }, (_, i) => 'L' + (i + 1)).concat('M1', 'M2');
const found = [];
for (const ed of data.editions) for (const subject of ed.subjects) for (const unit of subject.units) {
  ctx.unit = unit;
  const html = vm.runInContext('Learn.audioHTML(unit)', ctx);
  if (!unit.audio) { assert.equal(html, ''); continue; }
  assert.equal(ed.id, 'h5');
  assert.equal(subject.id, 'english');
  assert(unit.content.some(c => c.t === 'script'), 'audio must belong to a script unit');
  assert.equal(unit.audio, `audio/h5/english/${unit.code}.mp3`);
  assert(fs.statSync(path.join(root, 'docs', unit.audio)).size > 10000, 'missing/empty MP3');
  assert.match(html, /<audio controls preload="metadata"/);
  assert(html.includes('src="' + unit.audio + '"'));
  assert(!html.includes('autoplay'));
  assert(html.includes('公式音声ではありません'));
  found.push(unit.code);
}
assert.deepEqual(found.sort(), expected.sort());
const published = read('docs/index.html');
assert(published.includes('audioHTML(u) +'), 'published view must render the player');
assert(published.includes('audio/h5/english/L5.mp3'), 'published data lost the audio mapping');
console.log('All 10 listening units have playable controls and existing MP3 assets in the rebuilt site.');
