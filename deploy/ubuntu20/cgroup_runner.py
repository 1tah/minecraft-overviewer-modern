"""Small root supervisor for cgroup v1/v2; render children run as caller UID.

GPL-3.0-or-later, like the bundled Overviewer sources.
"""
import os
from pathlib import Path
import pwd
import signal
import subprocess
import time
import uuid


def counters(path):
    return {key: int(value) for key, value in
            (line.split() for line in path.read_text().splitlines())}


def memory_group(limit):
    unified = Path('/sys/fs/cgroup')
    if (unified/'cgroup.controllers').exists():
        if 'memory' not in (unified/'cgroup.controllers').read_text().split():
            raise RuntimeError('Memory controller is unavailable; refusing an unbounded render.')
        (unified/'cgroup.subtree_control').write_text('+memory')
        base, version = unified, 2
    else:
        base = None
        for line in Path('/proc/mounts').read_text().splitlines():
            fields = line.split()
            if fields[2] == 'cgroup' and 'memory' in fields[3].split(','):
                base = Path(fields[1].replace('\\040', ' '))
                break
        if base is None:
            raise RuntimeError('cgroup memory is not mounted; no unbounded render was started.')
        version = 1
    group = base/('overviewer-' + uuid.uuid4().hex)
    group.mkdir()
    try:
        if version == 2:
            (group/'memory.max').write_text(str(limit))
            (group/'memory.swap.max').write_text('0')
            (group/'memory.oom.group').write_text('1')
            actual = int((group/'memory.max').read_text())
            events = group/'memory.events'
            if (group/'memory.swap.max').read_text().strip() != '0':
                raise RuntimeError('Swap limit verification failed')
        else:
            (group/'memory.limit_in_bytes').write_text(str(limit))
            if (group/'memory.memsw.limit_in_bytes').exists():
                (group/'memory.memsw.limit_in_bytes').write_text(str(limit))
                if int((group/'memory.memsw.limit_in_bytes').read_text()) > limit:
                    raise RuntimeError('RAM+swap limit verification failed')
            elif (group/'memory.swappiness').exists():
                (group/'memory.swappiness').write_text('0')
                print('Note: kernel has no memsw accounting; RAM is capped, memory.swappiness=0.', flush=True)
            actual = int((group/'memory.limit_in_bytes').read_text())
            events = group/'memory.oom_control'
        if not 0 < actual <= limit:
            raise RuntimeError('Kernel did not apply the RAM limit')
        if 'oom_kill' not in counters(events):
            raise RuntimeError('Kernel OOM counter is unavailable; refusing to lose worker failures.')
        return group, events, version, actual
    except BaseException:
        group.rmdir()
        raise


def drop_user(uid, gid):
    if uid:
        account = pwd.getpwuid(uid)
        os.initgroups(account.pw_name, gid)
        os.setgid(gid)
        os.setuid(uid)


def _stop_group(process, group, grace=15):
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            pass
    # Kill only members of the unique cgroup created for this launch.
    for _ in range(30):
        pids = (group/'cgroup.procs').read_text().split()
        if not pids:
            break
        for pid in pids:
            try:
                identity = Path('/proc')/pid/'cgroup'
                if group.name in identity.read_text():
                    os.kill(int(pid), signal.SIGKILL)
            except (FileNotFoundError, ProcessLookupError):
                pass
        time.sleep(0.1)
    if process.poll() is None:
        process.wait(timeout=5)


def run(command, limit, uid, gid, environment, cwd, details=None):
    group, events, version, actual = memory_group(limit)
    print('Verified cgroup v{} RAM cap: {} bytes; workers UID={}.'.format(version, actual, uid), flush=True)
    before = counters(events)['oom_kill']
    process = None
    oom = False
    details = details if details is not None else {}
    environment = dict(environment, OVERVIEWER_CGROUP_PATH=str(group))
    usage_file = group/('memory.current' if version == 2 else 'memory.usage_in_bytes')
    peak_file = group/('memory.peak' if version == 2 else 'memory.max_usage_in_bytes')
    try:
        def prepare_child():
            os.setsid()
            (group/'cgroup.procs').write_text(str(os.getpid()))
            drop_user(uid, gid)
        process = subprocess.Popen(command, cwd=str(cwd), env=environment, preexec_fn=prepare_child)
        try:
            while True:
                peak = int((peak_file if peak_file.exists() else usage_file).read_text())
                details['peak_memory_bytes'] = max(details.get('peak_memory_bytes', 0), peak)
                if counters(events)['oom_kill'] > before:
                    oom = True
                    print('Kernel RAM limit reached; saved tile plan retained.', flush=True)
                    break
                if process.poll() is not None:
                    break
                time.sleep(0.2)
        except KeyboardInterrupt:
            print('Stopping render and saving acknowledged progress...', flush=True)
        finally:
            _stop_group(process, group)
            oom = oom or counters(events)['oom_kill'] > before
            if peak_file.exists():
                details['peak_memory_bytes'] = max(details.get('peak_memory_bytes', 0), int(peak_file.read_text()))
        return (137 if oom else (process.returncode if process.returncode >= 0 else 128-process.returncode)), oom
    finally:
        if process is not None and process.poll() is None:
            _stop_group(process, group, grace=1)
        try:
            group.rmdir()
        except OSError:
            print('Warning: cgroup cleanup delayed:', group, flush=True)
