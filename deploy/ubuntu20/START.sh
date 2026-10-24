#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -f assets/client.jar ]; then
    ./get-textures.py "${MINECRAFT_VERSION:-1.21.5}"
fi
exec ./overviewer.py --config=./configNew.py "$@"
