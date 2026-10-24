"""Run explicitly as root on Linux: bounded OOM/retry through the shipped launcher.

Uses a tiny fake renderer; never opens a user's world or modifies an installed bundle.
Usage: python3 test/native_resource_probe.py /path/to/bundled/runtime/bin/python3
"""
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import sys
import tempfile


def main():
    assert os.geteuid() == 0, 'Needs a writable memory cgroup'
    source = Path(__file__).resolve().parents[1]
    account = pwd.getpwnam(os.environ.get('PROBE_USER', 'nobody'))
    with tempfile.TemporaryDirectory(prefix='overviewer-oom-probe-') as temporary:
        root = Path(temporary)
        os.chown(root, account.pw_uid, account.pw_gid)
        for name in ('app', 'runtime/bin'):
            (root/name).mkdir(parents=True)
        (root/'runtime/bin/python3').symlink_to(Path(sys.argv[1]).resolve())
        for name in ('overviewer.py', 'cgroup_runner.py', 'mark_oom.py'):
            (root/name).write_text((source/'deploy/ubuntu20'/name).read_text())
        shutil.copyfile(source/'overviewer_core/resource_session.py', root/'resource_session.py')
        (root/'app/overviewer.py').write_text('''
import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from resource_session import atomic_json
ceiling=int(os.environ['OVERVIEWER_WORKER_CEILING'])
if os.environ.get('PROBE_INSUFFICIENT'):
    ceiling=int(os.environ['PROBE_INSUFFICIENT'])
root=Path.cwd()
with (root/'saved-plan.txt').open('a') as stream:
    stream.write(str(ceiling)+'\\n')
atomic_json(os.environ['OVERVIEWER_RESOURCE_STATE'],dict(current_workers=ceiling,
    outputdir=str(root),min_workers=1,max_workers_observed=ceiling,worker_seconds=2,
    render_seconds=1,completed_this_attempt=1,recommended_workers=ceiling,
    cpu_ids=sorted(os.sched_getaffinity(0))))
if ceiling>2 or os.environ.get('PROBE_INSUFFICIENT'):
    data=bytearray(128*1024**2)
assert os.getuid()!=0
assert len(os.sched_getaffinity(0))==4
''')
        (root/'overviewer.py').chmod(0o755)
        env = dict(os.environ, SUDO_UID=str(account.pw_uid), SUDO_GID=str(account.pw_gid),
                   SUDO_USER=account.pw_name)
        result = subprocess.run([str(root/'overviewer.py'), '--cpu-limit=4', '--memory-limit=64M'],
                                env=env, capture_output=True, text=True, timeout=60)
        print(result.stdout)
        assert result.returncode == 0, result.stderr
        # CPU maximum is 4, then the memory fallback halves it to 2.
        assert (root/'saved-plan.txt').read_text().splitlines() == ['4', '2']
        report = json.loads((root/'render-resources.json').read_text())
        assert report['oom_restarts'] == 1 and report['status'] == 'complete'
        assert report['recommended_workers'] == 2
        assert report['completed_this_session'] == 2
        assert report['peak_memory_bytes'] >= 60*1024**2
        assert (root/'render-resources.json').stat().st_uid == account.pw_uid
        assert report['attempts'][0]['oom'] is True
        print('PASS: real kernel OOM, bounded retry, saved state, CPU affinity and caller-owned report')
        for insufficient in ('1', '0'):
            failed = subprocess.run([str(root/'overviewer.py'), '--cpu-limit=4', '--memory-limit=64M'],
                env=dict(env, PROBE_INSUFFICIENT=insufficient), capture_output=True, text=True, timeout=30)
            assert failed.returncode == 137, failed.stdout+failed.stderr
            report = json.loads((root/'render-resources.json').read_text())
            assert len(report['attempts']) == 1 and report['status'] == 'error'
            assert report['oom_restarts'] == 0
            assert 'Не хватает памяти' in failed.stdout
        print('PASS: preparation/one-worker OOM stops clearly without retry loops')


if __name__ == '__main__':
    main()
