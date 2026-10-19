#!/usr/bin/env bash
# Copies the starter config into ${DATA_DIR}/homeassistant the first time (never overwrites an existing setup).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
dest="$DATA_DIR/homeassistant"
mkdir -p "$dest"
if [[ -z "$(ls -A "$dest")" ]]; then
  cp -r "$here/config/." "$dest/"
  touch "$dest/automations.yaml" "$dest/scripts.yaml" "$dest/scenes.yaml"
  [[ -s "$dest/automations.yaml" ]] || echo "[]" > "$dest/automations.yaml"
  echo "homeassistant: starter config copied to $dest"
else
  echo "homeassistant: $dest is not empty, keeping your config"
fi
