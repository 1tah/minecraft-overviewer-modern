"""Re-execute inside a kernel-enforced memory cgroup, before loading a world."""
import re
import shutil
import subprocess
import sys
from pathlib import Path


def verify_scope(limit):
    for entry in Path('/proc/self/cgroup').read_text().splitlines():
        if entry.startswith('0::'):
            group = Path('/sys/fs/cgroup') / entry[3:].lstrip('/')
            actual = (group / 'memory.max').read_text().strip()
            swap = (group / 'memory.swap.max').read_text().strip()
            if actual != 'max' and 0 < int(actual) <= limit and swap == '0':
                return
    raise RuntimeError('The memory cgroup did not enforce the requested limit; refusing to render.')


def run_limited(limit, argv):
    if not re.fullmatch(r'[1-9][0-9]*(?:[KMGT])?', limit, re.IGNORECASE):
        raise ValueError('--memory-limit expects positive bytes or a size such as 8G')
    if not sys.platform.startswith('linux') or not shutil.which('systemd-run'):
        raise RuntimeError('--memory-limit requires Linux with systemd-run and a user systemd session. '
                           'No unbounded render was started.')
    if not Path('/sys/fs/cgroup/cgroup.controllers').exists():
        raise RuntimeError('--memory-limit requires cgroup v2.')
    match = re.fullmatch(r'([1-9][0-9]*)([KMGT]?)', limit.upper())
    size = int(match[1]) * (1024 ** ('KMGT'.index(match[2])+1) if match[2] else 1)
    forwarded = []
    skip = False
    for arg in argv:
        if skip:
            skip = False
        elif arg == '--memory-limit':
            skip = True
        elif not arg.startswith('--memory-limit='):
            forwarded.append(arg)
    command = ['systemd-run', '--user', '--scope', '--quiet', '--expand-environment=no',
               '--property=MemoryAccounting=yes', '--property=MemoryMax=' + limit.upper(),
               '--property=MemorySwapMax=0', '--property=OOMPolicy=kill',
               '--', sys.executable, *forwarded, '--verify-memory-limit', str(size)]
    return subprocess.call(command)
