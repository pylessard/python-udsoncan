#!/bin/bash
set -euo pipefail

COVERAGE_SUFFIX="${COVERAGE_SUFFIX:-dev}"
HTML_COVDIR="htmlcov_${COVERAGE_SUFFIX}"
COV_DATAFILE=".coverage_${COVERAGE_SUFFIX}"

if ! [[ -z "${BUILD_CONTEXT+x}" ]]; then
    if [[ "$BUILD_CONTEXT" == "ci" ]]; then
        if ! [[ -z "${NODE_NAME+x}" ]]; then
            echo "Running tests on agent: ${NODE_NAME}"
        fi
    fi
fi

set -x 

python3 -m coverage run --data-file ${COV_DATAFILE} -m unittest -v
python3 -m mypy udsoncan --strict
python3 -m coverage report --data-file ${COV_DATAFILE}
python3 -m coverage html --data-file ${COV_DATAFILE} -d $HTML_COVDIR
  