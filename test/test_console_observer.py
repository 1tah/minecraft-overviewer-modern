"""Select a line logger when pool resize messages share a terminal."""
from types import SimpleNamespace
import os
import pytest
from overviewer_core import settingsDefinition as settings
from overviewer_core.observer import LoggingObserver


@pytest.mark.parametrize('flags,tty,platform,lines', [
    ([], True, 'Linux', False),
    (['--fixed-resources'], True, 'Linux', False),
    (['--auto-resources'], True, 'Linux', True),
    (['--simple'], True, 'Linux', True),
    (['--simple-output'], True, 'Linux', True),
    ([], False, 'Linux', True),
    ([], True, 'Windows', True),
])
def test_default_console_observer(flags, tty, platform, lines, monkeypatch):
    bar = object()
    monkeypatch.setattr(settings.sys, 'argv', ['overviewer.py', *flags])
    monkeypatch.setattr(settings.sys, 'stdout', SimpleNamespace(isatty=lambda: tty))
    monkeypatch.setattr(settings.platform, 'system', lambda: platform)
    monkeypatch.setattr(settings, 'ProgressBarObserver', lambda **kwargs: bar)
    observer = settings.get_default_config()['observer'].default
    assert isinstance(observer, LoggingObserver) if lines else observer is bar


def test_line_output_preserves_speed_and_fractional_progress(monkeypatch, caplog):
    import logging
    from overviewer_core import observer as module
    clock = [1000.0]
    monkeypatch.setattr(module.time, 'time', lambda: clock[0])
    caplog.set_level(logging.INFO)
    observer = LoggingObserver()
    observer.start(1499381)
    clock[0] += 60
    observer.update(104)
    message = caplog.records[-1].getMessage()
    assert 'Rendered 104 of 1499381' in message
    assert '0.01% complete' in message
    assert '1.73 t/s' in message
    assert '\r' not in message


@pytest.mark.skipif(os.name != 'posix', reason='POSIX pseudo-terminal')
def test_auto_console_does_not_interleave_carriage_return_bar():
    import errno, pty, subprocess, sys
    master, slave = pty.openpty()
    program = '''
import logging,sys
from overviewer_core import logger,settingsDefinition
sys.argv=['overviewer.py','--auto-resources']
logger.configure(simple=True)
observer=settingsDefinition.get_default_config()['observer'].default
observer.start(100)
observer.update(50)
logging.info('Auto resources: start; workers=2/10')
observer.finish()
'''
    try:
        process = subprocess.Popen([sys.executable, '-c', program], stdout=slave, stderr=slave)
        os.close(slave)
        slave = None
        output = b''
        while True:
            try:
                chunk = os.read(master, 65536)
                if not chunk: break
                output += chunk
            except OSError as error:
                if error.errno == errno.EIO: break
                raise
        assert process.wait(timeout=10) == 0, output
        assert b'Auto resources: start; workers=2/10' in output
        assert b'100.00% complete' in output
        assert b'\r' not in output.replace(b'\r\n', b'\n')
    finally:
        os.close(master)
        if slave is not None: os.close(slave)
