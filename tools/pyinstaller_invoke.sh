#!/usr/bin/env sh
set -eu
exec "$(dirname "$0")/../standalone-dist/ZenCad/ZenCad" "$@"
