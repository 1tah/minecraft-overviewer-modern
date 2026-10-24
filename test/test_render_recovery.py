import os
from pathlib import Path
import pickle
import sqlite3
import subprocess
import sys
from unittest.mock import patch

import pytest

from overviewer_core.files import FileReplacer
from overviewer_core.memorylimit import run_limited
from overviewer_core.memorylimit import verify_scope
from overviewer_core.renderjournal import OutputLock, RenderJournal
from overviewer_core.renderjournal import render_key
from overviewer_core.tileset import TileSet
from test.test_tileset import FakeRegionset, FakeAssetmanager, chunks


def test_manual_markers_do_not_break_or_invalidate_raster_resume():
    from types import SimpleNamespace
    world = SimpleNamespace(leveldat={'RandomSeed': 42})
    base = {'world': 'main', 'rendermode': 'normal'}
    decorated = dict(base, markers=[{'filterFunction': lambda poi: poi.get('name')}],
                     manualpois=[{'id': 'manual', 'x': 1, 'y': 64, 'z': 2}])
    assert render_key(base, world) == render_key(decorated, world)


def test_resume_does_not_rescan_or_repeat_completed_tiles(tmp_path):
    options = dict(name='test', bgcolor='#000000', imgformat='png', optimizeimg=0,
                   rendermode='normal', rerenderprob=0, renderchecks=2, resume_key='same-inputs')
    regions = FakeRegionset(chunks)
    first = TileSet(None, regions, FakeAssetmanager(0), None, options.copy(), str(tmp_path))
    first.do_preprocessing()
    all_jobs = list(first.iterate_work_items(0))
    completed = [path for path, deps in all_jobs[:5]]
    for path in completed:
        first.work_completed(path)
    first.journal.close()
    with patch.object(TileSet, '_set_map_size', side_effect=AssertionError('range scan')), \
         patch.object(TileSet, '_chunk_scan', side_effect=AssertionError('chunk scan')):
        resumed = TileSet(None, regions, FakeAssetmanager(0), None, options.copy(), str(tmp_path))
        resumed.do_preprocessing()
    pending = list(resumed.iterate_work_items(0))
    assert [p for p, _ in pending] == [p for p, _ in all_jobs[5:]]
    assert resumed.max_chunk_mtime == first.max_chunk_mtime
    assert resumed.journal.peek('changed-inputs') is None
    for path, deps in pending:
        resumed.work_completed(path)
    resumed.finish_journal()
    assert not Path(resumed.journal.path).exists()


def test_hard_exit_rolls_back_only_uncommitted_completions(tmp_path):
    journal = RenderJournal(str(tmp_path))
    journal.create(dict(key='key', depth=2, max_chunk_mtime=1),
                   [((0,0), []), ((0,1), []), ((0,), []), ((), [])])
    journal.close()
    code = '''
import os,sys
from overviewer_core.renderjournal import RenderJournal
j=RenderJournal(sys.argv[1]); j.connect()
j.completed((0,0)); j.flush()
j.completed((0,1)); os._exit(17)
'''
    result = subprocess.run([sys.executable, '-c', code, str(tmp_path)])
    assert result.returncode == 17
    journal.connect()
    assert [p for p, deps in journal.pending()] == [(0,1), (0,), ()]
    journal.close()


def test_failed_tile_write_preserves_old_image_even_on_windows(tmp_path):
    target = tmp_path / 'tile.png'
    target.write_bytes(b'old-image')
    with pytest.raises(RuntimeError):
        with FileReplacer(str(target), {'rename_works':False}) as temporary:
            Path(temporary).write_bytes(b'truncated-new-image')
            raise RuntimeError('interrupted')
    assert target.read_bytes() == b'old-image'
    with FileReplacer(str(target), {'rename_works':False}) as temporary:
        Path(temporary).write_bytes(b'complete-new-image')
    assert target.read_bytes() == b'complete-new-image'
    assert not list(tmp_path.glob('*.tmp'))


def test_output_lock_excludes_another_coordinator(tmp_path):
    first = OutputLock(str(tmp_path))
    try:
        with pytest.raises(RuntimeError):
            OutputLock(str(tmp_path))
    finally:
        first.close()
    second = OutputLock(str(tmp_path))
    second.close()


