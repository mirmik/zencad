#!/usr/bin/env bash

set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
venv_directory="${project_root}/venv"
venv_python="${venv_directory}/bin/python"
skip_install=0

if [[ "${1:-}" == "--skip-install" ]]; then
    skip_install=1
    shift
fi

python_probe='import platform, struct, sys; raise SystemExit(0 if platform.python_implementation() == "CPython" and struct.calcsize("P") * 8 == 64 and (3, 10) <= sys.version_info[:2] < (3, 15) else 1)'

find_supported_python() {
    local candidate resolved
    local -a candidates=()

    if [[ -n "${ZENCAD_PYTHON:-}" ]]; then
        candidates+=("${ZENCAD_PYTHON}")
    fi
    candidates+=(python3.14 python3.13 python3.12 python3.11 python3.10 python3 python)

    for candidate in "${candidates[@]}"; do
        resolved="$(command -v -- "${candidate}" 2>/dev/null || true)"
        if [[ -n "${resolved}" ]] && "${resolved}" -c "${python_probe}" 2>/dev/null; then
            printf '%s\n' "${resolved}"
            return 0
        fi
    done

    return 1
}

base_python="$(find_supported_python || true)"
if [[ -z "${base_python}" ]]; then
    echo "ZenCad requires 64-bit CPython 3.10-3.14." >&2
    echo "Install a supported Python or set ZENCAD_PYTHON to its executable." >&2
    exit 1
fi

echo "Using $("${base_python}" --version 2>&1) at ${base_python}"

if [[ ! -e "${venv_python}" ]]; then
    if [[ -e "${venv_directory}" ]]; then
        echo "Existing '${venv_directory}' is not a valid Unix virtual environment." >&2
        exit 1
    fi
    echo "Creating virtual environment in '${venv_directory}'..."
    "${base_python}" -m venv "${venv_directory}"
elif ! "${venv_python}" -c "${python_probe}" 2>/dev/null; then
    echo "Existing '${venv_directory}' does not use supported 64-bit CPython 3.10-3.14." >&2
    exit 1
fi

if (( ! skip_install )); then
    echo "Installing ZenCad and its GUI dependencies..."
    "${venv_python}" -m pip install --upgrade pip
    "${venv_python}" -m pip install --editable "${project_root}[gui]"
fi

echo "Starting ZenCad..."
exec "${venv_python}" -m zencad "$@"
