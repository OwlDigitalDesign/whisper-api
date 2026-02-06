#!/bin/sh
# Install only missing system dependencies (Python 3.9+, ffmpeg, venv/pip).
# Idempotent: does nothing if all are present.
# Run with sudo or as root.

set -e

need_python=0
need_ffmpeg=0
need_venv=0
need_pip=0

# Check Python 3.9+
if ! command -v python3 >/dev/null 2>&1; then
  need_python=1
else
  if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
    need_python=1
  fi
fi

# Check ffmpeg
if ! command -v ffmpeg >/dev/null 2>&1; then
  need_ffmpeg=1
fi

# Check venv (required when Python present)
if [ "$need_python" -eq 0 ] && ! python3 -c 'import venv' 2>/dev/null; then
  need_venv=1
fi

# Check pip
if [ "$need_python" -eq 0 ] && ! python3 -m pip --version >/dev/null 2>&1; then
  need_pip=1
fi

# venv and pip are required (not optional): when Python is present, always ensure both are installed
if [ "$need_python" -eq 0 ]; then
  need_venv=1
  need_pip=1
fi

if [ "$need_python" -eq 0 ] && [ "$need_ffmpeg" -eq 0 ] && [ "$need_venv" -eq 0 ] && [ "$need_pip" -eq 0 ]; then
  echo "All dependencies satisfied."
  exit 0
fi

# Detect package manager and install only what's missing
if command -v apt-get >/dev/null 2>&1; then
  apt_get_install=""
  [ "$need_python" -eq 1 ] && apt_get_install="$apt_get_install python3 python3-pip"
  [ "$need_ffmpeg" -eq 1 ] && apt_get_install="$apt_get_install ffmpeg"
  [ "$need_venv" -eq 1 ] && apt_get_install="$apt_get_install python3-venv"
  [ "$need_pip" -eq 1 ] && apt_get_install="$apt_get_install python3-pip"
  if [ -n "$apt_get_install" ]; then
    apt-get update
    apt-get install -y $apt_get_install
  fi
elif command -v dnf >/dev/null 2>&1; then
  dnf_install=""
  [ "$need_python" -eq 1 ] && dnf_install="$dnf_install python3 python3-pip"
  [ "$need_ffmpeg" -eq 1 ] && dnf_install="$dnf_install ffmpeg"
  [ "$need_venv" -eq 1 ] && dnf_install="$dnf_install python3-virtualenv"
  [ "$need_pip" -eq 1 ] && dnf_install="$dnf_install python3-pip"
  if [ -n "$dnf_install" ]; then
    dnf install -y $dnf_install
  fi
elif command -v yum >/dev/null 2>&1; then
  yum_install=""
  [ "$need_python" -eq 1 ] && yum_install="$yum_install python3 python3-pip"
  [ "$need_ffmpeg" -eq 1 ] && yum_install="$yum_install ffmpeg"
  [ "$need_venv" -eq 1 ] && yum_install="$yum_install python3-virtualenv"
  [ "$need_pip" -eq 1 ] && yum_install="$yum_install python3-pip"
  if [ -n "$yum_install" ]; then
    yum install -y $yum_install
  fi
elif command -v apk >/dev/null 2>&1; then
  apk_add=""
  [ "$need_python" -eq 1 ] && apk_add="$apk_add python3 py3-pip"
  [ "$need_ffmpeg" -eq 1 ] && apk_add="$apk_add ffmpeg"
  [ "$need_venv" -eq 1 ] && apk_add="$apk_add python3-dev"  # venv usually included in python3
  [ "$need_pip" -eq 1 ] && apk_add="$apk_add py3-pip"
  if [ -n "$apk_add" ]; then
    apk add --no-cache $apk_add
  fi
elif command -v zypper >/dev/null 2>&1; then
  zypper_install=""
  [ "$need_python" -eq 1 ] && zypper_install="$zypper_install python3 python3-pip"
  [ "$need_ffmpeg" -eq 1 ] && zypper_install="$zypper_install ffmpeg"
  [ "$need_venv" -eq 1 ] && zypper_install="$zypper_install python3-virtualenv"
  [ "$need_pip" -eq 1 ] && zypper_install="$zypper_install python3-pip"
  if [ -n "$zypper_install" ]; then
    zypper install -y $zypper_install
  fi
else
  echo "Unknown package manager. Install manually: Python 3.9+, ffmpeg, python3-venv, python3-pip."
  exit 1
fi

echo "Dependencies installed."
