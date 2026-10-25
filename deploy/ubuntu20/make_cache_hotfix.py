"""Generate one stdlib-only server patch that preserves existing journal keys."""
import base64
import hashlib
from pathlib import Path
import sys

source = Path(__file__).resolve().parents[2]/'overviewer_cache_policy.py'
payload = source.read_text(encoding='utf-8').encode('utf-8')
target = Path(sys.argv[1])
template = r'''#!/usr/bin/env python3
"""Fix cache-aware worker growth without invalidating saved render plans.
Stop the render with Ctrl+C, run this from the bundle directory, restart normally.
"""
import ast, base64, hashlib, os, shutil, sys, tempfile
from pathlib import Path

PAYLOAD = '__PAYLOAD__'
SHA256 = '__SHA256__'
root = Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
app = root/'app' if (root/'app/overviewer.py').is_file() else root
main = app/'overviewer.py'
core = app/'overviewer_core'
if not main.is_file() or not (core/'adaptive.py').is_file():
    raise SystemExit('Run from CublayCraft-Overviewer or provide its directory as an argument.')
if 'def pressure_sample(' in (core/'adaptive.py').read_text(encoding='utf-8'):
    raise SystemExit('This build already includes the cache-aware controller. No changes made.')
def fingerprint():
    digest=hashlib.sha256()
    for path in sorted(core.rglob('*')):
        if path.suffix in ('.py','.c','.h'):
            digest.update(path.relative_to(core).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()
before=fingerprint()
text=main.read_text(encoding='utf-8')
marker='# OVERVIEWER_CACHE_FIX_1'
guard='if __name__ == "__main__":'
if marker not in text:
    if text.count(guard)!=1:
        raise SystemExit('Unexpected entry point; no files changed.')
    text=text.replace(guard,guard+'\n    '+marker+'\n    from overviewer_cache_policy import install_legacy\n    install_legacy()',1)
ast.parse(text)
payload=base64.b64decode(PAYLOAD)
assert hashlib.sha256(payload).hexdigest()==SHA256
ast.parse(payload.decode('utf-8'))
backup=main.with_name('overviewer.py.before-cache-fix.bak')
if not backup.exists(): shutil.copy2(main,backup)
def atomic(path,data,identity):
    fd,temporary=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary,identity.st_mode & 0o777)
        if os.geteuid()==0: os.chown(temporary,identity.st_uid,identity.st_gid)
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
identity=main.stat()
atomic(app/'overviewer_cache_policy.py',payload,identity)
atomic(main,text.encode('utf-8'),identity)
assert fingerprint()==before,'Core identity changed unexpectedly'
print('Cache-aware policy installed. Hashed core files are unchanged; saved plans remain compatible.')
print('Restart the SAME render command, WITHOUT --forcerender or --discard-resume.')
print('Startup log: Cache-aware memory policy enabled. Resume log: skipping chunk/tile scan.')
'''
target.write_text(template.replace('__PAYLOAD__',base64.b64encode(payload).decode())
                  .replace('__SHA256__',hashlib.sha256(payload).hexdigest()),encoding='utf-8',newline='\n')
print(target)
