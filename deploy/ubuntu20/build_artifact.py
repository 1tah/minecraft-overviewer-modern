"""Assemble the native server archive after setup.py build in Ubuntu 20.04."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

parser = argparse.ArgumentParser()
parser.add_argument('--source', required=True, type=Path)
parser.add_argument('--runtime', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--revision', default='unknown')
parser.add_argument('--native-module', type=Path)
parser.add_argument('--reports', type=Path)
args = parser.parse_args()
source, runtime, output = args.source.resolve(), args.runtime.resolve(), args.output.resolve()
deploy = source/'deploy/ubuntu20'
bundle = output/'CublayCraft-Overviewer'
if bundle.exists():
    raise SystemExit('Use a new empty output directory')
bundle.mkdir(parents=True)
shutil.copytree(runtime, bundle/'runtime', symlinks=True)
app = bundle/'app'
app.mkdir()
for name in ('overviewer_core', 'contrib', 'test'):
    shutil.copytree(source/name, app/name, ignore=shutil.ignore_patterns(
        '__pycache__', '.pytest_cache', '*.so', '*.pyd', '*.dll'))
for file in source.iterdir():
    if file.is_file() and (file.suffix in ('.py', '.md', '.rst') or
                           file.name in ('COPYING.txt', 'requirements.txt', 'MANIFEST.in', 'setup.cfg')):
        shutil.copyfile(file, app/file.name)
native = args.native_module or next((source/'overviewer_core').glob('c_overviewer.cpython-312-*.so'))
shutil.copyfile(native, app/'overviewer_core'/native.name)
namespace = {}
exec((source/'overviewer_core/util.py').read_text().split('DIMENSION_INFO =')[0], namespace)
version = namespace['DEFAULT_VERSION']
(app/'overviewer_core/overviewer_version.py').write_text(
    "VERSION=%r\nHASH=%r\nBUILD_DATE='2026-10-24'\nBUILD_PLATFORM='Ubuntu 20.04 x86_64 / GCC 9'\nBUILD_OS='Linux'\n"
    % (version, args.revision))
for name in ('overviewer.py', 'cgroup_runner.py', 'mark_oom.py', 'get-textures.py',
             'serve.py', 'configNew.py', 'START.sh', 'START_HERE_RU.md', 'ICONS.txt',
             'runtime-python.json', 'requirements.lock.txt'):
    (bundle/name).write_text((deploy/name).read_text(encoding='utf-8'), encoding='utf-8', newline='\n')
for name in ('overviewer.py', 'get-textures.py', 'serve.py', 'START.sh'):
    (bundle/name).chmod(0o755)
shutil.copyfile(source/'COPYING.txt', bundle/'COPYING.txt')
shutil.copytree(deploy/'icons', bundle/'output/icons')
shutil.copytree(deploy/'pillow_include', bundle/'build-tools/pillow-headers')
for name in ('assets', 'worlds/2015', 'worlds/2015_nether', 'worlds/2015_the_end', 'worlds/plotworld'):
    (bundle/name).mkdir(parents=True, exist_ok=True)
(bundle/'worlds/README.txt').write_text('Поместите сохранения в эти папки либо укажите свои пути в configNew.py.\nlevel.dat должен находиться в корне сохранения, не в dimensions/.\n', encoding='utf-8')
(bundle/'assets/README.txt').write_text('Клиентский JAR: client.jar. START.sh загрузит 1.21.5, если файла нет.\nДля 26.3: MINECRAFT_VERSION=26.3 ./START.sh при отсутствии client.jar.\n', encoding='utf-8')
dependencies = subprocess.check_output([str(runtime/'bin/python3'), '-m', 'pip', 'freeze'], text=True).splitlines()
info = dict(source_commit=args.revision, version=version, built_for='Ubuntu 20.04 x86_64, glibc 2.31',
            python_runtime=json.loads((deploy/'runtime-python.json').read_text()), dependencies=dependencies,
            palette_26_3_hotfix_included=True, includes_user_worlds=False, includes_mojang_assets=False,
            cgroup_v1_note='Supported interface; not tested on the target server kernel.')
if args.reports:
    shutil.copytree(args.reports, bundle/'reports')
(bundle/'BUILD_INFO.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
assert not list((bundle/'assets').glob('*.jar'))
for link in bundle.rglob('*'):
    if link.is_symlink() and not link.resolve().is_relative_to(bundle):
        raise SystemExit('External symlink in bundle: '+str(link))
archive = output/'CublayCraft-Overviewer-Ubuntu20.04-x86_64.tar.gz'
with tarfile.open(archive, 'w:gz', compresslevel=6) as tar:
    tar.add(bundle, arcname=bundle.name)
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(output/(archive.name+'.sha256')).write_text(digest+'  '+archive.name+'\n')
print(archive)
print('SHA256:', digest)
