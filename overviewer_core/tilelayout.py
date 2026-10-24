"""Recoverable directory moves when the map's quadtree changes depth.

The next operation is persisted before a move. Moves are idempotent when the
source is absent and the destination exists, covering a kill between rename
and recording its completion. Discarded subtrees are removed only after the
new layout is committed.
"""
import json
import os
from pathlib import Path
import shutil
import time

from .files import FileReplacer


class TileLayout:
    def __init__(self, directory, initial_depth, extension):
        self.root = Path(directory).resolve()
        self.path = self.root / '.overviewer-layout.json'
        self.extension = extension
        if self.path.exists():
            self.state = json.loads(self.path.read_text(encoding='utf-8'))
        else:
            self.state = dict(depth=initial_depth, pending=None, garbage=[])

    @property
    def depth(self):
        return self.state['depth']

    def save(self):
        with FileReplacer(str(self.path)) as temporary:
            Path(temporary).write_text(json.dumps(self.state), encoding='utf-8')

    def child(self, relative):
        path = self.root / relative
        if Path(relative).is_absolute() or self.root not in path.resolve().parents:
            raise ValueError('Invalid tile layout path: ' + str(relative))
        return path

    def sync_directories(self, *paths):
        if os.name == 'posix':
            for path in set(paths):
                fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)

    def operation(self, operation):
        action, *arguments = operation
        if action == 'mkdir':
            self.child(arguments[0]).mkdir(exist_ok=True)
        elif action == 'move':
            source, destination = map(self.child, arguments)
            if source.exists():
                if destination.exists():
                    raise RuntimeError('Both sides of a layout move exist: %s -> %s' % (source,destination))
                for attempt in range(6):
                    try:
                        os.rename(source, destination)
                        break
                    except PermissionError:
                        # Windows antivirus/cloud sync can briefly open directories
                        # without FILE_SHARE_DELETE. Keep the operation journaled.
                        if os.name != 'nt' or attempt == 5:
                            raise
                        time.sleep(0.05 * 2**attempt)
                self.sync_directories(source.parent, destination.parent)
            # Both absent means an optional old tile/subtree did not exist.
        elif action == 'unlink':
            self.child(arguments[0]).unlink(missing_ok=True)
        else:
            raise ValueError('Unknown layout operation: ' + str(action))

    def recover(self):
        pending = self.state.get('pending')
        if pending:
            operations = pending['operations']
            while pending['next'] < len(operations):
                self.operation(operations[pending['next']])
                pending['next'] += 1
                self.save()
            self.state['depth'] = pending['target']
            self.state['pending'] = None
            self.save()
        for name in self.state.get('garbage', []):
            path = self.child(name)
            # Verify each recursive delete is a direct, named staging child of
            # this output directory. Never follow a substituted symlink.
            allowed = {'.overviewer-layout-trash-' + str(q) for q in range(4)}
            if path.parent.resolve() != self.root or path.name not in allowed:
                raise ValueError('Invalid layout cleanup path')
            if path.is_symlink():
                path.unlink()
            elif path.exists():
                shutil.rmtree(path)
        if self.state.get('garbage'):
            self.state['garbage'] = []
            self.save()

    def resize(self, target):
        self.recover()
        while self.depth != target:
            grow = target > self.depth
            new_depth = self.depth + (1 if grow else -1)
            operations, garbage = [], []
            for quadrant in range(4):
                q, opposite = str(quadrant), str(3-quadrant)
                stage = '.overviewer-layout-stage-' + q
                image = q + '.' + self.extension
                if grow:
                    operations.extend([['mkdir',stage],
                                       ['move',image,stage+'/'+opposite+'.'+self.extension],
                                       ['move',q,stage+'/'+opposite],
                                       ['move',stage,q]])
                else:
                    trash = '.overviewer-layout-trash-' + q
                    garbage.append(trash)
                    operations.extend([['move',q+'/'+opposite,stage],
                                       ['move',q,trash],
                                       ['move',stage,q], ['unlink',image]])
            operations.append(['unlink','base.'+self.extension])
            self.state['pending'] = dict(target=new_depth, next=0, operations=operations)
            self.state['garbage'] = garbage
            self.save()
            self.recover()
