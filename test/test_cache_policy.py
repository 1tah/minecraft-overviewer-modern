from pathlib import Path

import pytest

from overviewer_cache_policy import pressure_sample, install_legacy
from overviewer_core.adaptive import CgroupMemory, ResourcePolicy, MIB


def sample(tmp_path, values, usage, unified=False):
    (tmp_path/'memory.stat').write_text('\n'.join('%s %s' % item for item in values.items()))
    return pressure_sample(tmp_path, unified, usage)


def test_server_v1_statistics_allow_growth_without_discounting_active_cache(tmp_path):
    stats = dict(cache=7653220352, rss=2505613312, shmem=0, inactive_file=6151872512,
                 total_cache=7653220352, total_rss=2505613312, total_inactive_file=6151872512)
    used = stats['rss']+stats['cache']
    result = sample(tmp_path, stats, used)
    assert result['reclaimable_bytes'] == 6151872512
    assert result['working_bytes'] == 4006961152
    policy = ResourcePolicy(10*1024**3, 10)
    assert policy.decide(used, 1, False, False, 1507392*1024, 0) is None
    assert policy.decide(result['working_bytes'], 1, False, False, 1507392*1024, 0) == 'grow'


@pytest.mark.parametrize('unified', [False, True])
def test_dirty_writeback_and_shmem_are_not_treated_as_free(tmp_path, unified):
    names = ('file', 'file_dirty', 'file_writeback') if unified else ('cache', 'dirty', 'writeback')
    values = dict(zip(names, (900*MIB, 200*MIB, 100*MIB)))
    values.update(shmem=300*MIB, inactive_file=800*MIB)
    result = sample(tmp_path, values, 1000*MIB, unified)
    assert result['reclaimable_bytes'] == 300*MIB
    assert result['working_bytes'] == 700*MIB
    values[names[1]] = 1000*MIB
    assert sample(tmp_path, values, 1000*MIB, unified)['reclaimable_bytes'] == 0


def test_v1_hierarchical_counters_take_precedence_without_double_counting(tmp_path):
    values = dict(cache=100*MIB, inactive_file=50*MIB, total_cache=500*MIB,
                  total_inactive_file=400*MIB, total_shmem=150*MIB, total_dirty=100*MIB)
    assert sample(tmp_path, values, 800*MIB)['reclaimable_bytes'] == 250*MIB


@pytest.mark.parametrize('content', ['', 'cache not-a-number', 'bad line with extra fields'])
def test_unavailable_statistics_fail_closed(tmp_path, content):
    assert pressure_sample(tmp_path, True, 123)['working_bytes'] == 123
    (tmp_path/'memory.stat').write_text(content)
    assert pressure_sample(tmp_path, True, 123)['reclaimable_bytes'] == 0


def test_accounting_is_bounded_when_statistics_change_during_read(tmp_path):
    result = sample(tmp_path, dict(file=1000, inactive_file=900), 100, True)
    assert result['reclaimable_bytes'] == 100 and result['working_bytes'] == 0


def test_nonreclaimable_pressure_still_shrinks_pool(tmp_path):
    result = sample(tmp_path, dict(file=50*MIB, inactive_file=10*MIB), 900*MIB, True)
    policy = ResourcePolicy(1024*MIB, 10)
    assert policy.decide(result['working_bytes'], 3, False, False, 100*MIB, 0) == 'shrink'


def test_legacy_patch_is_idempotent_and_leaves_core_files_unchanged(tmp_path, monkeypatch):
    from overviewer_core import adaptive
    core = Path(adaptive.__file__)
    before = core.read_bytes()
    monkeypatch.delattr(CgroupMemory, 'pressure_sample')
    monkeypatch.setattr(ResourcePolicy, 'decide', ResourcePolicy.decide)
    (tmp_path/'memory.limit_in_bytes').write_text(str(10*1024**3))
    (tmp_path/'memory.stat').write_text('cache 7653220352\ninactive_file 6151872512\nshmem 0\n')
    monkeypatch.setenv('OVERVIEWER_CGROUP_PATH', str(tmp_path))
    install_legacy()
    patched = ResourcePolicy.decide
    install_legacy()
    assert ResourcePolicy.decide is patched
    policy = ResourcePolicy(10*1024**3, 10)
    assert policy.decide(10158833664, 1, False, False, 1507392*1024, 0) == 'grow'
    assert core.read_bytes() == before
