#!/usr/bin/env bash
# First-run files for the iptv module: an empty channels.xml for epg-grabber, and the nginx config that
# publishes ${DATA_DIR}/iptv-public/www under a secret path (anyone with the link can watch, so keep it random).
set -euo pipefail
mkdir -p "$DATA_DIR/epg" "$DATA_DIR/iptv-public/www"
[[ -f "$DATA_DIR/epg/channels.xml" ]] || printf '<?xml version="1.0" encoding="UTF-8"?>\n<channels>\n</channels>\n' > "$DATA_DIR/epg/channels.xml"
conf="$DATA_DIR/iptv-public/default.conf"
if [[ ! -f "$conf" ]]; then
  key="${IPTV_PUBLIC_KEY:-$(head -c 12 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 16)}"
  cat > "$conf" <<NGINX
server {
  listen 8099;
  location = / { return 404; }
  location /$key/ { alias /www/; add_header Access-Control-Allow-Origin *; }
}
NGINX
  echo "iptv: playlist and guide are served at http://<host>:${IPTV_PUBLIC_PORT:-8099}/$key/ (put list.m3u and guide.xml in $DATA_DIR/iptv-public/www)"
fi
