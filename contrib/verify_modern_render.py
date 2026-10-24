"""Offline smoke test. Supply your own official client JAR; no game assets ship here.

python contrib/verify_modern_render.py /path/26.3.jar /tmp/ov-check
Then use the printed commands to exercise normal and interrupted rendering.
"""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test.modern_fixture import make_world


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('jar')
    parser.add_argument('directory')
    parser.add_argument('--crash-after', type=int, default=0,
                        help='Test only: exit after N confirmed tiles. Reuse existing fixture/config.')
    args = parser.parse_args()
    root = Path(args.directory).resolve()
    config = root/'map.py'
    if not args.crash_after:
        version = make_world(root/'world', args.jar)
        config.write_text("worlds['fixture'] = %r\noutputdir = %r\nrenders['map'] = "
                          "{'world':'fixture','dimension':'overworld','title':'Modern blocks','rendermode':'normal','texturepath':%r}\n"
                          % (str(root/'world'),str(root/'output'),str(Path(args.jar).resolve())), encoding='utf-8')
        print('Fixture:', version['id'], 'DataVersion:',version['world_version'])
        print('Render/resume: python overviewer.py -c "%s" -p 1' % config)
        return
    import os
    import overviewer
    from overviewer_core.tileset import TileSet
    original = TileSet.work_completed
    count = 0
    def confirmed(self, tile):
        nonlocal count
        original(self, tile)
        self.journal.flush()
        count += 1
        if count >= args.crash_after:
            os._exit(23)
    TileSet.work_completed = confirmed
    sys.argv = ['overviewer.py','-c',str(config),'-p','1']
    raise SystemExit(overviewer.main())


if __name__ == '__main__':
    main()
