#!/bin/bash

set -euo pipefail
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/.. >/dev/null 2>&1 && pwd -P )"
source "$PROJECT_ROOT/scripts/activate-venv.sh"

set -e  # activate-venv  sets +e
exec "$@"
