import multiprocessing
import subprocess
import sys

import pytest


@pytest.mark.parametrize('method', multiprocessing.get_all_start_methods())
def test_manager_parent_guard_supports_all_start_methods(method):
    # A separate interpreter leaves the test runner's start method untouched.
    program = '''
import multiprocessing, os, sys
from overviewer_core.dispatcher import MultiprocessingDispatcherManager, follow_parent
if __name__ == '__main__':
    multiprocessing.set_start_method(sys.argv[1], force=True)
    manager = MultiprocessingDispatcherManager()
    manager.start(initializer=follow_parent, initargs=(os.getpid(),))
    try:
        jobs = manager.get_job_queue()
        jobs.put('ready')
        assert jobs.get(timeout=5) == 'ready'
    finally:
        manager.shutdown()
    print('parent guard OK')
'''
    result = subprocess.run([sys.executable, '-c', program, method], capture_output=True,
                            text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'parent guard OK' in result.stdout
