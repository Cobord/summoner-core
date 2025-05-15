#!/bin/bash

set -e  # Exit on error

# Ensure we're using the virtualenv Python and tools
if [ -f "../../venv/bin/activate" ]; then
  . "../../venv/bin/activate"
  echo "✅ Virtualenv activated inside reinstall_rust_server.sh"
else
  echo "❌ Could not find venv/bin/activate — maturin may fail"
fi

# --- Parse optional argument ---
PREFIX_FILTER="$1"  # e.g., "relay_v" or empty for all

# --- Resolve paths ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUST_DIR="$SCRIPT_DIR/summoner/rust"

# --- Validate directory ---
if [ ! -d "$RUST_DIR" ]; then
  echo "❌ Directory not found: $RUST_DIR"
  exit 1
fi

# --- Process matching subdirectories with Cargo.toml ---
FOUND=0
for DIR in "$RUST_DIR"/*/; do
  BASENAME="$(basename "$DIR")"
  if [[ -n "$PREFIX_FILTER" && "$BASENAME" != $PREFIX_FILTER* ]]; then
    continue
  fi

  if [ -f "$DIR/Cargo.toml" ]; then
    FOUND=1
    echo "🔄 Reinstalling crate in: $DIR"

    cd "$DIR"
    echo "🧼 Running cargo clean..."
    cargo clean

    echo "🔨 Rebuilding with maturin develop --release..."
    maturin develop --release

    echo "✅ Reinstalled crate in $DIR"
  fi
done

if [ $FOUND -eq 0 ]; then
  echo "⚠️ No matching folders with Cargo.toml found in $RUST_DIR"
fi
