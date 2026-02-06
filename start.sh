#!/bin/sh
# Start the API from the repo root (no install to /opt).
# Uses config.yaml in repo root. Creates venv and installs deps if missing.

set -e

cd "$(dirname "$0")"
ROOT="$(pwd)"

if [ ! -x "./venv/bin/python" ]; then
  echo "Creating venv and installing dependencies..."
  python3 -m venv ./venv
  ./venv/bin/pip install -q --upgrade pip
  ./venv/bin/pip install -q -r requirements.txt
fi
PYTHON="./venv/bin/python"

if [ ! -f "config.yaml" ]; then
  echo "Warning: config.yaml not found. Copy config.yaml.example to config.yaml and edit if needed."
fi

export PYTHONPATH="${ROOT}/src"
exec "$PYTHON" "${ROOT}/src/run_server.py"
