"""Bounded adaptive worker pool: one in-flight tile per worker, no manager copy."""
import hashlib
import logging
import multiprocessing
from multiprocessing.connection import wait
import os
from pathlib import Path
import time
import traceback

from .dispatcher import Dispatcher, follow_parent
from .resource_session import atomic_json, read_state
from .signals import Signal
from overviewer_cache_policy import pressure_sample
from overviewer_worker_start import (validate_start_workers, spawn_snapshot_worker,
                                    complete_initial_pool, close_worker_snapshot)

MIB = 1024**2


class CgroupMemory:
    def __init__(self):
        provided = os.environ.get('OVERVIEWER_CGROUP_PATH')
        if provided:
            self.path = Path(provided)
        else:
            lines = Path('/proc/self/cgroup').read_text().splitlines()
            unified = next((line[3:] for line in lines if line.startswith('0::')), None)
            if unified is None:
                raise RuntimeError('Auto mode requires the verified launcher memory cgroup.')
            self.path = Path('/sys/fs/cgroup')/unified.lstrip('/')
        self.v2 = (self.path/'memory.max').exists()
        value = (self.path/('memory.max' if self.v2 else 'memory.limit_in_bytes')).read_text().strip()
        if value == 'max' or int(value) >= 2**60:
            raise RuntimeError('Auto mode requires a finite kernel memory limit.')
        self.limit = int(value)

    def usage(self):
        return int((self.path/('memory.current' if self.v2 else 'memory.usage_in_bytes')).read_text())

    def peak_usage(self):
        path = self.path/('memory.peak' if self.v2 else 'memory.max_usage_in_bytes')
        return int(path.read_text()) if path.exists() else self.usage()

    def pressure_sample(self, usage=None):
        return pressure_sample(self.path, self.v2, self.usage() if usage is None else usage)


def worker_rss(pid):
    try:
        for line in Path('/proc/%d/status' % pid).read_text().splitlines():
            if line.startswith('VmRSS:'):
                return int(line.split()[1])*1024
    except OSError:
        pass
    return 0


class ResourcePolicy:
    def __init__(self, limit, maximum, cooldown=10):
        self.limit, self.maximum, self.cooldown = limit, maximum, cooldown
        self.last_change = float('-inf')

    def decide(self, usage, live, starting, retiring, estimate, now):
        if retiring or starting:
            return None
        if usage >= self.limit*0.82 and live > 1:
            self.last_change = now
            return 'shrink'
        if now-self.last_change < self.cooldown:
            return None
        reserve = max(32*MIB, self.limit*0.12)
        if live < self.maximum and usage < self.limit*0.72 and usage+estimate*1.6+reserve < self.limit*0.94:
            self.last_change = now
            return 'grow'
        return None


def adaptive_worker(connection, tilesets, parent):
    follow_parent(parent)
    emitted = []
    for name, sig in Signal.signals.items():
        sig.set_interceptor(lambda *a, _name=name, **kw: emitted.append((_name, a, kw)))
    try:
        connection.send(('ready',))
        while True:
            item = connection.recv()
            if item is None:
                return
            index, tile = item
            tilesets[index].do_work(tile)
            connection.send(('done', index, tile, emitted))
            emitted = []
    except (EOFError, KeyboardInterrupt):
        return
    except BaseException:
        try:
            connection.send(('error', traceback.format_exc()))
        except (OSError, EOFError):
            pass
        raise
    finally:
        connection.close()


