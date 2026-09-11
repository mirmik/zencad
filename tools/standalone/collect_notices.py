#!/usr/bin/env python3
"""Record the frozen build and preserve notices from its build environment."""

import ast
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess


def main():
    root = Path(__file__).resolve().parents[2]
    bundle = root / 'standalone-dist/ZenCad'
    version = metadata.version('zencad')
    (bundle / 'VERSION').write_text(version + '\n')
    (bundle / 'build-info.json').write_text(json.dumps({
        'version': version,
        'source_revision': os.environ.get('ZENCAD_SOURCE_REVISION', 'unknown'),
        'python': platform.python_version(),
        'platform': platform.platform(),
        'os_release': Path('/etc/os-release').read_text(),
        'distributions': {d.metadata['Name']: d.version for d in metadata.distributions()},
    }, indent=2) + '\n')
    shutil.copyfile(root / 'LICENSE.txt', bundle / 'LICENSE.txt')
    shutil.copyfile(root / 'tools/standalone/README.md', bundle / 'README.md')
    notices = bundle / 'licenses'
    notices.mkdir(exist_ok=True)
    shutil.copytree('/usr/share/common-licenses', notices / 'common', dirs_exist_ok=True)
    # Match only the system binaries actually copied by PyInstaller.
    entries = ast.literal_eval((root / 'build/standalone/__main__/COLLECT-00.toc').read_text())[0]
    packages = set()
    for _, source, kind in entries:
        if kind not in ('BINARY', 'EXTENSION') or not source.startswith(('/lib/', '/usr/lib/')):
            continue
        result = subprocess.run(['dpkg-query', '-S', source], text=True, capture_output=True)
        for line in result.stdout.splitlines():
            package, separator, _ = line.rpartition(': ')
            if separator:
                packages.add(package)
    system = {}
    for package in sorted(packages):
        copyright_file = Path('/usr/share/doc') / package.split(':')[0] / 'copyright'
        if copyright_file.exists():
            shutil.copyfile(copyright_file, notices / f'{package}.copyright')
        system[package] = subprocess.check_output(
            ['dpkg-query', '-W', '-f=${Version}', package], text=True,
        )
    (notices / 'system-packages.json').write_text(json.dumps(system, indent=2) + '\n')
    shutil.copytree(root / 'tools/standalone/licenses', notices / 'upstream', dirs_exist_ok=True)
    freezer = metadata.distribution('pyinstaller')
    for file in freezer.files or ():
        if 'licenses' in file.parts:
            destination = notices / 'PyInstaller' / file.name
            destination.parent.mkdir(exist_ok=True)
            shutil.copyfile(freezer.locate_file(file), destination)


if __name__ == '__main__':
    main()
