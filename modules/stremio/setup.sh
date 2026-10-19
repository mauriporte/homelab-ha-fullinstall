#!/usr/bin/env bash
# The Stremio web app has no official image: nginx serves a build of github.com/Stremio/stremio-web.
set -euo pipefail
mkdir -p "$DATA_DIR/stremio-web" "$DATA_DIR/stremio-server"
if [[ -z "$(ls -A "$DATA_DIR/stremio-web")" ]]; then
  echo "stremio: put a stremio-web build in $DATA_DIR/stremio-web (git clone https://github.com/Stremio/stremio-web; npm ci; npm run build; copy build/)"
fi
