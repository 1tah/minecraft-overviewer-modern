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
    updated_at: 1000, elapsed_seconds: 455.9, total: 999999, done: 99,
    renders: [{world: 'CublayCraft-Nether', id: 'nether', total: 229780, done: 7599, initial_done: 0}]};
let view = util.formatRenderProgress(data, 'CublayCraft-Nether', 'nether', 1001);
assert.match(view.message, /Готово 7599 из 229780 тайлов \(3\.3%\)/);
assert.match(view.message, /Осталось 222181 тайлов/);
assert.match(view.message, /Осталось ~223 мин/);
assert.equal(view.stale, false);
assert.equal(util.formatRenderProgress(data, 'CublayCraft-Nether', 'nether', 1091).stale, true);
data.renders[0].initial_done = 7599;
assert.match(util.formatRenderProgress(data, 'CublayCraft-Nether', 'nether', 1001).message, /Осталось —$/);
data.renders[0].done = 229780;
view = util.formatRenderProgress(data, 'CublayCraft-Nether', 'nether', 1001);
assert.equal(view.message, 'CublayCraft-Nether · Готово: 229780 из 229780 тайлов (100.0%)');
assert.equal(view.showBar, false);
data.status = 'complete';
assert.equal(util.formatRenderProgress(data, 'CublayCraft-Nether', 'nether', 1001).showBar, false);
data.status = 'interrupted';
data.phase = 'Прервано';
assert.equal(util.formatRenderProgress(data, null, null, 2000).stale, false);
assert.equal(util.formatRenderProgress({message:'legacy'}, null, null, 0).message, 'legacy');
const url = util.getTileUrlGenerator('nether', '', 'png');
assert.equal(url({x:0,y:0,z:0}), 'nether/base.png?c=old');
context.overviewerConfig.map.liveTileVersion = 'run:5';
assert.equal(url({x:0,y:0,z:0}), 'nether/base.png?c=old&live=run%3A5');
console.log('Web progress formatter, resume ETA, stale status and tile refresh: passed');
