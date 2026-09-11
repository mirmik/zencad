#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python -m PyInstaller --noconfirm --clean \
    --workpath build/standalone --distpath standalone-dist __main__.spec
