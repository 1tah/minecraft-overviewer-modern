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
    run_id: 'test-run', updated_at: 1000, elapsed_seconds: 455.9, total: 229790, done: 7609, eta_seconds: 13320,
    renders: [{world: 'Nether', title: 'Ночь', id: 'nether_night', total: 229780, done: 7599, initial_done: 0},
              {world: 'Overworld', title: 'День', id: 'overworld', total: 10, done: 10, initial_done: 10}]};
const previous = {run_id: 'test-run', renders: [{id:'nether_night', done:7590}]};
const format = (d,w,p,n) => util.formatRenderProgress(d,w,p,n,previous);
let view = format(data, 'Overworld', 'overworld', 1001);
assert.match(view.message, /Общий рендер/);
assert.match(view.message, /Активный слой: Nether — Ночь/);
assert.match(view.message, /Готово 7609 из 229790 тайлов/);
assert.match(view.message, /Осталось 222181 тайлов/);
assert.match(view.message, /Осталось ~03:42/);
assert.equal(view.showBar, true);
assert.equal(view.stale, false);
assert.equal(view.message, format(data, 'Nether', 'nether_night', 1001).message);
data.renders.push({world: 'End', title: 'Край', id: 'end', total: 0, done: 0, initial_done: 0});
assert.equal(view.message, format(data, 'End', 'end', 1001).message);
assert.equal(format(data, 'Overworld', 'overworld', 1091).stale, true);
data.renders.push({world: 'Nether', title: 'Север', id: 'north', total: 0, done: 0, skipped: true});
assert.doesNotMatch(format(data, null, null, 1001).message, /Север/);
const other = {...data, renders: [...data.renders,
    {world:'Views', title:'Восток', id:'east', total:100, done:80}]};
const active = util.formatRenderProgress(other, null, null, 1001,
    {run_id:'test-run', renders:[{id:'nether_night',done:7598}, {id:'east',done:40}]});
assert.match(active.message, /Активный слой: Views — Восток/);
assert.doesNotMatch(active.message, /Nether — Ночь/);
assert.doesNotMatch(util.formatRenderProgress(other, null, null, 1001).message, /Активный слой/);
data.status = 'complete';
data.done = data.total;
view = format(data, 'Overworld', 'overworld', 1001);
assert.equal(view.message, 'Общий рендер · Готово: 229790 из 229790 тайлов (100.0%)');
assert.equal(view.showBar, false);
data.total = data.done = 0;
assert.equal(format(data, null, null, 1001).message, 'Карта актуальна · Изменений для рендера нет');
data.status = 'interrupted';
data.phase = 'Прервано';
assert.equal(format(data, null, null, 2000).stale, false);
assert.equal(util.formatRenderProgress({message:'legacy'}, null, null, 0).message, 'legacy');
const url = util.getTileUrlGenerator('nether', '', 'png');
assert.equal(url({x:0,y:0,z:0}), 'nether/base.png?c=old');
context.overviewerConfig.map.liveTileVersion = 'run:5';
assert.equal(url({x:0,y:0,z:0}), 'nether/base.png?c=old&live=run%3A5');
console.log('Web progress formatter, resume ETA, stale status and tile refresh: passed');

const liveResources = {...data, total:100, done:40, status:'rendering', phase:'Рендер',
    resources:{memory_used_bytes:3.25*1073741824, memory_limit_bytes:10*1073741824,
        memory_peak_bytes:4*1073741824, workers_current:4, workers_starting:1, worker_limit:12}};
const liveLabel = format(liveResources, null, null, 1001).message;
assert.match(liveLabel, /RAM 3.3\/10.0 ГиБ/);
assert.match(liveLabel, /Воркеры 4\/12 \(запуск 1\)/);
assert.doesNotMatch(format(liveResources, null, null, 1091).message, /RAM|Воркеры/);
const finishedResources = {...liveResources, status:'complete', done:100};
const finishedLabel = format(finishedResources, null, null, 1001);
assert.match(finishedLabel.message, /Пик RAM 4.0 ГиБ/);
assert.doesNotMatch(finishedLabel.message, /Воркеры|Осталось/);
assert.equal(finishedLabel.showBar, false);
const preparingLabel = format({...liveResources, status:'preparing', config_ready:false}, null, null, 1001);
assert.match(preparingLabel.message, /RAM 3.3\/10.0 ГиБ/);
console.log('Live RAM, worker counts, starting workers, terminal peak and stale readings: passed');
assert.equal(util.formatRemainingTime(null), '—');
assert.equal(util.formatRemainingTime(Infinity), '—');
assert.equal(util.formatRemainingTime(37*60), '~37 мин');
assert.equal(util.formatRemainingTime(59*60), '~59 мин');
assert.equal(util.formatRemainingTime(59*60+1), '~01:00');
assert.equal(util.formatRemainingTime(60*60), '~01:00');
assert.equal(util.formatRemainingTime(135*60), '~02:15');
assert.equal(util.formatRemainingTime(25*3600+60), '~25:01');
const compact = format(liveResources, null, null, 1001);
assert.equal(compact.title, 'Nether — Ночь');
assert.equal(compact.counts, '40 из 100 тайлов · 40.0%');
assert.match(compact.details, /60 тайлов осталось/);
assert.match(compact.details, /Осталось ~03:42/);
assert.match(compact.details, /RAM 3.3\/10.0 ГиБ/);
assert.doesNotMatch(finishedLabel.details, /осталось|Осталось|Воркеры/);
console.log('Compact two-line layout and minute/hour ETA boundaries: passed');
const finalSummary = format({...finishedResources, total:13634, done:13634, elapsed_seconds:383.9,
    resources:{memory_peak_bytes:7.5*1073741824, workers_peak:8}}, null, null, 1001);
assert.equal(finalSummary.title, 'Рендер завершён');
assert.equal(finalSummary.counts, '13 634 из 13 634 тайлов · 100.0%');
assert.match(finalSummary.details, /Время рендера 6 мин 24 с/);
assert.match(finalSummary.details, /Пик RAM 7.5 ГиБ/);
assert.match(finalSummary.details, /Воркеры: до 8/);
assert.doesNotMatch(finalSummary.details, /Осталось/);
assert.equal(finalSummary.showBar, false);
assert.equal(util.formatElapsedTime(0), '0 с');
assert.equal(util.formatElapsedTime(59), '59 с');
assert.equal(util.formatElapsedTime(60), '1 мин 0 с');
assert.equal(util.formatElapsedTime(3661), '01:01:01');
assert.equal(util.formatElapsedTime(null), '');
console.log('Explicit tile labels and completed render duration/RAM/worker summary: passed');
