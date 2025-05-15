#!/usr/bin/env bash

set -euo pipefail

# ─────────────────────────────────────────────────────────────
# Resolve paths
# ─────────────────────────────────────────────────────────────
THIS_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$THIS_SCRIPT/.." && pwd)"
VENV_DIR="$ROOT_DIR/venv"
RUST_DIR="$THIS_SCRIPT/summoner/rust"

# ─────────────────────────────────────────────────────────────
# Activate virtualenv
# ─────────────────────────────────────────────────────────────
if [ -f "$VENV_DIR/bin/activate" ]; then
  echo "✅ Activating venv from: $VENV_DIR"
  # shellcheck disable=SC1090
  . "$VENV_DIR/bin/activate"
else
  echo "❌ Virtualenv not found at: $VENV_DIR"
  exit 1
fi

# ─────────────────────────────────────────────────────────────
# Diagnostics
# ─────────────────────────────────────────────────────────────
echo "🐍 Python:   $(which python)"
echo "🔧 Maturin:  $(which maturin || echo 'not found')"

# ─────────────────────────────────────────────────────────────
# Optional prefix filter
# ─────────────────────────────────────────────────────────────
PREFIX_FILTER="${1:-}"  # pass e.g. `rust_server_sdk` if you only want that crate

# ─────────────────────────────────────────────────────────────
# Validate Rust SDK directory
# ─────────────────────────────────────────────────────────────
if [ ! -d "$RUST_DIR" ]; then
  echo "❌ Expected Rust SDK path not found: $RUST_DIR"
  exit 1
fi

# ─────────────────────────────────────────────────────────────
# Build each matching crate
# ─────────────────────────────────────────────────────────────
FOUND=0
echo "🔍 Searching for Rust crates in: $RUST_DIR"

for DIR in "$RUST_DIR"/*/; do
  BASENAME="$(basename "$DIR")"
  echo "🔎 Found directory: $BASENAME"

  # skip if it doesn’t match the optional prefix
  if [[ -n "$PREFIX_FILTER" && "$BASENAME" != "$PREFIX_FILTER"* ]]; then
    echo "🚫 Skipping $BASENAME (prefix filter: '$PREFIX_FILTER')"
    continue
  fi

  if [ -f "$DIR/Cargo.toml" ]; then
    FOUND=1
    echo "🔨 Building with: maturin develop --release"
    cd "$DIR"
    maturin develop --release
    echo "✅ Reinstalled crate: $BASENAME"
  else
    echo "⚠️ No Cargo.toml in $DIR — skipping"
  fi
done

if [ "$FOUND" -eq 0 ]; then
  echo "⚠️ No matching crates found with prefix: '$PREFIX_FILTER'"
fi