def test_memory_limit_applies_to_entire_process_tree():
    with patch('sys.platform', 'linux'), patch('shutil.which', return_value='/bin/systemd-run'), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('subprocess.call', return_value=0) as call:
        assert run_limited('8G', ['overviewer.py','--memory-limit','8G','-p','4','-c','map.py']) == 0
        command = call.call_args.args[0]
        assert '--property=MemoryMax=8G' in command
        assert '--property=MemorySwapMax=0' in command
        assert command[-7:-2] == ['overviewer.py','-p','4','-c','map.py']
        assert command[-2:] == ['--verify-memory-limit', str(8*1024**3)]
        assert '--memory-limit' not in command
    with pytest.raises(ValueError):
        run_limited('0', ['overviewer.py'])


def test_memory_scope_must_be_enforced_by_kernel():
    with patch('pathlib.Path.read_text', side_effect=['0::/user.slice/test.scope\n', '8589934592\n', '0\n']):
        verify_scope(8*1024**3)
    with patch('pathlib.Path.read_text', side_effect=['0::/user.slice/test.scope\n', 'max\n', '0\n']):
        with pytest.raises(RuntimeError):
            verify_scope(8*1024**3)


def test_no_changed_chunks_cannot_reset_incremental_watermark(tmp_path):
    regions = FakeRegionset({})
    options = dict(name='test', bgcolor='#000000', imgformat='png', optimizeimg=0,
                   rendermode='normal', rerenderprob=0, renderchecks=0)
    ts = TileSet(None, regions, FakeAssetmanager(0), None, options, str(tmp_path))
    ts.last_rendertime = 123456
    ts._chunk_scan()
    assert ts.max_chunk_mtime == 123456


def test_dead_worker_fails_instead_of_waiting_forever():
    from types import SimpleNamespace
    from overviewer_core.dispatcher import MultiprocessingDispatcher
    dispatcher = object.__new__(MultiprocessingDispatcher)
    dispatcher.pool = [SimpleNamespace(pid=100,exitcode=-9)]
    with pytest.raises(RuntimeError, match='exited unexpectedly'):
        dispatcher._handle_messages()


def test_plan_creation_does_not_write_changelist_but_dispatch_iteration_does(tmp_path):
    with (tmp_path/'changes.txt').open('w+', encoding='utf-8') as changes:
        options = dict(name='test', bgcolor='#000000', imgformat='png', optimizeimg=0,
                       rendermode='normal', rerenderprob=0, renderchecks=2,
                       resume_key='key', changelist=changes.fileno())
        ts = TileSet(None, FakeRegionset(chunks), FakeAssetmanager(0), None, options, str(tmp_path))
        try:
            ts.do_preprocessing()
            assert (tmp_path/'changes.txt').read_text(encoding='utf-8') == ''
            pending = list(ts.iterate_work_items(0))
            lines = (tmp_path/'changes.txt').read_text(encoding='utf-8').splitlines()
            assert len(lines) == len(pending)
            assert str(tmp_path/'base.png') in lines
        finally:
            ts.journal.close()


def test_ordinary_world_saves_keep_resume_key_but_asset_changes_do_not(tmp_path):
    from types import SimpleNamespace
    from overviewer_core.renderjournal import render_key
    texture = tmp_path/'client.jar'
    texture.write_bytes(b'client-assets')
    config = dict(world='world-path', texturepath=str(texture))
    world = SimpleNamespace(leveldat={'RandomSeed':123, 'LastPlayed':100})
    initial = render_key(config, world)
    world.leveldat['LastPlayed'] = 200
    assert render_key(config, world) == initial
    texture.write_bytes(b'changed-client-assets')
    assert render_key(config, world) != initial


def test_invisible_legacy_sentinels_do_not_overflow_modern_numpy():
    from overviewer_core.world import RegionSet
    region = RegionSet('overviewer_core', 'region')
    for name in ('barrier','light','moving_piston','structure_void'):
        assert region._get_block({'Name':'minecraft:'+name}) == (0,0)
