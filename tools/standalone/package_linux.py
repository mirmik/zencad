#!/usr/bin/env python3
"""Package an existing PyInstaller directory as tar.gz and AppImage."""

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tarfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--appimagetool', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    output = root / 'standalone-dist'
    bundle = output / 'ZenCad'
    version = (bundle / 'VERSION').read_text().strip()
    name = f'ZenCad-{version}-linux-x86_64'
    appdir = root / 'build/standalone/ZenCad.AppDir'
    if appdir.exists():
        shutil.rmtree(appdir)
    shutil.copytree(bundle, appdir / 'usr/lib/zencad', symlinks=True)
    shutil.copyfile(root / 'zencad/zencad_logo.png', appdir / 'zencad.png')
    (appdir / '.DirIcon').symlink_to('zencad.png')
    (appdir / 'zencad.desktop').write_text(
        '[Desktop Entry]\nType=Application\nName=ZenCad\n'
        'Comment=Scriptable CAD\nExec=ZenCad %f\nIcon=zencad\n'
        'Terminal=false\nCategories=Graphics;3DGraphics;Engineering;\n'
    )
    launcher = appdir / 'AppRun'
    launcher.write_text(
        '#!/bin/sh\nset -eu\n'
        'app_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\n'
        'exec "$app_root/usr/lib/zencad/ZenCad" "$@"\n'
    )
    launcher.chmod(0o755)
    # A desktop launcher should also resolve its Exec entry inside the AppDir.
    (appdir / 'usr/bin').mkdir()
    (appdir / 'usr/bin/ZenCad').symlink_to('../lib/zencad/ZenCad')
    appimage = output / f'{name}.AppImage'
    subprocess.run([
        str(args.appimagetool.resolve()), '--appimage-extract-and-run',
        '--runtime-file', str(args.runtime.resolve()), '--no-appstream',
        str(appdir), str(appimage),
    ], check=True, env={**os.environ, 'ARCH': 'x86_64', 'VERSION': version})
    archive = output / f'{name}.tar.gz'
    with tarfile.open(archive, 'w:gz', compresslevel=6) as tar:
        tar.add(bundle, arcname='ZenCad')
    with (output / 'SHA256SUMS').open('w') as checksums:
        for artifact in (appimage, archive):
            digest = hashlib.sha256()
            with artifact.open('rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(block)
            checksums.write(f'{digest.hexdigest()}  {artifact.name}\n')
            print(artifact)


if __name__ == '__main__':
    main()
