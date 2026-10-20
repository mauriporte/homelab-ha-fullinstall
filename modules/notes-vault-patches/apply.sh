#!/bin/sh
# Apply the Notes Vault patches inside the Home Assistant container (idempotent). Usage: ./apply.sh [container]
set -e
C="${1:-${HA_CONTAINER:-homeassistant}}"
cd "$(dirname "$0")"
for p in [0-9][0-9]_*.py; do
  printf '%s: ' "$p"
  docker exec -i "$C" python3 - < "$p"
done
echo "Done. Reload Notes Vault (Settings > Devices & services > Notes Vault > Reload) and refresh the browser."
