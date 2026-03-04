#!/bin/bash
set -euo pipefail

log() { echo "$(tput setaf 2)[ok]$(tput sgr0) $@"; }
SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd -P )"

cd "$SCRIPT_ROOT"
[ ! -e "$SCRIPT_ROOT/.venv" ] && log "Setup venv" && python3 -m venv --prompt venv .venv
[ ! -e "$SCRIPT_ROOT/.venv/bin/uv" ] && log "Install uv" && "$SCRIPT_ROOT/.venv/bin/pip" install uv
source "$SCRIPT_ROOT/.venv/bin/activate"

log "Install project as editable"
uv pip install -U --editable .[dev]
