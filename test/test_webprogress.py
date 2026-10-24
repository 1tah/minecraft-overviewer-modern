import json
from types import SimpleNamespace

import pytest

from overviewer_core.renderjournal import RenderJournal
from overviewer_core.webprogress import WebProgress, manage_lifecycle, register


def tileset(directory, name, pending=4, total=10):
    directory.mkdir()
    journal = RenderJournal(str(directory))
    journal.create({'key': name}, [((i,), []) for i in range(total)])
    for i in range(total-pending):
        journal.completed((i,))
    journal.flush()
    return SimpleNamespace(journal=journal, options=dict(name=name, worldname_orig=name,
        title=name, resume_key=name, renderchecks=0),
        get_num_phases=lambda: 1, get_phase_length=lambda p: pending)


def test_resume_progress_preserves_original_total_and_separate_worlds(tmp_path):
    a = tileset(tmp_path/'a', 'Nether')
    b = tileset(tmp_path/'b', 'End', pending=2, total=2)
    progress = WebProgress(tmp_path/'output', heartbeat=False)
    try:
        assert 'location.reload' in (tmp_path/'output/index.html').read_text(encoding='utf-8')
        progress.begin([a, b])
        snapshot = json.loads(progress.path.read_text(encoding='utf-8'))
        assert (snapshot['total'], snapshot['done'], snapshot['remaining']) == (12, 6, 6)
        assert snapshot['renders'][0]['initial_done'] == 6
        assert snapshot['renders'][0]['eta_seconds'] is None
        progress.completed(a)
        assert progress.snapshot()['renders'][0]['done'] == 7
        assert progress.snapshot()['renders'][1]['done'] == 0
        assert progress.snapshot()['eta_seconds'] >= 0
        progress.stop('interrupted')
        assert json.loads(progress.path.read_text(encoding='utf-8'))['status'] == 'interrupted'
    finally:
        progress.close()
        a.journal.close()
        b.journal.close()


@pytest.mark.parametrize('exception,state', [(KeyboardInterrupt, 'interrupted'), (RuntimeError, 'error')])
def test_lifecycle_reports_failure_and_stops_heartbeat(tmp_path, exception, state):
    @manage_lifecycle
    def run():
        progress = WebProgress(tmp_path, interval=0.02)
        register(progress)
        raise exception()
    with pytest.raises(exception):
        run()
    snapshot = json.loads((tmp_path/'render-progress.json').read_text(encoding='utf-8'))
    assert snapshot['status'] == state
    assert not snapshot['config_ready']


def test_empty_render_and_existing_index(tmp_path):
    (tmp_path/'index.html').write_text('existing map', encoding='utf-8')
    progress = WebProgress(tmp_path, heartbeat=False)
    try:
        assert (tmp_path/'index.html').read_text() == 'existing map'
        progress.begin([])
        progress.stop('complete')
        data = json.loads(progress.path.read_text(encoding='utf-8'))
        assert data['percent'] == 100
        assert data['remaining'] == 0
        assert data['status'] == 'complete'
    finally:
        progress.close()
