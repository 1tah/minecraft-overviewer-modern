from pathlib import Path
from unittest.mock import patch

import pytest

from overviewer_core.tilelayout import TileLayout


class SimulatedKill(BaseException):
    pass


def seed_tree(root):
    root.mkdir(parents=True)
    for q in range(4):
        (root/str(q)).mkdir()
        (root/str(q)/'leaf.png').write_bytes(('leaf-%d' % q).encode())
        (root/('%d.png' % q)).write_bytes(('quad-%d' % q).encode())
    (root/'base.png').write_bytes(b'old-base')


@pytest.mark.parametrize('crash_at', range(1,20))
def test_growing_tree_recovers_after_each_move(tmp_path, crash_at):
    root = tmp_path/'map'
    seed_tree(root)
    layout = TileLayout(root, 5, 'png')
    original = layout.save
    calls = 0
    def interrupted_save():
        nonlocal calls
        calls += 1
        if calls == crash_at:
            raise SimulatedKill()
        original()
    with patch.object(layout, 'save', side_effect=interrupted_save):
        try:
            layout.resize(6)
        except SimulatedKill:
            pass
    recovered = TileLayout(root, 5, 'png')
    recovered.resize(6)
    assert recovered.depth == 6
    for q in range(4):
        assert (root/str(q)/str(3-q)/'leaf.png').read_bytes() == ('leaf-%d' % q).encode()
        assert (root/str(q)/('%d.png' % (3-q))).read_bytes() == ('quad-%d' % q).encode()
    assert not list(root.glob('.overviewer-layout-stage-*'))


@pytest.mark.parametrize('crash_at', range(1,21))
def test_shrinking_tree_recovers_before_deleting_old_subtrees(tmp_path, crash_at):
    root = tmp_path/'map'
    seed_tree(root)
    TileLayout(root, 5, 'png').resize(6)
    # Extra discarded branches exercise cleanup without touching wanted leaves.
    for q in range(4):
        (root/str(q)/'discarded').mkdir()
        (root/str(q)/'discarded'/'old.png').write_bytes(b'obsolete')
    layout = TileLayout(root, 6, 'png')
    original = layout.save
    calls = 0
    def interrupted_save():
        nonlocal calls
        calls += 1
        if calls == crash_at:
            raise SimulatedKill()
        original()
    with patch.object(layout, 'save', side_effect=interrupted_save):
        try:
            layout.resize(5)
        except SimulatedKill:
            pass
    recovered = TileLayout(root, 6, 'png')
    recovered.resize(5)
    assert recovered.depth == 5
    for q in range(4):
        assert (root/str(q)/'leaf.png').read_bytes() == ('leaf-%d' % q).encode()
    assert not list(root.glob('.overviewer-layout-stage-*'))
    assert not list(root.glob('.overviewer-layout-trash-*'))


def test_layout_cannot_escape_output_directory(tmp_path):
    layout = TileLayout(tmp_path, 5, 'png')
    with pytest.raises(ValueError):
        layout.child('../other-map')
