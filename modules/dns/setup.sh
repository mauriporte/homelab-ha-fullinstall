#!/usr/bin/env bash
# Creates ${DATA_DIR}/dnsmasq/dnsmasq.conf from the example the first time.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$DATA_DIR/dnsmasq"
if [[ ! -f "$DATA_DIR/dnsmasq/dnsmasq.conf" ]]; then
  cp "$here/dnsmasq.conf.example" "$DATA_DIR/dnsmasq/dnsmasq.conf"
  echo "dns: edit $DATA_DIR/dnsmasq/dnsmasq.conf (your hostnames → LAN IPs)"
fi
