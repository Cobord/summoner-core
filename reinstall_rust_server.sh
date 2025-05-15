#!/bin/bash

set -e  # Exit on error

# Activate venv explicitly from parent of summoner-src
VENV_PATH=\"$(cd \"$(dirname \"$0\")/..\" && pwd)/venv\"
if [ -f \"$VENV_PATH/bin/activate\" ]; then
  echo \"✅ Activating venv from $VENV_PATH\"
  . \"$VENV_PATH/bin/activate\"
else
  echo \"❌ Could not find venv at $VENV_PATH\"
  exit 1
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
