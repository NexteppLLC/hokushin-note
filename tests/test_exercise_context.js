/* Run after export_app.py: node tests/test_exercise_context.js [baseline-content.json] */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const content = fs.readFileSync(path.join(root, 'data/app/content.json'), 'utf8');
const core = fs.readFileSync(path.join(root, 'app/js/00_core.js'), 'utf8');
const learn = fs.readFileSync(path.join(root, 'app/js/40_learn.js'), 'utf8').replace(
  'return { render, open, rerenderBlock, refreshNotes, state: st };',
  'return { render, open, rerenderBlock, refreshNotes, state: st, testRender: renderBlock, testVisible: visible };'
);
function contextFor(json) {
  const ctx = vm.createContext({ console, setTimeout, clearTimeout,
    document: {
      getElementById: () => ({ textContent: json }), addEventListener() {},
      createElement: () => ({ set innerHTML(value) { this.content = { firstElementChild: { outerHTML: value } }; } })
    }, window: { addEventListener() {} }
  });
  vm.runInContext(core, ctx);
  const historyPath = path.join(root, 'app/js/05_history.js');
  if (fs.existsSync(historyPath)) vm.runInContext(fs.readFileSync(historyPath, 'utf8'), ctx);
  return ctx;
}
const ctx = contextFor(content);
vm.runInContext(learn, ctx);
vm.runInContext(`
  const unit = SUBJ.science.byCode.R13, block = unit.content[2];
  const question = unit.items.find(i => i.ci === 2 && i.n === 1);
  if (question.key !== 'h5:science/R13#2:1') throw Error('persistent item key changed');
  if (!question.context.includes('<svg')) throw Error('card lost its shared circuit');
  if (question.q.includes('<svg')) throw Error('shared circuit duplicated in question');
  const card = studyCard(question, 'science');
  if (!card.context.includes('<svg') || !card.label.includes('(1)')) throw Error('card adapter lost context or numbering');
  ['all', 'ex'].forEach(tab => {
    Learn.state.tab = tab;
    if (!Learn.testVisible(block)) throw Error('exercise hidden');
    const rendered = Learn.testRender(unit, block).outerHTML;
    const originalCount = (block.context.match(/<svg/g) || []).length;
    if ((rendered.match(/<svg/g) || []).length !== originalCount) throw Error('shared circuit absent or duplicated');
  });
  Learn.state.tab = 'ex';
  if (!Learn.testVisible({t:'q'}) || !Learn.testVisible({t:'data'})) throw Error('raw question or data hidden in exercises');
  Learn.state.tab = 'points';
  if (Learn.testVisible({t:'q'})) throw Error('raw question incorrectly shown as a knowledge point');
  const answerUnit = SUBJ.science.units.find(u => u.code === 'M1' && u.title.includes('解答'));
  if (answerUnit && answerUnit.content.filter(c => c.t === 'a').some(c => !(c.answerKeys || []).length)) throw Error('a separated mock answer lost its question exposure mapping');
`, ctx);
const baseline = process.argv[2];
if (baseline) {
  const previous = contextFor(fs.readFileSync(baseline, 'utf8'));
  const keys = vm.runInContext('EDITIONS.flatMap(e => e.subjects.flatMap(s => s.units.flatMap(u => u.items.map(it => it.key))))', previous);
  const newKeys = new Set(vm.runInContext('EDITIONS.flatMap(e => e.subjects.flatMap(s => s.units.flatMap(u => u.items.map(it => it.key))))', ctx));
  assert(keys.every(key => newKeys.has(key)), 'an existing grade key disappeared');
  const oldShape = vm.runInContext('EDITIONS.flatMap(e => e.subjects.flatMap(s => s.units.map(u => [u.ukey, u.content.length])))', previous);
  const newShape = vm.runInContext('EDITIONS.flatMap(e => e.subjects.flatMap(s => s.units.map(u => [u.ukey, u.content.length])))', ctx);
  const shapeMap = new Map(newShape);
  assert(oldShape.every(([ukey, count]) => shapeMap.has(ukey) && shapeMap.get(ukey) >= count), 'an existing unit or block position disappeared');
  console.log('Preserved ' + keys.length + ' existing item keys and the original units/block slots (additional content allowed).');
}
console.log('Question contexts, mock visibility, and card adapters passed.');
