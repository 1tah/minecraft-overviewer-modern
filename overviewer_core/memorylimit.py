"""Re-execute inside a kernel-enforced memory cgroup, before loading a world."""
import re
import shutil
import subprocess
import sys
import os
import uuid
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
    automatic = '--auto-resources' in forwarded and '--genpoi' not in forwarded
    if not automatic:
        return subprocess.call(command)
    import argparse
    from .resource_session import ResourceSession, pin_cpus, finalize_session
    options = argparse.ArgumentParser(add_help=False)
    options.add_argument('--cpu-limit', type=int)
    options.add_argument('-p', '--processes', dest='workers', type=int)
    opts, _ = options.parse_known_args(forwarded[1:])
    cpus = pin_cpus(opts.cpu_limit or (opts.workers if opts.workers and opts.workers > 0 else None))
    maximum = min(len(cpus), opts.workers) if opts.workers and opts.workers > 0 else len(cpus)
    session = ResourceSession(maximum, cpus, size)
    ceiling = maximum
    try:
        while True:
            unit = 'overviewer-'+uuid.uuid4().hex+'.scope'
            environment = dict(os.environ, **session.environment(ceiling))
            result = subprocess.call(command[:1]+['--unit='+unit]+command[1:], env=environment)
            outcome = subprocess.run(['systemctl', '--user', 'show', unit, '--property=Result', '--property=MemoryPeak'],
                                     capture_output=True, text=True)
            properties = dict(line.split('=', 1) for line in outcome.stdout.splitlines() if '=' in line)
            oom = outcome.returncode == 0 and properties.get('Result') == 'oom-kill'
            peak = properties.get('MemoryPeak', '')
            details = {'peak_memory_bytes': int(peak)} if peak.isdigit() and int(peak) < 2**60 else {}
            session.record(result, oom, details)
            subprocess.run(['systemctl', '--user', 'reset-failed', unit], capture_output=True)
            next_ceiling = session.retry_ceiling(ceiling) if oom else None
            if next_ceiling is None:
                break
            ceiling = next_ceiling
            command = [arg for arg in command if arg != '--discard-resume']
            print('Auto resources: resume saved plan with at most %d workers.' % ceiling, flush=True)
        finalize_session(session.export())
        return result
    finally:
        session.close()
