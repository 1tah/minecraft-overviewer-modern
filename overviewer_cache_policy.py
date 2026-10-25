"""Conservative clean-cache accounting; stdlib only, also used by the hotfix.

Kept outside overviewer_core so installing the legacy policy patch does not
change the render-journal identity or invalidate unfinished tile plans.
"""
import logging
from pathlib import Path


def pressure_sample(path, unified, usage):
    """Discount at most inactive, potentially clean, non-shmem file pages.

    Never subtract anonymous memory, active file pages, dirty/writeback pages
    or slab. Missing/malformed statistics fall back to the full kernel usage.
    Counters overlap; they must not simply be added together.
    """
    result = dict(usage_bytes=usage, working_bytes=usage, reclaimable_bytes=0)
    try:
        stats = {key: max(0, int(value)) for key, value in
                 (line.split() for line in (Path(path)/'memory.stat').read_text().splitlines())}
        def counter(name):
            return stats.get('total_'+name, stats.get(name, 0)) if not unified else stats.get(name, 0)
        file_bytes = counter('file' if unified else 'cache')
        dirty = counter('file_dirty' if unified else 'dirty')
        writeback = counter('file_writeback' if unified else 'writeback')
        clean_budget = max(0, file_bytes-counter('shmem')-dirty-writeback)
        reclaimable = min(max(0, usage), counter('inactive_file'), clean_budget)
        result.update(working_bytes=max(0, usage-reclaimable), reclaimable_bytes=reclaimable)
    except (OSError, ValueError):
        pass
    return result


def install_legacy():
    """Patch the old controller in memory, without changing hashed core files."""
    from overviewer_core import adaptive
    if hasattr(adaptive.CgroupMemory, 'pressure_sample'):
        return  # Current builds already use the native implementation.
    original = adaptive.ResourcePolicy.decide
    if getattr(original, '_cache_aware', False):
        return

    def decide(self, usage, live, starting, retiring, estimate, now):
        try:
            memory = getattr(self, '_cache_memory', None)
            if memory is None:
                memory = self._cache_memory = adaptive.CgroupMemory()
            sample = pressure_sample(memory.path, memory.v2, usage)
        except (OSError, ValueError, RuntimeError):
            sample = dict(usage_bytes=usage, working_bytes=usage, reclaimable_bytes=0)
        action = original(self, sample['working_bytes'], live, starting, retiring, estimate, now)
        if action:
            logging.info('Cache-aware %s: RAM %.0f MiB; working %.0f MiB; inactive clean cache %.0f MiB',
                         action, usage/1024**2, sample['working_bytes']/1024**2,
                         sample['reclaimable_bytes']/1024**2)
        return action
    decide._cache_aware = True
    adaptive.ResourcePolicy.decide = decide
    print('Cache-aware memory policy enabled; kernel RAM cap unchanged.', flush=True)
