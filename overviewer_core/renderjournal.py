"""Durable, bounded-memory render plans. Only the coordinator writes this DB.

Completion is recorded AFTER the worker atomically publishes the image. A crash
may repeat an acknowledged-but-uncommitted batch; it cannot skip unfinished work.
"""
import json
import os
import sqlite3
import time
import hashlib
import pickle
import weakref
from contextlib import closing
from pathlib import Path


class OutputLock:
    """OS lock releases on a crash; the marker file is deliberately persistent."""
    def __init__(self, directory):
        self.stream = open(os.path.join(directory, '.overviewer-render.lock'), 'a+b')
        try:
            self.stream.seek(0)
            if not self.stream.read(1):
                self.stream.write(b'0')
                self.stream.flush()
            self.stream.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                ref = weakref.ref(self.stream)
                def close_in_child():
                    stream = ref()
                    if stream is not None:
                        stream.close()
                os.register_at_fork(after_in_child=close_in_child)
        except OSError:
            self.stream.close()
            raise RuntimeError('Another Overviewer process is using this output directory')

    def close(self):
        self.stream.close()


def render_key(render, world, texture_files=()):
    """Config/code/assets invalidate the plan; ordinary world saves do not.

    A resumed plan keeps its original chunk watermark. Changes made after the
    scan therefore remain eligible for the next incremental update, including
    chunks outside the saved plan's bounds. A snapshot gives consistent output.
    """
    # POI filters are config-defined functions and are not pickleable. They do
    # not change raster tiles, so editing markers must not invalidate a plan.
    options = {k: v for k, v in render.items()
               if k not in ('changelist', 'renderchecks', 'markers', 'manualpois')}
    digest = hashlib.sha256(pickle.dumps(options, protocol=4))
    identity = (world.leveldat.get('RandomSeed'), world.leveldat.get('WorldGenSettings', {}).get('seed'))
    digest.update(repr(identity).encode())
    root = Path(__file__).parent
    for path in sorted(root.rglob('*')):
        if path.suffix in ('.py', '.c', '.h'):
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(path.read_bytes())
    paths = [Path(path) for path in texture_files]
    texturepath = render.get('texturepath')
    if texturepath:
        texturepath = Path(texturepath)
        paths.extend(texturepath.rglob('*') if texturepath.is_dir() else [texturepath])
    for path in sorted(set(paths)):
        stat = path.stat()
        digest.update(str((str(path.resolve()), stat.st_size, stat.st_mtime_ns)).encode())
    return digest.hexdigest()


class RenderJournal:
    def __init__(self, directory, slot=0):
        self.path = os.path.join(directory, '.overviewer-resume-%s.sqlite3' % slot)
        self.db = None
        self.uncommitted = 0
        self.last_commit = time.monotonic()

    def peek(self, key):
        if not os.path.isfile(self.path):
            return None
        with closing(sqlite3.connect(self.path)) as db:
            try:
                row = db.execute('SELECT value FROM metadata WHERE name="plan"').fetchone()
            except sqlite3.OperationalError:
                return None  # interrupted before publishing the first plan
        if row:
            meta = json.loads(row[0])
            if meta['key'] == key:
                return meta
        return None

    def connect(self):
        self.db = sqlite3.connect(self.path)
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('PRAGMA cache_size=-4096')

    def create(self, metadata, items):
        self.connect()
        # DDL and data belong to the same transaction. No partial plan is usable.
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS metadata (name TEXT PRIMARY KEY, value TEXT)')
            self.db.execute('CREATE TABLE IF NOT EXISTS jobs (sequence INTEGER PRIMARY KEY, path TEXT UNIQUE)')
            self.db.execute('DELETE FROM metadata')
            self.db.execute('DELETE FROM jobs')
            self.db.executemany('INSERT INTO jobs(path) VALUES (?)',
                                (("".join(map(str, path)),) for path, deps in items))
            metadata = dict(metadata, jobs_total=self.db.execute('SELECT count(*) FROM jobs').fetchone()[0])
            self.db.execute('INSERT INTO metadata VALUES (?, ?)', ('plan', json.dumps(metadata)))

    def pending(self):
        # Separate read connection: the write connection commits while iterating.
        # Keyset pagination avoids a long-lived read transaction blocking commits.
        last = 0
        while True:
            rows = self.db.execute('SELECT sequence,path FROM jobs WHERE sequence>? ORDER BY sequence LIMIT 512', (last,)).fetchall()
            if not rows:
                return
            for last, path in rows:
                tile = tuple(map(int, path))
                yield tile, [tile + (i,) for i in range(4)]

    def count(self):
        return self.db.execute('SELECT count(*) FROM jobs').fetchone()[0]

    def completed(self, tile):
        self.db.execute('DELETE FROM jobs WHERE path=?', ("".join(map(str, tile)),))
        self.uncommitted += 1
        if self.uncommitted >= 128 or time.monotonic() - self.last_commit >= 1:
            self.flush()

    def flush(self):
        self.db.commit()
        self.uncommitted = 0
        self.last_commit = time.monotonic()

    def close(self):
        if self.db is not None:
            self.flush()
            self.db.close()
            self.db = None

    def finish(self):
        if self.count():
            raise RuntimeError('Cannot finalize an unfinished render plan')
        self.close()
        os.unlink(self.path)
