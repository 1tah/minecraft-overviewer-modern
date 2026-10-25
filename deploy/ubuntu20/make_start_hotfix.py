"""Create the journal-compatible initial-pool patch for existing ready bundles."""
import base64
import hashlib
import json
from pathlib import Path
import sys

repo = Path(__file__).resolve().parents[2]
payloads = {}
for name in ('overviewer_cache_policy.py', 'overviewer_worker_start.py'):
    data = (repo/name).read_text(encoding='utf-8').encode('utf-8')
    payloads[name] = dict(data=base64.b64encode(data).decode(), sha256=hashlib.sha256(data).hexdigest())
template = r'''#!/usr/bin/env python3
"""Add --start-workers without changing hashed core files. GPL-3.0-or-later."""
import ast,base64,hashlib,json,os,shutil,sys,tempfile
from pathlib import Path
PAYLOADS = json.loads('__PAYLOADS__')
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
app=root/'app' if (root/'app/overviewer.py').is_file() else root
main=app/'overviewer.py'
core=app/'overviewer_core'
if not main.is_file() or not (core/'adaptive.py').is_file():
    raise SystemExit('Provide the existing CublayCraft-Overviewer directory.')
adaptive=(core/'adaptive.py').read_text(encoding='utf-8')
if 'supports_start_workers = True' in adaptive:
    print('This build already supports --start-workers. No changes needed.')
    sys.exit(0)
if 'requested_maximum' not in adaptive:
    raise SystemExit('Requires an adaptive build from resume.6 or newer; no files changed.')
def fingerprint():
    digest=hashlib.sha256()
    for path in sorted(core.rglob('*')):
        if path.suffix in ('.py','.c','.h'):
            digest.update(path.relative_to(core).as_posix().encode()); digest.update(path.read_bytes())
    return digest.hexdigest()
before=fingerprint()
text=main.read_text(encoding='utf-8')
guard='if __name__ == "__main__":'
if text.count(guard)!=1:
    raise SystemExit('Unexpected entry point; no files changed.')
if '# OVERVIEWER_START_FIX_1' not in text:
    text=text.replace(guard,guard+'\n    # OVERVIEWER_START_FIX_1\n    from overviewer_worker_start import install_legacy as _install_start_pool\n    _install_start_pool()',1)
if '# OVERVIEWER_CACHE_FIX_1' not in text:
    text=text.replace(guard,guard+'\n    # OVERVIEWER_CACHE_FIX_1\n    from overviewer_cache_policy import install_legacy as _install_cache_policy\n    _install_cache_policy()',1)
ast.parse(text)
decoded={}
for name,record in PAYLOADS.items():
    data=base64.b64decode(record['data'])
    assert hashlib.sha256(data).hexdigest()==record['sha256']
    ast.parse(data.decode('utf-8'))
    decoded[name]=data
backup=main.with_name('overviewer.py.before-start-workers.bak')
if not backup.exists(): shutil.copy2(main,backup)
identity=main.stat()
def atomic(path,data):
    fd,name=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.chmod(name,identity.st_mode & 0o777)
        if os.geteuid()==0: os.chown(name,identity.st_uid,identity.st_gid)
        os.replace(name,path)
    finally:
        if os.path.exists(name): os.unlink(name)
for name,data in decoded.items(): atomic(app/name,data)
atomic(main,text.encode('utf-8'))
assert fingerprint()==before
print('Initial worker pool installed. Core identity unchanged; saved plans remain compatible.')
print('Restart with --start-workers=6 --cpu-limit=10 --memory-limit=13G, same config/output.')
print('Continue without --forcerender or --discard-resume.')
'''
Path(sys.argv[1]).write_text(template.replace('__PAYLOADS__',json.dumps(payloads)),encoding='utf-8',newline='\n')
print(sys.argv[1])
