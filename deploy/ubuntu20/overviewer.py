#!/bin/sh
''':'
exec "$(dirname "$0")/runtime/bin/python3" "$0" "$@"
':'''
"""Ubuntu 20.04 launcher; system Python 3.8 runs only this stdlib wrapper."""
import os
from pathlib import Path
import pwd
import re
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def parse_limit(arguments):
    forwarded = []
    requested = None
    items = iter(arguments)
    for item in items:
        if item == '--memory-limit':
            requested = next(items, '')
        elif item.startswith('--memory-limit='):
            requested = item.split('=', 1)[1]
        else:
            forwarded.append(item)
    total = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                     if line.startswith('MemTotal:'))) * 1024
    if requested is None:
        limit = min(8*1024**3, int(total*0.7)) // 4096 * 4096
    else:
        match = re.fullmatch(r'([1-9][0-9]*)([KMGT]?)', requested.upper())
        if not match:
            raise ValueError('--memory-limit expects a size such as 8G')
        limit = int(match[1]) * (1024 ** ('KMGT'.index(match[2])+1) if match[2] else 1)
    if limit < 64*1024**2 or limit > total*0.9:
        raise ValueError('Choose RAM >=64M and <=90% of server RAM; leave memory for the OS.')
    return forwarded, limit


def main():
    if not sys.platform.startswith('linux'):
        raise RuntimeError('This archive is for Ubuntu Linux x86_64')
    runtime = ROOT/'runtime/bin/python3'
    app = ROOT/'app/overviewer.py'
    if not runtime.exists():
        raise RuntimeError('Bundled Python is missing; extract the complete tar.gz archive.')
    arguments = sys.argv[1:] or ['--config=./configNew.py']
    if any(item in ('--version', '-V', '--help', '-h') for item in arguments):
        return subprocess.call([str(runtime), str(app), *arguments], cwd=str(ROOT))
    forwarded, limit = parse_limit(arguments)
    if os.geteuid() != 0:
        print('sudo is required only to create a kernel RAM limit; renderer keeps your UID.', flush=True)
        return subprocess.call(['sudo', '--', sys.executable, str(ROOT/'overviewer.py'), *arguments])
    uid = int(os.environ.get('SUDO_UID', '0'))
    gid = int(os.environ.get('SUDO_GID', str(os.getgid())))
    account = pwd.getpwuid(uid)
    environment = dict(os.environ, HOME=account.pw_dir, USER=account.pw_name,
                       LOGNAME=account.pw_name, OVERVIEWER_HOME=str(ROOT))
    for key in ('SUDO_UID', 'SUDO_GID', 'SUDO_USER', 'PYTHONHOME', 'PYTHONPATH'):
        environment.pop(key, None)
    environment['PYTHONPATH'] = str(ROOT/'app')
    from cgroup_runner import run, drop_user
    from resource_session import ResourceSession, pin_cpus
    import argparse
    options = argparse.ArgumentParser(add_help=False)
    options.add_argument('--cpu-limit', type=int)
    options.add_argument('-p', '--processes', dest='workers', type=int)
    options.add_argument('--start-workers', type=int)
    opts, _ = options.parse_known_args(forwarded)
    automatic = '--fixed-resources' not in forwarded and '--genpoi' not in forwarded
    cpu_request = opts.cpu_limit if opts.cpu_limit is not None else (opts.workers if automatic and opts.workers and opts.workers > 0 else None)
    cpus = pin_cpus(cpu_request)
    maximum = min(len(cpus), opts.workers) if opts.workers and opts.workers > 0 else len(cpus)
    if opts.start_workers is not None:
        if not automatic:
            raise ValueError('--start-workers requires automatic rendering')
        if not 1 <= opts.start_workers <= maximum:
            raise ValueError('--start-workers must be between 1 and %d' % maximum)
    if automatic:
        if '--auto-resources' not in forwarded:
            forwarded.append('--auto-resources')
        environment.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    signal.signal(signal.SIGTERM, lambda signum, frame: (_ for _ in ()).throw(KeyboardInterrupt()))
    session = ResourceSession(maximum, cpus, limit, uid, gid) if automatic else None
    ceiling = maximum
    try:
        while True:
            details = {}
            attempt_env = dict(environment, **session.environment(ceiling)) if session else environment
            result, oom = run([str(runtime), str(app), *forwarded], limit, uid, gid, attempt_env, ROOT, details)
            if not session:
                break
            session.record(result, oom, details)
            next_ceiling = session.retry_ceiling(ceiling) if oom else None
            if next_ceiling is None:
                break
            ceiling = next_ceiling
            forwarded = [arg for arg in forwarded if arg != '--discard-resume']
            print('Auto resources: retry saved plan with at most {} workers.'.format(ceiling), flush=True)
        if session:
            def finalize_as_user():
                drop_user(uid, gid)
            subprocess.run([str(runtime), str(ROOT/'resource_session.py'), str(session.export())],
                           cwd=str(ROOT), env=environment, preexec_fn=finalize_as_user, check=True)
    finally:
        if session:
            session.close()
    if oom:
        def unprivileged():
            drop_user(uid, gid)
        subprocess.run([str(runtime), str(ROOT/'mark_oom.py'), *forwarded], cwd=str(ROOT),
                       env=environment, preexec_fn=unprivileged)
    return result


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, OSError) as error:
        print('Cannot start:', error, file=sys.stderr)
        sys.exit(2)
