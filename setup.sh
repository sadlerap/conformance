#!/usr/bin/env bash

set -e

OUTPUT_DIR=test-output
if [ $# -ge 2 ]; then
    OUTPUT_DIR=$1
fi
[ -d "${OUTPUT_DIR}" ] || mkdir -p "${OUTPUT_DIR}"
echo "${OUTPUT_DIR}" > test-tmp-dir

PYTHON_VENV_DIR="${OUTPUT_DIR}/venv"

python3 -m venv "${PYTHON_VENV_DIR}"

"${PYTHON_VENV_DIR}"/bin/pip install --upgrade wheel setuptools pip -r features/requirements.txt
