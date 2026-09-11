#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
test "$(uname -m)" = x86_64 || { echo 'This builder targets Linux x86_64.' >&2; exit 1; }
docker build -f tools/standalone/Dockerfile -t zencad-standalone:ubuntu22.04 .
revision=$(git describe --always --dirty)
docker run --rm --user "$(id -u):$(id -g)" \
    -e PYINSTALLER_CONFIG_DIR=/tmp/pyinstaller \
    -e "ZENCAD_SOURCE_REVISION=$revision" -v "$PWD:/src" \
    zencad-standalone:ubuntu22.04 \
    sh -c 'sh tools/pyinstaller_make.sh && python tools/standalone/collect_notices.py'
python3 tools/standalone/fetch_appimage_tools.py build/appimage-tools
python3 tools/standalone/package_linux.py \
    --appimagetool build/appimage-tools/appimagetool \
    --runtime build/appimage-tools/runtime-x86_64
