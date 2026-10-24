#!/bin/sh
''':'
exec "$(dirname "$0")/runtime/bin/python3" "$0" "$@"
':'''
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=8080)
parser.add_argument('--bind', default='127.0.0.1')
parser.add_argument('--directory', default=str(Path(__file__).resolve().parent/'output'))
args = parser.parse_args()
Path(args.directory).mkdir(parents=True, exist_ok=True)
print('Serving {} at http://{}:{}/'.format(args.directory, args.bind, args.port), flush=True)
ThreadingHTTPServer((args.bind, args.port), partial(SimpleHTTPRequestHandler, directory=args.directory)).serve_forever()
