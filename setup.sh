#!/bin/sh
# Install whisper-api to /opt/whisper-api: user, dirs, copy files, venv, systemd.
# Run with sudo from repo root.
# Optional: copy config.yaml.example to config.production.yaml, edit it, then run setup;
# setup copies config.production.yaml to /etc/whisper-api/config.yaml if present.

set -e

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="/opt/whisper-api"
VAR_LIB="/var/lib/whisper"
ETC_DIR="/etc/whisper-api"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run with sudo or as root."
  exit 1
fi

# Optional: install system deps first
if [ -x "${REPO_ROOT}/install-deps.sh" ]; then
  "${REPO_ROOT}/install-deps.sh" || true
fi

# Python 3.9+ check
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
  echo "Python 3.9+ required. Run install-deps.sh or install python3."
  exit 1
fi

# Create user
if ! getent passwd whisper >/dev/null 2>&1; then
  useradd --system --no-create-home --shell /usr/sbin/nologin whisper
fi

# Create dirs
mkdir -p "$INSTALL_DIR" "$VAR_LIB" "$ETC_DIR"
mkdir -p "${VAR_LIB}/tmp"
chown whisper:whisper "$VAR_LIB" "${VAR_LIB}/tmp" 2>/dev/null || true

# Copy src contents to /opt/whisper-api
for f in "${REPO_ROOT}/src/"*.py; do
  [ -f "$f" ] && cp "$f" "$INSTALL_DIR/"
done
cp "${REPO_ROOT}/requirements.txt" "$INSTALL_DIR/"
cp "${REPO_ROOT}/config.yaml.example" "$INSTALL_DIR/"

# Copy systemd unit
cp "${REPO_ROOT}/whisper-api.service" /etc/systemd/system/
systemctl daemon-reload

# Production config: use config.production.yaml if present, else copy example to /etc
if [ -f "${REPO_ROOT}/config.production.yaml" ]; then
  cp "${REPO_ROOT}/config.production.yaml" "${ETC_DIR}/config.yaml"
  chown whisper:whisper "${ETC_DIR}/config.yaml" 2>/dev/null || true
else
  if [ ! -f "${ETC_DIR}/config.yaml" ]; then
    cp "${REPO_ROOT}/config.yaml.example" "${ETC_DIR}/config.yaml"
    chown whisper:whisper "${ETC_DIR}/config.yaml" 2>/dev/null || true
  fi
  echo "Tip: copy config.yaml.example to config.production.yaml, edit it, then re-run setup to use it."
fi

# Venv and pip install
if [ ! -d "${INSTALL_DIR}/venv" ]; then
  python3 -m venv "${INSTALL_DIR}/venv"
fi
"${INSTALL_DIR}/venv/bin/pip" install -q --upgrade pip
"${INSTALL_DIR}/venv/bin/pip" install -q -r "${INSTALL_DIR}/requirements.txt"

# Ownership
chown -R whisper:whisper "$INSTALL_DIR"

echo "Installation complete. Enable and start the service:"
echo "  sudo systemctl enable --now whisper-api.service"
echo "  sudo systemctl status whisper-api.service"
