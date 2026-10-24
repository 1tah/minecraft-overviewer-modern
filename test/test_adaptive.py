"""Exercise the actual pipe pool, dependency acknowledgements and pressure control."""
import os
from pathlib import Path
import time

import pytest

from overviewer_core.adaptive import AdaptiveDispatcher, ResourcePolicy, MIB
from overviewer_core.resource_session import ResourceSession, read_state, finalize_session, atomic_json


def test_policy_reserves_headroom_and_uses_hysteresis():
    p = ResourcePolicy(1024*MIB, 8)
    assert p.decide(300*MIB, 1, False, False, 100*MIB, 0) == 'grow'
    assert p.decide(300*MIB, 2, False, False, 100*MIB, 1) is None
    assert p.decide(850*MIB, 2, False, False, 100*MIB, 2) == 'shrink'
    assert p.decide(850*MIB, 1, False, False, 100*MIB, 30) is None
    assert p.decide(650*MIB, 2, False, False, 300*MIB, 30) is None
    assert p.decide(200*MIB, 2, True, False, 100*MIB, 30) is None
    assert p.decide(200*MIB, 2, False, True, 100*MIB, 30) is None


def test_session_retries_are_bounded_and_report_aggregates(tmp_path):
    session = ResourceSession(16, list(range(16)), 8*1024**3)
    try:
        session.attempts = [dict(current_workers=8, oom=True, min_workers=1, max_workers_observed=8,
            render_seconds=10, worker_seconds=30, completed_this_attempt=100, peak_memory_bytes=800,
            exit_code=137), dict(current_workers=2, oom=False, min_workers=1, max_workers_observed=2,
            render_seconds=20, worker_seconds=40, completed_this_attempt=200, peak_memory_bytes=500,
            exit_code=0, recommended_workers=2, outputdir=str(tmp_path))]
        assert session.retry_ceiling(8) == 1
        finalize_session(session.export())
        report = read_state(tmp_path/'render-resources.json')
        assert report['oom_restarts'] == 1
        assert report['completed_this_session'] == 300
        assert report['average_tiles_per_second'] == 10
        assert report['observed_max_workers'] == 8
        assert report['peak_memory_bytes'] == 800
    finally:
        session.close()


class Memory:
    limit = 1024*MIB

    def __init__(self, pressure=True):
        self.started = time.monotonic()
        self.pressure = pressure
        self.pressure_started = self.pressure_done = False
        self.pool = None

    def usage(self):
        if self.pressure and self.pool is not None and not self.pressure_done:
            ready = sum(s['ready'] for s in self.pool.slots)
            if ready >= 3 and self.pool.completed >= 30:
                self.pressure_started = True
            if self.pressure_started:
                if len(self.pool.slots) <= 1:
                    self.pressure_done = True
                else:
                    return 900*MIB
        return 200*MIB


class Tiles:
    options = {'resume_key': 'test'}

    def __init__(self, directory, count=200, fail=False):
        self.directory, self.count, self.fail = str(directory), count, fail
        self.acknowledged = []

    def get_num_phases(self):
        return 1

    def get_phase_length(self, phase):
        return self.count+1

    def iterate_work_items(self, phase):
        for i in range(self.count):
            yield i, []
        yield 'parent', list(range(self.count))

    def do_work(self, tile):
        if self.fail and tile == 2:
            raise ValueError('intentional worker failure')
        if tile == 'parent':
            assert len(list(Path(self.directory).glob('*.tile'))) == self.count
        time.sleep(0.03)
        target = Path(self.directory)/(str(tile)+'.tile')
        assert not target.exists(), 'duplicate work'
        target.write_text('done')

    def work_completed(self, tile):
        self.acknowledged.append(tile)


class Observer:
    def start(self, total): pass
    def add(self, count): pass
    def finish(self): pass


@pytest.mark.skipif(not hasattr(os, 'sched_getaffinity'), reason='Linux adaptive pool')
def test_pool_grows_drains_and_regrows_without_losing_dependencies(tmp_path):
    tiles = Tiles(tmp_path)
    pool = AdaptiveDispatcher(3, tmp_path, memory=Memory(), interval=0.02, cooldown=0.1)
    pool.memory.pool = pool
    try:
        pool.render_all([tiles], Observer())
        pool.close()
    finally:
        pool.abort()
    actions = [event['action'] for event in pool.events]
    assert actions.count('start') >= 4, actions
    assert 'drain' in actions and 'retired' in actions, actions
    assert len(tiles.acknowledged) == len(set(tiles.acknowledged)) == 201
    assert tiles.acknowledged[-1] == 'parent'
    assert pool.max_observed == 3
    assert not pool.slots


@pytest.mark.skipif(not hasattr(os, 'sched_getaffinity'), reason='Linux adaptive pool')
def test_worker_exception_preserves_unacknowledged_work(tmp_path):
    tiles = Tiles(tmp_path, count=10, fail=True)
    pool = AdaptiveDispatcher(1, tmp_path, memory=Memory(False))
    try:
        with pytest.raises(RuntimeError, match='intentional worker failure'):
            pool.render_all([tiles], Observer())
    finally:
        pool.abort()
    assert 2 not in tiles.acknowledged
    assert pool.failed_workers == 1


@pytest.mark.skipif(not hasattr(os, 'sched_getaffinity'), reason='Linux adaptive pool')
def test_empty_plan_starts_no_worker(tmp_path):
    tiles = Tiles(tmp_path)
    tiles.get_phase_length = lambda phase: 0
    pool = AdaptiveDispatcher(8, tmp_path, memory=Memory(False))
    pool.setup_tilesets([tiles])
    assert not pool.slots
    pool.close()


@pytest.mark.skipif(not hasattr(os, 'sched_getaffinity'), reason='Linux tuning profile')
def test_profile_remembers_safe_ceiling_and_resets_for_changed_budget(tmp_path):
    tiles = Tiles(tmp_path)
    tiles.get_phase_length = lambda phase: 0
    first = AdaptiveDispatcher(8, tmp_path, memory=Memory(False))
    first.setup_tilesets([tiles])
    atomic_json(first.profile, dict(key=first.key, recommended_workers=2, safe_ceiling=3))
    first.close()
    second = AdaptiveDispatcher(8, tmp_path, memory=Memory(False))
    second.setup_tilesets([tiles])
    assert second.maximum == 3 and second.start_target == 2
    second.close()
    memory = Memory(False)
    memory.limit *= 2
    third = AdaptiveDispatcher(8, tmp_path, memory=memory)
    third.setup_tilesets([tiles])
    assert third.maximum == 8 and third.start_target == 1
    third.close()
    fourth = AdaptiveDispatcher(12, tmp_path, memory=Memory(False))
    fourth.setup_tilesets([tiles])
    assert fourth.maximum == 12 and fourth.start_target == 1
    fourth.close()
