#!/usr/bin/env bash

set -euo pipefail

# if we got sourced in a non-Bash shell, restart under Bash
if [ -z "$BASH_VERSION" ]; then
  exec bash "$0" "$@"
fi


# ─────────────────────────────────────────────────────────────
# Resolve absolute paths
# ─────────────────────────────────────────────────────────────
THIS_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$THIS_SCRIPT/.." && pwd)"
RUST_SCRIPT="$THIS_SCRIPT/reinstall_rust_server.sh"

# ─────────────────────────────────────────────────────────────
# Parse args: <optional-prefix> [--dev-core]
# ─────────────────────────────────────────────────────────────
DEV_CORE=false
PREFIX_FILTER=""

echo "🔍 Raw arguments: $*"

for arg in "$@"; do
  if [[ "$arg" == "--dev-core" ]]; then
    DEV_CORE=true
  elif [[ -z "$PREFIX_FILTER" && "$arg" != --* ]]; then
    PREFIX_FILTER="$arg"
  fi
done

echo "✅ Final values: DEV_CORE=$DEV_CORE, PREFIX_FILTER=$PREFIX_FILTER"

# ─────────────────────────────────────────────────────────────
# Select venv location
# ─────────────────────────────────────────────────────────────
if $DEV_CORE; then
  VENV_DIR="$THIS_SCRIPT/venv"
else
  VENV_DIR="$ROOT_DIR/venv"
fi

# ─────────────────────────────────────────────────────────────
# Activate virtualenv
# ─────────────────────────────────────────────────────────────
if [ -f "$VENV_DIR/bin/activate" ]; then
  echo "✅ Activating venv from: $VENV_DIR"
  # shellcheck disable=SC1090
  . "$VENV_DIR/bin/activate"
else
  echo "❌ Virtualenv not found at: $VENV_DIR"
  # exit 1
fi

# Diagnostic: show interpreter in use
echo "🐍 Using Python: $(which python)"
echo "📦 Using Pip:    $(which pip)"
echo "🔧 Pip version:  $(pip --version)"

# ─────────────────────────────────────────────────────────────
# Reinstall Rust crates (optional prefix)
# ─────────────────────────────────────────────────────────────
echo "🔁 Reinstalling Rust crates via: $RUST_SCRIPT"
if [ ! -f "$RUST_SCRIPT" ]; then
  echo "❌ Missing script: $RUST_SCRIPT"
  # exit 1
fi

if $DEV_CORE; then
  bash "$RUST_SCRIPT" "$PREFIX_FILTER" --dev-core
else
  bash "$RUST_SCRIPT" "$PREFIX_FILTER"
fi

# ─────────────────────────────────────────────────────────────
# Reinstall Python package in editable mode
# ─────────────────────────────────────────────────────────────
echo "🔁 Reinstalling Python package: summoner"

cd "$THIS_SCRIPT"

if pip show summoner > /dev/null 2>&1; then
  echo "🗑️  Uninstalling existing 'summoner' package..."
  pip uninstall -y summoner
else
  echo "ℹ️  'summoner' not currently installed — skipping uninstall."
fi

echo "📦 Installing 'summoner' in editable mode..."
if $DEV_CORE; then
  pip install -e .
else
  pip install .
fi

echo "✅ Python SDK reinstalled successfully with prefix: '$PREFIX_FILTER'"

if $DEV_CORE; then
  echo "   (used --dev-core → venv at $THIS_SCRIPT/venv)"
else
  echo "   (used default → venv at $ROOT_DIR/venv)"
fi
