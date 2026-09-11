#!/usr/bin/env python3
"""Download verified AppImage build tools into the supplied directory."""

import argparse
import hashlib
from pathlib import Path
from urllib.request import urlopen

ASSETS = (
    ('appimagetool',
     'https://github.com/AppImage/appimagetool/releases/download/1.9.1/appimagetool-x86_64.AppImage',
     'ed4ce84f0d9caff66f50bcca6ff6f35aae54ce8135408b3fa33abfc3cb384eb0'),
    # type2-runtime commit 75849dce7cc37e4319b633df1f116ca895c71a12.
    # Upstream replaces "continuous": fail on a new hash instead of silently updating.
    ('runtime-x86_64',
     'https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-x86_64',
     '1cc49bcf1e2ccd593c379adb17c9f85a36d619088296504de95b1d06215aebbf'),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    for name, url, expected in ASSETS:
        path = args.directory / name
        data = path.read_bytes() if path.exists() else urlopen(url, timeout=60).read()
        if hashlib.sha256(data).hexdigest() != expected:
            raise SystemExit(f'Checksum mismatch: {name}; review the upstream release before updating the pin')
        path.write_bytes(data)
        path.chmod(0o755)
        print(path)


if __name__ == '__main__':
    main()
