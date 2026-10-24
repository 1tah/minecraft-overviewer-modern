// Run: node test/test_webprogress_js.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const context = {overviewer: {}, overviewerConfig: {map: {cacheTag: 'old'}}};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, '../overviewer_core/data/js_src/util.js'), 'utf8'), context);
const util = context.overviewer.util;
const data = {version: 2, config_ready: true, status: 'rendering', phase: 'Рендер',
    updated_at: 1000, elapsed_seconds: 455.9, total: 229790, done: 7609, eta_seconds: 13320,
    renders: [{world: 'Nether', title: 'Ночь', id: 'nether_night', total: 229780, done: 7599, initial_done: 0},
              {world: 'Overworld', title: 'День', id: 'overworld', total: 10, done: 10, initial_done: 10}]};
let view = util.formatRenderProgress(data, 'Overworld', 'overworld', 1001);
assert.match(view.message, /Общий рендер/);
assert.match(view.message, /Сейчас: Nether — Ночь/);
assert.match(view.message, /Готово 7609 из 229790 тайлов/);
assert.match(view.message, /Осталось 222181 тайлов/);
assert.match(view.message, /Осталось ~222 мин/);
assert.equal(view.showBar, true);
assert.equal(view.stale, false);
assert.equal(view.message, util.formatRenderProgress(data, 'Nether', 'nether_night', 1001).message);
data.renders.push({world: 'End', title: 'Край', id: 'end', total: 0, done: 0, initial_done: 0});
assert.equal(view.message, util.formatRenderProgress(data, 'End', 'end', 1001).message);
assert.equal(util.formatRenderProgress(data, 'Overworld', 'overworld', 1091).stale, true);
data.renders.push({world: 'Nether', title: 'Север', id: 'north', total: 0, done: 0, skipped: true});
assert.doesNotMatch(util.formatRenderProgress(data, null, null, 1001).message, /Север/);
data.status = 'complete';
data.done = data.total;
view = util.formatRenderProgress(data, 'Overworld', 'overworld', 1001);
assert.equal(view.message, 'Общий рендер · Готово: 229790 из 229790 тайлов (100.0%)');
assert.equal(view.showBar, false);
data.total = data.done = 0;
assert.equal(util.formatRenderProgress(data, null, null, 1001).message, 'Карта актуальна · Изменений для рендера нет');
data.status = 'interrupted';
data.phase = 'Прервано';
assert.equal(util.formatRenderProgress(data, null, null, 2000).stale, false);
assert.equal(util.formatRenderProgress({message:'legacy'}, null, null, 0).message, 'legacy');
const url = util.getTileUrlGenerator('nether', '', 'png');
assert.equal(url({x:0,y:0,z:0}), 'nether/base.png?c=old');
context.overviewerConfig.map.liveTileVersion = 'run:5';
assert.equal(url({x:0,y:0,z:0}), 'nether/base.png?c=old&live=run%3A5');
console.log('Web progress formatter, resume ETA, stale status and tile refresh: passed');
