#!/usr/bin/env bash
# homelab-ha-fullinstall installer (Debian/Ubuntu/Raspberry Pi OS; other Linux with Docker already installed).
#   ./install.sh                         interactive: pick modules
#   ./install.sh homeassistant media     non-interactive
#   ./install.sh --list                  show modules
set -euo pipefail
cd "$(dirname "$0")"

MODULES=(homeassistant monitoring portainer media vpn-downloads iptv mail remote-access sync)
declare -A INFO=(
  [homeassistant]="Home Assistant (host network) + starter config, themes and card-mod notes"
  [monitoring]="Uptime Kuma + Glances (host metrics for HA)"
  [portainer]="Portainer (HA gets a start/stop switch per container)"
  [media]="Jellyfin, Jellyseerr, Sonarr, Radarr, Lidarr, Prowlarr, FlareSolverr"
  [vpn-downloads]="qBittorrent that can only reach the internet through gluetun (VPN kill switch)"
  [iptv]="Threadfin (Jellyfin Live TV) + tvheadend (Kodi)"
  [mail]="Stalwart mail server (SMTP/IMAP)"
  [remote-access]="Cloudflare Tunnel (public hostnames without opening ports)"
  [sync]="Syncthing"
)

die() { echo "error: $*" >&2; exit 1; }

list() { for m in "${MODULES[@]}"; do printf '  %-14s %s\n' "$m" "${INFO[$m]}"; done; }

valid() { local m; for m in "${MODULES[@]}"; do [[ $m == "$1" ]] && return 0; done; return 1; }

if [[ ${1:-} == --list ]]; then list; exit 0; fi

# 1. Docker
if ! command -v docker >/dev/null; then
  echo "Docker not found: installing it with the official convenience script (needs sudo)."
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER" || true
  echo "Docker installed. Log out and back in (docker group), then run ./install.sh again."
  exit 0
fi
docker compose version >/dev/null 2>&1 || die "the docker compose plugin is missing"

# 2. Settings and secrets
[[ -f .env ]] || { cp .env.example .env; echo "Created .env from .env.example: edit it, then run ./install.sh again."; exit 0; }
if [[ -f secrets.enc.env ]]; then
  command -v sops >/dev/null || die "secrets.enc.env exists but sops is not installed (docs/secrets.md)"
  sops --decrypt --input-type dotenv --output-type dotenv secrets.enc.env > .secrets.env
  chmod 600 .secrets.env
fi
ENV_ARGS=(--env-file .env)
[[ -f .secrets.env ]] && ENV_ARGS+=(--env-file .secrets.env)

# 3. Modules
chosen=("$@")
if [[ ${#chosen[@]} -eq 0 ]]; then
  echo "Modules:"; list
  read -rp "Which ones (space-separated): " -a chosen
fi
[[ ${#chosen[@]} -gt 0 ]] || die "no module chosen"
profiles=()
for m in "${chosen[@]}"; do valid "$m" || die "unknown module '$m' (./install.sh --list)"; profiles+=(--profile "$m"); done

# 4. Data folders and module extras
set -a
# shellcheck disable=SC1091
source .env
# shellcheck disable=SC1091
if [[ -f .secrets.env ]]; then source .secrets.env; fi
set +a
mkdir -p "$DATA_DIR"
for m in "${chosen[@]}"; do
  if [[ -x modules/$m/setup.sh ]]; then DATA_DIR="$DATA_DIR" "modules/$m/setup.sh"; fi
done

# 5. Start
docker compose "${ENV_ARGS[@]}" "${profiles[@]}" up -d
echo
echo "Started: ${chosen[*]}"
echo "Next steps per module: docs/modules.md"
