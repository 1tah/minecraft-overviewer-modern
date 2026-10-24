"""Stdlib-only resource reports, also copied beside the Ubuntu 20 launcher."""
import json
import os
from pathlib import Path
import tempfile
import time


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.'+path.name+'-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_state(path):
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
        with os.fdopen(fd, 'r', encoding='utf-8') as stream:
            data = stream.read(262145)
        if len(data) > 262144:
            return {}
        result = json.loads(data)
        return result if isinstance(result, dict) else {}
    except (OSError, ValueError):
        return {}


def pin_cpus(count):
    available = sorted(os.sched_getaffinity(0))
    if count is None:
        return available
    if count < 1:
        raise ValueError('--cpu-limit must be a positive number of logical CPUs')
    # First use distinct physical cores, then SMT siblings.
    first, siblings, seen = [], [], set()
    for cpu in available:
        base = Path('/sys/devices/system/cpu/cpu%d/topology' % cpu)
        try:
            key = ((base/'physical_package_id').read_text().strip(), (base/'core_id').read_text().strip())
        except OSError:
            key = ('unknown', cpu)
        (siblings if key in seen else first).append(cpu)
        seen.add(key)
    chosen = set((first+siblings)[:min(count, len(available))])
    for thread in Path('/proc/self/task').iterdir():
        try:
            os.sched_setaffinity(int(thread.name), chosen)
        except ProcessLookupError:
            pass
    return sorted(chosen)


class ResourceSession:
    def __init__(self, maximum, cpu_ids, limit, uid=None, gid=None):
        self.maximum, self.cpu_ids, self.limit = maximum, cpu_ids, limit
        self.started = time.monotonic()
        self.temporary = tempfile.TemporaryDirectory(prefix='overviewer-resources-')
        self.directory = Path(self.temporary.name)
        self.directory.chmod(0o711)
        child = self.directory/'child'
        child.mkdir(mode=0o700)
        if uid is not None and os.geteuid() == 0:
            os.chown(child, uid, gid)
        self.state = child/'state.json'
        self.attempts = []

    def environment(self, ceiling):
        atomic_json(self.state, {'phase': 'preparing', 'current_workers': 0})
        return {'OVERVIEWER_RESOURCE_STATE': str(self.state),
                'OVERVIEWER_WORKER_CEILING': str(ceiling),
                'OVERVIEWER_RESOURCE_SESSION': '1'}

    def record(self, result, oom, details):
        data = read_state(self.state)
        data.update(exit_code=result, oom=oom,
                    peak_memory_bytes=max(int(data.get('peak_memory_bytes', 0)), details.get('peak_memory_bytes', 0)))
        self.attempts.append(data)
        return data

    def retry_ceiling(self, ceiling):
        current = self.attempts[-1].get('current_workers', 0)
        if not isinstance(current, int) or current <= 1:
            return None
        return max(1, min(ceiling-1, current//2))

    def export(self):
        value = dict(max_allowed_workers=self.maximum, cpu_ids=self.cpu_ids,
                     memory_limit_bytes=self.limit, session_seconds=time.monotonic()-self.started,
                     attempts=self.attempts)
        target = self.directory/'session.json'
        atomic_json(target, value)
        return target

    def close(self):
        self.temporary.cleanup()


def finalize_session(path):
    session = json.loads(Path(path).read_text(encoding='utf-8'))
    attempts = session['attempts']
    if not attempts:
        return
    last = attempts[-1]
    elapsed = sum(a.get('render_seconds', 0) for a in attempts)
    worker_seconds = sum(a.get('worker_seconds', 0) for a in attempts)
    done = sum(a.get('completed_this_attempt', 0) for a in attempts)
    session.update(status='complete' if last.get('exit_code') == 0 else 'interrupted' if last.get('status') == 'interrupted' else 'error',
                   observed_min_workers=min((a['min_workers'] for a in attempts if a.get('min_workers')), default=0),
                   observed_max_workers=max((a.get('max_workers_observed', 0) for a in attempts), default=0),
                   average_workers=worker_seconds/elapsed if elapsed else 0,
                   average_busy_workers=sum(a.get('busy_worker_seconds', 0) for a in attempts)/elapsed if elapsed else 0,
                   peak_memory_bytes=max((a.get('peak_memory_bytes', 0) for a in attempts), default=0),
                   average_tiles_per_second=done/elapsed if elapsed else 0,
                   completed_this_session=done, oom_restarts=sum(a.get('oom', False) for a in attempts[:-1]),
                   recommended_workers=last.get('recommended_workers', 1))
    output = last.get('outputdir')
    directory = Path(output) if isinstance(output, str) and output else Path.home()/'.local/state/overviewer'
    target = directory/'render-resources.json'
    atomic_json(target, session)
    maximum = session['observed_max_workers']
    print('\nАвто-ресурсы: максимум CPU {}, работников {}..{}, среднее {:.2f}; пик RAM {:.2f} GiB; {:.2f} тайлов/с.'.format(
        len(session['cpu_ids']), session['observed_min_workers'], maximum, session['average_workers'],
        session['peak_memory_bytes']/1024**3, session['average_tiles_per_second']), flush=True)
    print('Рекомендация следующего запуска: {} работников. Отчёт: {}'.format(session['recommended_workers'], target), flush=True)
    if last.get('oom') and last.get('current_workers', 0) <= 1:
        print('Не хватает памяти для подготовки/одного работника. Увеличьте --memory-limit или уменьшите набор слоёв.', flush=True)


if __name__ == '__main__':
    import sys
    finalize_session(sys.argv[1])
