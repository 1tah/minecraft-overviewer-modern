"""Explicit initial pools, parallel loading and recovery ceilings."""
import os
from pathlib import Path
import time
import pytest
from overviewer_worker_start import validate_start_workers
from overviewer_core.resource_session import atomic_json
from overviewer_core.adaptive import AdaptiveDispatcher
from test.test_adaptive import Tiles, Memory, Observer


@pytest.mark.parametrize('value', [0, -1, 7])
def test_invalid_start(value):
    with pytest.raises(ValueError, match='--start-workers'):
        validate_start_workers(value, 6)


class SlowLoadTiles(Tiles):
    def __getstate__(self):
        # More than a pipe buffer after an object with slow reconstruction.
        return self.__dict__, b'x'*1024**2

    def __setstate__(self, state):
        self.__dict__.update(state[0])
        (Path(self.directory)/('load-%d' % os.getpid())).write_text(str(time.monotonic()))
        time.sleep(0.7)
        (Path(self.directory)/('ready-%d' % os.getpid())).write_text(str(time.monotonic()))


@pytest.mark.skipif(not hasattr(os, 'sched_getaffinity'), reason='Linux adaptive pool')
def test_initial_workers_load_in_parallel_then_complete_dependencies(tmp_path):
    pool = AdaptiveDispatcher(6, tmp_path, memory=Memory(False), start_workers=6)
    tiles = SlowLoadTiles(tmp_path, count=60)
    try:
        pool.setup_tilesets([tiles])
        assert len(pool.slots) == pool.initial_workers_started == 6
        snapshot = Path(pool._worker_snapshot_path)
        assert snapshot.exists() and snapshot.parent.stat().st_mode & 0o077 == 0
        deadline = time.monotonic()+10
        while not all(slot['ready'] for slot in pool.slots):
            pool._service()
            assert time.monotonic() < deadline
        loads = {path.name[5:]:float(path.read_text()) for path in tmp_path.glob('load-*')}
        ends = {path.name[6:]:float(path.read_text()) for path in tmp_path.glob('ready-*')}
        assert len(loads) == len(ends) == 6
        assert any(loads[a] < loads[b] < ends[a] for a in loads for b in loads if a != b), loads
        # setup already ran; drive the normal dependency scheduler without restarting it.
        pool.setup_tilesets = lambda ignored: None
        pool.render_all([tiles], Observer())
        pool.close()
        assert len(tiles.acknowledged) == 61
        assert tiles.acknowledged[-1] == 'parent'
        assert not snapshot.exists()
    finally:
        pool.abort()


@pytest.mark.skipif(not hasattr(os, 'sched_getaffinity'), reason='Linux adaptive pool')
def test_oom_ceiling_clamps_requested_initial_pool(tmp_path, monkeypatch):
    monkeypatch.setenv('OVERVIEWER_WORKER_CEILING', '2')
    pool = AdaptiveDispatcher(10, tmp_path, memory=Memory(False), start_workers=6)
    try:
        pool.setup_tilesets([Tiles(tmp_path)])
        assert pool.maximum == 2 and len(pool.slots) == 2
        assert pool.initial_workers_requested == 6 and pool.initial_workers_started == 2
        snapshot = Path(pool._worker_snapshot_path)
    finally:
        pool.abort()
    assert not snapshot.exists()


@pytest.mark.skipif(not hasattr(os, 'sched_getaffinity'), reason='Linux adaptive pool')
def test_empty_plan_with_start_count_creates_no_snapshot(tmp_path):
    tiles = Tiles(tmp_path)
    tiles.get_phase_length = lambda phase: 0
    pool = AdaptiveDispatcher(10, tmp_path, memory=Memory(False), start_workers=6)
    pool.setup_tilesets([tiles])
    assert not pool.slots and not hasattr(pool, '_worker_snapshot')
    pool.close()


def test_native_install_keeps_flag_for_native_parser(monkeypatch):
    import sys
    from overviewer_worker_start import install_legacy
    argv = ['overviewer.py', '--start-workers=6']
    monkeypatch.setattr(sys, 'argv', argv.copy())
    install_legacy()
    assert sys.argv == argv


@pytest.mark.skipif(not hasattr(os, 'sched_getaffinity'), reason='Linux adaptive pool')
def test_initial_pool_respects_learned_safe_ceiling(tmp_path):
    empty = Tiles(tmp_path)
    empty.get_phase_length = lambda phase: 0
    first = AdaptiveDispatcher(10, tmp_path, memory=Memory(False))
    first.setup_tilesets([empty])
    atomic_json(first.profile, dict(key=first.key, recommended_workers=1, safe_ceiling=2))
    first.close()
    pool = AdaptiveDispatcher(10, tmp_path, memory=Memory(False), start_workers=6)
    try:
        pool.setup_tilesets([Tiles(tmp_path)])
        assert pool.maximum == pool.initial_workers_started == 2
    finally:
        pool.abort()


@pytest.mark.skipif(not hasattr(os, 'sched_getaffinity'), reason='Linux legacy pool')
def test_legacy_flag_consumption_and_initial_pool(tmp_path, monkeypatch):
    import sys
    from overviewer_core import adaptive
    from overviewer_worker_start import install_legacy
    class OldPool(AdaptiveDispatcher):
        supports_start_workers = False
    monkeypatch.setattr(adaptive, 'AdaptiveDispatcher', OldPool)
    monkeypatch.setattr(sys, 'argv', ['overviewer.py', '--start-workers=2', '--cpu-limit=2'])
    monkeypatch.setenv('OVERVIEWER_INITIAL_WORKERS', '')
    install_legacy()
    assert '--start-workers=2' not in sys.argv
    assert '--auto-resources' in sys.argv and '--simple' in sys.argv
    pool = adaptive.AdaptiveDispatcher(2, tmp_path, memory=Memory(False))
    try:
        pool.setup_tilesets([Tiles(tmp_path)])
        assert pool.initial_workers_requested == pool.initial_workers_started == 2
    finally:
        pool.abort()


@pytest.mark.parametrize('flags', [
    ['--start-workers=0'],
    ['--start-workers=2', '--cpu-limit=1'],
    ['--start-workers=2', '-p=1'],
    ['--start-workers=1', '--fixed-resources'],
    ['--start-workers=1', '--genpoi'],
])
def test_cli_rejects_invalid_initial_pool_before_loading_world(flags):
    import subprocess, sys
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, str(root/'overviewer.py'), *flags],
                            cwd=root, capture_output=True, text=True, timeout=25)
    assert result.returncode == 2, result.stdout+result.stderr
    assert '--start-workers' in result.stderr
