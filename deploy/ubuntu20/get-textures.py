#!/bin/sh
''':'
exec "$(dirname "$0")/runtime/bin/python3" "$0" "$@"
':'''
"""Download a client JAR from Mojang metadata, verifying both SHA-1 values."""
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

root = Path(__file__).resolve().parent
version = sys.argv[1] if len(sys.argv) > 1 else '1.21.5'
manifest = json.load(urllib.request.urlopen('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json'))
entry = next((item for item in manifest['versions'] if item['id'] == version), None)
if not entry:
    sys.exit('Version not found in Mojang manifest: ' + version)
metadata = urllib.request.urlopen(entry['url']).read()
if hashlib.sha1(metadata).hexdigest() != entry['sha1']:
    sys.exit('Version metadata checksum mismatch')
client = json.loads(metadata)['downloads']['client']
assets = root/'assets'
assets.mkdir(exist_ok=True)
destination = assets/'client.jar'
if destination.exists():
    sys.exit('assets/client.jar already exists. Move it aside before downloading another version.')
temporary = assets/'client.jar.download'
print('Downloading official Minecraft Java client', version, flush=True)
urllib.request.urlretrieve(client['url'], temporary)
if hashlib.sha1(temporary.read_bytes()).hexdigest() != client['sha1']:
    sys.exit('Client checksum mismatch; client.jar was not published')
temporary.replace(destination)
(assets/'client-version.txt').write_text(version+'\n', encoding='utf-8')
print('Verified:', destination)
