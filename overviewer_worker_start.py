"""Private worker snapshots and explicit initial pools; also usable as a hotfix."""
import logging
import os
from pathlib import Path
import pickle
import tempfile
import traceback


def validate_start_workers(value, maximum):
    if value is not None and (not isinstance(value, int) or value < 1 or value > maximum):
        raise ValueError('--start-workers must be between 1 and %d (CPU/-p maximum)' % maximum)
    return value


def snapshot_worker(connection, snapshot, parent):
    from overviewer_core.dispatcher import follow_parent
    from overviewer_core.signals import Signal
    follow_parent(parent)
    emitted = []
    try:
        with open(snapshot, 'rb') as stream:
            tilesets = pickle.load(stream)
        for name, sig in Signal.signals.items():
            sig.set_interceptor(lambda *a, _name=name, **kw: emitted.append((_name, a, kw)))
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


def spawn_snapshot_worker(pool):
    # Passing a large TileSet through Process.start() can block while a child
    # regenerates textures during unpickling. A tiny path argument avoids that:
    # all initial children can load the same trusted private snapshot in parallel.
    if getattr(pool, '_worker_snapshot', None) is None:
        state = getattr(pool, 'state', None)
        pool._worker_snapshot = tempfile.TemporaryDirectory(prefix='overviewer-worker-state-',
            dir=str(Path(state).parent) if state else None)
        snapshot = Path(pool._worker_snapshot.name)/'tilesets.pickle'
        with snapshot.open('wb') as stream:
            pickle.dump(pool.tilesets, stream, protocol=4)
        pool._worker_snapshot_path = str(snapshot)
    parent, child = pool.context.Pipe()
    process = pool.context.Process(target=snapshot_worker,
        args=(child, pool._worker_snapshot_path, os.getpid()))
    pool.slots.append(dict(process=process, pipe=parent, ready=False, job=None, retiring=False, closing=False))
    pool._event('start')
    try:
        process.start()
    finally:
        child.close()


def complete_initial_pool(pool, requested):
    pool.initial_workers_requested = requested
    pool.initial_workers_started = len(pool.slots)
    if requested is not None and pool.slots:
        count = min(requested, pool.maximum)
        pool.start_target = count
        logging.info('Initial pool: requested=%d, starting=%d, maximum=%d', requested, count, pool.maximum)
        while len(pool.slots) < count:
            pool._spawn()
        pool.initial_workers_started = len(pool.slots)
        pool.checkpoint()


def close_worker_snapshot(pool):
    snapshot = getattr(pool, '_worker_snapshot', None)
    if snapshot is not None:
        snapshot.cleanup()
        pool._worker_snapshot = None


def install_legacy():
    """Consume the new flag and patch old pools without touching hashed core."""
    import argparse
    import sys
    from overviewer_core import adaptive
    if getattr(adaptive.AdaptiveDispatcher, 'supports_start_workers', False):
        return
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--start-workers', type=int)
    parser.add_argument('--cpu-limit', type=int)
    parser.add_argument('-p', '--processes', dest='workers', type=int)
    opts, _ = parser.parse_known_args()
    raw = opts.start_workers
    if raw is None and os.environ.get('OVERVIEWER_INITIAL_WORKERS'):
        try:
            raw = int(os.environ['OVERVIEWER_INITIAL_WORKERS'])
        except ValueError:
            raise SystemExit('OVERVIEWER_INITIAL_WORKERS must be an integer')
    if raw is not None:
        if any(flag in sys.argv for flag in ('--fixed-resources', '--genpoi')):
            raise SystemExit('--start-workers requires automatic rendering, without --fixed-resources/--genpoi')
        maximum = len(os.sched_getaffinity(0))
        for cap in (opts.cpu_limit, opts.workers):
            if cap is not None and cap > 0:
                maximum = min(maximum, cap)
        try:
            validate_start_workers(raw, maximum)
        except ValueError as error:
            raise SystemExit(str(error))
        os.environ['OVERVIEWER_INITIAL_WORKERS'] = str(raw)
        forwarded, skip = [], False
        for item in sys.argv[1:]:
            if skip: skip = False
            elif item == '--start-workers': skip = True
            elif not item.startswith('--start-workers='): forwarded.append(item)
        sys.argv[:] = [sys.argv[0], *forwarded]
        if '--auto-resources' not in sys.argv:
            sys.argv.append('--auto-resources')
        if '--simple' not in sys.argv:
            sys.argv.append('--simple')
    base = adaptive.AdaptiveDispatcher
    if getattr(base, 'supports_start_workers', False):
        return

    class LegacyInitialDispatcher(base):
        supports_start_workers = True

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.initial_workers_requested = validate_start_workers(raw, self.requested_maximum)
            self.initial_workers_started = 0

        def _spawn(self):
            spawn_snapshot_worker(self)

        def setup_tilesets(self, tilesets):
            super().setup_tilesets(tilesets)
            complete_initial_pool(self, self.initial_workers_requested)

        def checkpoint(self, status='rendering'):
            from overviewer_core.resource_session import atomic_json
            report = super().checkpoint(status)
            report.update(initial_workers_requested=self.initial_workers_requested,
                          initial_workers_started=self.initial_workers_started)
            if self.state:
                atomic_json(self.state, report)
            return report

        def close(self):
            try: super().close()
            finally: close_worker_snapshot(self)

        def abort(self):
            try: super().abort()
            finally: close_worker_snapshot(self)

    adaptive.AdaptiveDispatcher = LegacyInitialDispatcher
    print('Initial worker pool enabled; saved render plan identity unchanged.', flush=True)
