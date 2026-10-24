"""Publish the OOM result as the original user, after all workers stopped."""
import argparse
import json
from pathlib import Path
import sys
import time

from overviewer_core.config_parser import MultiWorldParser
from overviewer_core.files import FileReplacer

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-c', '--config', default='configNew.py')
arguments, _ = parser.parse_known_args()
try:
    config = MultiWorldParser()
    config.parse(arguments.config)
    output = Path(config.get_validated_config()['outputdir'])/'render-progress.json'
    if output.exists():
        data = json.loads(output.read_text(encoding='utf-8'))
        data.update(status='error', phase='Остановлен: достигнут лимит RAM; уменьшите -p',
                    message='Остановлен: достигнут лимит RAM; уменьшите -p',
                    updated_at=time.time(), sequence=data.get('sequence', 0)+1)
        with FileReplacer(str(output)) as temporary:
            Path(temporary).write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
except Exception as error:
    print('Could not update web status after OOM:', error, file=sys.stderr)
