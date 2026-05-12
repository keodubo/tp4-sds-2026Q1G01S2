#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export RESUME="${RESUME:-1}"
export PACKAGE_OUTPUTS="${PACKAGE_OUTPUTS:-0}"

exec bash "${SCRIPT_DIR}/local_run_outputs.sh"
