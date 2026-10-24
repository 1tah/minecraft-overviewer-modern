"""Download the pinned Astral runtime for building; verify before extraction."""
import hashlib
import json
from pathlib import Path
import posixpath
import shutil
import sys
import tarfile
import tempfile
import urllib.request

spec = json.loads(Path(__file__).with_name('runtime-python.json').read_text())
destination = Path(sys.argv[1]).resolve()
if destination.exists():
    raise SystemExit('Runtime target already exists')
destination.parent.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
    temporary = Path(temporary)
    archive = temporary/'runtime.tar.gz'
    urllib.request.urlretrieve(spec['url'], archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != spec['sha256']:
        raise SystemExit('Python archive SHA-256 mismatch')
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            name = posixpath.normpath(member.name)
            if not (name == 'python' or name.startswith('python/')) or member.isdev():
                raise SystemExit('Invalid runtime archive member')
            if member.issym() or member.islnk():
                target = member.linkname if member.islnk() else posixpath.join(posixpath.dirname(name), member.linkname)
                target = posixpath.normpath(target)
                if not target.startswith('python/'):
                    raise SystemExit('External runtime symlink')
        tar.extractall(temporary)
    shutil.move(str(temporary/'python'), str(destination))
print('Verified Python runtime:', destination)
