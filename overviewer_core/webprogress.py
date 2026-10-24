"""Coordinator-owned atomic progress snapshots for static map hosting."""
import contextvars
import functools
import json
import logging
import os
from pathlib import Path
import threading
import time
import uuid

from .files import FileReplacer

_active = contextvars.ContextVar('overviewer_web_progress', default=None)
TERMINAL = {'complete', 'interrupted', 'error'}


def manage_lifecycle(function):
    @functools.wraps(function)
    def wrapped(*args, **kwargs):
        token = _active.set(None)
        try:
            return function(*args, **kwargs)
        except KeyboardInterrupt:
            if _active.get():
                _active.get().stop('interrupted')
            raise
        except BaseException:
            if _active.get():
                _active.get().stop('error')
            raise
        finally:
            progress = _active.get()
            if progress:
                if progress.state not in TERMINAL:
                    progress.stop('error')
                progress.close()
            _active.reset(token)
    return wrapped


class WebProgress:
    def __init__(self, outputdir, interval=2, heartbeat=True):
        self.outputdir = Path(outputdir)
        self.outputdir.mkdir(parents=True, exist_ok=True)
        self.path = self.outputdir / 'render-progress.json'
        self.run_id = uuid.uuid4().hex
        self.owner_pid = os.getpid()
        self.interval = interval
        self.state = 'preparing'
        self.phase = 'Подготовка рендера'
        self.config_ready = False
        self.rows = {}
        self.sequence = 0
        self.started = time.monotonic()
        self.render_started = None
        self.last_write = float('-inf')
        self.lock = threading.RLock()
        self._stop = threading.Event()
        self.thread = None
        self.publish(force=True)
        self._bootstrap()
        if heartbeat:
            self.thread = threading.Thread(target=self._heartbeat, daemon=True,
                                           name='overviewer-web-progress')
            self.thread.start()

    def _bootstrap(self):
        index = self.outputdir / 'index.html'
        if index.exists():
            return
        # Replaced by AssetManager once the real map configuration is available.
        page = '''<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Подготовка карты Minecraft</title>
<style>body{background:#1a1a1a;color:#eee;font:16px sans-serif;padding:3em;line-height:1.6}</style>
<h1>Карта Minecraft</h1><p id="status">Подготовка рендера…</p>
<p>Карта откроется автоматически после подготовки текстур и плана тайлов.</p>
<script>
async function tick(){try{const r=await fetch('render-progress.json?t='+Date.now(),{cache:'no-store'});
if(!r.ok)throw Error();const d=await r.json();
document.getElementById('status').textContent=d.message;
if(d.config_ready){location.reload();return;}}
catch(e){document.getElementById('status').textContent='Ожидание состояния рендера…';}
setTimeout(tick,2000);}tick();
</script></html>'''
        with FileReplacer(str(index)) as temporary:
            Path(temporary).write_text(page, encoding='utf-8')

    def stage(self, phase):
        with self.lock:
            self.phase = phase
            self.sequence += 1
            self.publish(force=True)

    def begin(self, tilesets):
        with self.lock:
            self.render_started = time.monotonic()
            for tileset in tilesets:
                pending = sum(tileset.get_phase_length(p) or 0 for p in range(tileset.get_num_phases()))
                metadata = {}
                if tileset.journal.db is not None:
                    metadata = tileset.journal.peek(tileset.options.get('resume_key')) or {}
                total = max(pending, metadata.get('jobs_total', pending))
                self.rows[id(tileset)] = dict(
                    id=tileset.options['name'], world=tileset.options['worldname_orig'],
                    title=tileset.options['title'], total=total, done=total-pending,
                    initial_done=total-pending, skipped=tileset.options['renderchecks'] == 3)
            self.state = 'rendering'
            self.phase = 'Рендер'
            self.config_ready = True
            self.sequence += 1
            self.publish(force=True)

    def completed(self, tileset):
        with self.lock:
            row = self.rows[id(tileset)]
            row['done'] = min(row['total'], row['done'] + 1)
            self.sequence += 1
            self.publish()

    def stop(self, state):
        with self.lock:
            self.state = state
            self.phase = {'complete':'Готово', 'interrupted':'Прервано',
                          'error':'Ошибка рендера; подробности в журнале'}[state]
            self.sequence += 1
            self.publish(force=True)

    def _row(self, row, elapsed):
        result = dict(row)
        remaining = max(0, row['total'] - row['done'])
        performed = row['done'] - row['initial_done']
        result.update(remaining=remaining, percent=100*row['done']/row['total'] if row['total'] else 100,
                      eta_seconds=elapsed*remaining/performed if performed else (0 if not remaining else None))
        return result

    def snapshot(self):
        elapsed = time.monotonic() - (self.render_started or self.started)
        rows = [self._row(row, elapsed) for row in self.rows.values()]
        total = sum(row['total'] for row in rows)
        done = sum(row['done'] for row in rows)
        performed = sum(row['done']-row['initial_done'] for row in rows)
        remaining = max(0, total-done)
        eta = elapsed*remaining/performed if performed else (0 if not remaining else None)
        return dict(version=2, run_id=self.run_id, sequence=self.sequence, status=self.state,
                    phase=self.phase, message=self.phase, config_ready=self.config_ready,
                    elapsed_seconds=elapsed,
                    updated_at=time.time(), update=2000 if self.state not in TERMINAL else 5000,
                    total=total, done=done, remaining=remaining,
                    percent=100*done/total if total else 100, eta_seconds=eta, renders=rows)

    def publish(self, force=False):
        if os.getpid() != self.owner_pid:
            return
        with self.lock:
            now = time.monotonic()
            if not force and now-self.last_write < self.interval:
                return
            with FileReplacer(str(self.path)) as temporary:
                Path(temporary).write_text(json.dumps(self.snapshot(), ensure_ascii=False), encoding='utf-8')
            self.last_write = now

    def _heartbeat(self):
        while not self._stop.wait(self.interval):
            try:
                self.publish(force=True)
            except OSError:
                logging.warning('Could not publish render progress', exc_info=True)

    def close(self):
        self._stop.set()
        if self.thread:
            self.thread.join(timeout=5)


def register(progress):
    _active.set(progress)