class AdaptiveDispatcher(Dispatcher):
    supports_start_workers = True

    def __init__(self, maximum, outputdir, memory=None, context=None, interval=1.0, cooldown=10, start_workers=None):
        super().__init__()
        self.memory = memory or CgroupMemory()
        self.requested_maximum = maximum
        self.initial_workers_requested = validate_start_workers(start_workers, maximum)
        self.initial_workers_started = 0
        self.maximum = max(1, min(maximum, int(os.environ.get('OVERVIEWER_WORKER_CEILING', maximum))))
        self.outputdir = str(outputdir)
        self.context = context or multiprocessing.get_context('forkserver')
        self.policy = ResourcePolicy(self.memory.limit, self.maximum, cooldown)
        self.cooldown = cooldown
        self.start_target = 1
        self.interval = interval
        self.slots = []
        self.finished = []
        self.completed = 0
        self.started = self.last_tick = time.monotonic()
        self.last_sample = float('-inf')
        self.worker_seconds = 0.0
        self.busy_worker_seconds = 0.0
        self.peak = self.min_workers = self.max_observed = 0
        self.events = []
        self.closed = False
        self.state = os.environ.get('OVERVIEWER_RESOURCE_STATE')
        self.profile = Path(outputdir)/'.overviewer-autotune.json'
        self.recommended = 1
        self.best_rate = 0
        self.failed_workers = 0
        self.memory_sample = {}
        self.first_ready = None
        self.initialization_seconds = 1.0
        self.window = (self.started, 0, 0)

    def setup_tilesets(self, tilesets):
        self.tilesets = tilesets
        self.total = sum((ts.get_phase_length(p) or 0) for ts in tilesets for p in range(ts.get_num_phases()))
        signature = repr(([ts.options.get('resume_key') for ts in tilesets], self.memory.limit,
                          os.cpu_count(), os.uname().machine, self.requested_maximum,
                          sorted(os.sched_getaffinity(0)), 'forkserver-v1'))
        self.key = hashlib.sha256(signature.encode()).hexdigest()
        profile = read_state(self.profile)
        if profile.get('key') == self.key:
            safe = profile.get('safe_ceiling', self.maximum)
            if isinstance(safe, int) and safe > 0:
                self.maximum = min(self.maximum, safe)
                self.policy.maximum = self.maximum
            target = profile.get('recommended_workers', 1)
            self.recommended = max(1, min(self.maximum, target)) if isinstance(target, int) else 1
            self.start_target = self.recommended
        if any((ts.get_phase_length(p) or 0) for ts in tilesets for p in range(ts.get_num_phases())):
            self._spawn()
        complete_initial_pool(self, self.initial_workers_requested)

    def _spawn(self):
        spawn_snapshot_worker(self)

    def _event(self, action):
        self.events.append(dict(seconds=time.monotonic()-self.started, action=action, workers=len(self.slots)))
        self.events = self.events[-256:]
        used = self.memory.usage()
        sample = self.memory.pressure_sample(used) if hasattr(self.memory, 'pressure_sample') else {}
        logging.info('Auto resources: %s; workers=%s/%s, RAM=%.0f/%.0f MiB; working=%.0f, clean inactive cache=%.0f MiB',
                     action, len(self.slots), self.maximum, used/MIB, self.memory.limit/MIB,
                     sample.get('working_bytes', used)/MIB, sample.get('reclaimable_bytes', 0)/MIB)
        self.checkpoint()

    def _retire(self):
        choices = [slot for slot in self.slots if not slot['retiring']]
        slot = max(choices, key=lambda s: (s['job'] is None, worker_rss(s['process'].pid)))
        slot['retiring'] = True
        if slot['ready'] and slot['job'] is None:
            slot['pipe'].send(None)
            slot['closing'] = True
        self._event('drain')

    def _account(self):
        now = time.monotonic()
        ready = sum(slot['ready'] and not slot['closing'] for slot in self.slots)
        self.worker_seconds += (now-self.last_tick)*ready
        self.busy_worker_seconds += (now-self.last_tick)*sum(s['job'] is not None for s in self.slots)
        self.last_tick = now
        return now, ready

    def _sample(self):
        now, ready = self._account()
        if ready:
            self.min_workers = min(self.min_workers or ready, ready)
            self.max_observed = max(self.max_observed, ready)
        if now-self.last_sample < self.interval:
            return
        self.last_sample = now
        usage = self.memory.usage()
        self.memory_sample = self.memory.pressure_sample(usage) if hasattr(self.memory, 'pressure_sample') else dict(
            usage_bytes=usage, working_bytes=usage, reclaimable_bytes=0)
        working = self.memory_sample['working_bytes']
        self.peak = max(self.peak, usage)
        estimate = max([64*MIB]+[worker_rss(slot['process'].pid) for slot in self.slots])
        starting = any(not s['ready'] for s in self.slots)
        retiring = any(s['retiring'] for s in self.slots)
        self.policy.cooldown = min(2, self.cooldown) if len(self.slots) < self.start_target else self.cooldown
        action = None if self.closed or self.completed >= self.total else self.policy.decide(working, len(self.slots), starting, retiring, estimate, now)
        if action == 'shrink':
            self._retire()
        elif action == 'grow':
            active = now-self.first_ready if self.first_ready is not None else 0
            rate = self.completed/active if active > 0 else 0
            remaining_seconds = (self.total-self.completed)/rate if rate else float('inf')
            if remaining_seconds > self.initialization_seconds*1.5:
                self._spawn()
        if not starting and not retiring and ready == self.window[2]:
            elapsed = now-self.window[0]
            count = self.completed-self.window[1]
            if elapsed >= 15 and count >= 20:
                rate = count/elapsed
                if rate > self.best_rate and working < self.memory.limit*0.82:
                    self.best_rate, self.recommended = rate, ready
                self.window = (now, self.completed, ready)
        else:
            self.window = (now, self.completed, ready)
        self.checkpoint()

    def _service(self):
        if self.slots:
            wait([s['pipe'] for s in self.slots], timeout=0.05)
        self._account()
        for slot in list(self.slots):
            try:
                while slot['pipe'].poll():
                    message = slot['pipe'].recv()
                    if message[0] == 'ready':
                        slot['ready'] = True
                        if self.first_ready is None:
                            self.first_ready = time.monotonic()
                            self.initialization_seconds = max(0.1, self.first_ready-self.started)
                        if slot['retiring']:
                            slot['pipe'].send(None)
                            slot['closing'] = True
                    elif message[0] == 'error':
                        raise RuntimeError('Adaptive render worker failed:\n'+message[1])
                    elif message[0] == 'done':
                        _, index, tile, emitted = message
                        self.finished.append((self.tilesets[index], tile))
                        self.completed += 1
                        slot['job'] = None
                        for name, args, kwargs in emitted:
                            Signal.signals[name].emit_intercepted(*args, **kwargs)
                        if slot['retiring']:
                            slot['pipe'].send(None)
                            slot['closing'] = True
            except EOFError:
                if not slot['closing']:
                    raise RuntimeError('Adaptive worker disconnected; saved render plan is retained.')
            if slot['process'].exitcode is not None:
                if not slot['closing'] or slot['job'] is not None:
                    raise RuntimeError('Adaptive worker exited unexpectedly; render plan is retained.')
                slot['process'].join()
                slot['pipe'].close()
                self.slots.remove(slot)
                self._event('retired')
        self._sample()

    def dispatch(self, tileset, workitem):
        self._service()
        if tileset is not None:
            while True:
                idle = next((s for s in self.slots if s['ready'] and s['job'] is None and not s['retiring']), None)
                if idle is not None:
                    self._account()
                    index = self.tilesets.index(tileset)
                    idle['pipe'].send((index, workitem))
                    idle['job'] = (index, workitem)
                    break
                self._service()
        finished, self.finished = self.finished, []
        return finished

    def checkpoint(self, status='rendering'):
        elapsed = time.monotonic()-self.started
        report = dict(status=status, phase='rendering', outputdir=self.outputdir,
            current_workers=len(self.slots) or self.failed_workers, max_workers_allowed=self.maximum,
            min_workers=self.min_workers, max_workers_observed=self.max_observed,
            worker_seconds=self.worker_seconds, render_seconds=elapsed,
            busy_worker_seconds=self.busy_worker_seconds, profile_start_target=self.start_target,
            initial_workers_requested=self.initial_workers_requested, initial_workers_started=self.initial_workers_started,
            completed_this_attempt=self.completed, peak_memory_bytes=self.peak,
            recommended_workers=max(1, self.recommended if self.best_rate or not self.completed else self.max_observed),
            cpu_ids=sorted(os.sched_getaffinity(0)), events=self.events, memory_accounting=self.memory_sample)
        if self.state:
            atomic_json(self.state, report)
        return report

    def resource_snapshot(self):
        slots = list(self.slots)
        return dict(workers_current=sum(s['ready'] and not s['closing'] for s in slots),
                    workers_busy=sum(s['job'] is not None for s in slots),
                    workers_starting=sum(not s['ready'] for s in slots), worker_limit=self.maximum)

    def close(self):
        self.closed = True
        self._sample()
        for slot in self.slots:
            slot['pipe'].send(None)
            slot['closing'] = True
        for slot in self.slots:
            slot['process'].join(timeout=10)
            if slot['process'].is_alive():
                slot['process'].terminate()
                slot['process'].join(timeout=5)
            slot['pipe'].close()
        self.slots = []
        self.closed = True
        close_worker_snapshot(self)

    def abort(self):
        self.failed_workers = len(self.slots)
        self._sample_before_abort()
        for slot in self.slots:
            if slot['process'].pid is not None:
                if slot['process'].is_alive():
                    slot['process'].terminate()
                slot['process'].join(timeout=5)
            slot['pipe'].close()
        self.slots = []
        self.closed = True
        close_worker_snapshot(self)

    def _sample_before_abort(self):
        self.closed = True
        self.last_sample = float('-inf')
        self._sample()

    def finish_report(self, status):
        report = self.checkpoint(status)
        atomic_json(Path(self.outputdir)/'render-resources.json', report)
        if status == 'complete' and self.completed:
            atomic_json(self.profile, dict(key=self.key, recommended_workers=report['recommended_workers'],
                                          safe_ceiling=self.maximum, peak_memory_bytes=self.peak))
        if not self.state:
            from .resource_session import ResourceSession, finalize_session
            session = ResourceSession(self.maximum, report['cpu_ids'], self.memory.limit)
            try:
                session.attempts = [dict(report, exit_code=0 if status == 'complete' else 1, oom=False)]
                finalize_session(session.export())
            finally:
                session.close()
        return report
