#!/usr/bin/env python3
"""Test a Linux frozen executable outside the checkout (run under xvfb-run)."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('--extract-and-run', action='store_true')
    parser.add_argument('--headless', action='store_true')
    args = parser.parse_args()
    command = [str(args.executable.resolve())]
    if args.extract_and_run:
        command.append('--appimage-extract-and-run')
    with tempfile.TemporaryDirectory(prefix='zencad-frozen-') as temporary:
        root = Path(temporary)
        environment = os.environ.copy()
        for name in ('PYTHONPATH', 'PYTHONHOME'):
            environment.pop(name, None)
        environment.update(
            XDG_CONFIG_HOME=str(root / 'config'),
            ZENCAD_CACHE_DIR=str(root / 'cache'),
            QT_QPA_PLATFORM='xcb',
        )

        def run(*arguments, timeout=120):
            result = subprocess.run(command + list(arguments), cwd=root,
                                    env=environment, text=True, capture_output=True,
                                    timeout=timeout)
            assert result.returncode == 0, (arguments, result.stdout, result.stderr)
            return result.stdout

        model = root / 'моя модель.py'
        model.write_text('from zencad import *\ndisplay(box(10), name="cube")\nshow()\n')
        report = json.loads(run('inspect', str(model), '--json'))
        assert report['status'] == 'ok'
        assert report['scene']['object_count'] == 1
        assert abs(report['objects'][0]['geometry']['volume'] - 1000) < 1e-6
        run('check', str(model), '--valid')

        dependencies = root / 'dependencies.py'
        dependencies.write_text('''import sys
from pathlib import Path
import numpy as np
import zencad as z
import trimesh
from PIL import Image
from skimage import measure, io
assert sys.frozen
assert Path(z.__file__).is_relative_to(sys._MEIPASS)
examples = Path(z.exampledir)
assert len(list(examples.rglob('*.py'))) > 40
mesh = trimesh.load(examples / 'Integration/trimesh/bulbasaur.STL')
assert len(mesh.vertices) > 50
grid = np.zeros((5, 5, 5)); grid[1:4, 1:4, 1:4] = 1
vertices, faces, _, _ = measure.marching_cubes(grid, 0.5)
assert len(vertices) > 0 and len(faces) > 0
Image.new('RGB', (8, 8), 'red').save('pillow.png')
assert io.imread('pillow.png').shape == (8, 8, 3)
assert list((examples / 'fonts').glob('*.ttf'))
print('Frozen dependencies and resources: OK')
''')
        print(run('--no-show', str(dependencies)).strip())
        if not args.headless:
            preview = root / 'render.png'
            run('render', str(model), '-o', str(preview), '--size', '320x240',
                '--yaw', '35', '--pitch', '25', '--msaa', '4')
            data = preview.read_bytes()
            assert data[:8] == b'\x89PNG\r\n\x1a\n' and len(data) > 1000
            tests = Path(__file__).resolve().parent
            for name, flag in (('gui_reload_smoke.py', '--no-show'),
                               ('gui_standalone_smoke.py', '--display')):
                script = root / name
                shutil.copyfile(tests / name, script)
                print(run(flag, str(script)).strip())
        print('Frozen executable smoke: OK')


if __name__ == '__main__':
    main()
