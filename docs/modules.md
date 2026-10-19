# Next steps per module

| Module | After `install.sh` |
| --- | --- |
| homeassistant | Open `http://<host>:8123`, create your user. Install [HACS](https://hacs.xyz), then **card-mod** (Frontend) if you want per-card CSS. Pick a theme from `themes/thin_margins.yaml` per view. Dashboards: generate them with [homelab-ha-toolkit](https://github.com/mauriporte/homelab-ha-toolkit) (`servers_dashboard.py`, `android_tv_remote.py`). |
| monitoring | Uptime Kuma at `:3001` (create the admin user, add monitors, then HA's Uptime Kuma integration with an API key). Glances at `:61208` → HA's Glances integration. |
| portainer | `https://<host>:9443`, create the admin. HA's Portainer integration then gives a switch per container. |
| media | Jellyfin `:8096` (libraries under `/data`), then Prowlarr → Sonarr/Radarr/Lidarr (indexers, download client = qBittorrent at `gluetun:8080` from inside the network or `<host>:8080`), Jellyseerr `:5055`. FlareSolverr URL for Prowlarr: `http://<host>:8191`. |
| vpn-downloads | Check the exit country: `docker exec qbittorrent curl -s https://ipinfo.io/country`. In qBittorrent → Advanced → Network interface choose **tun0**. The web UI password is printed in `docker logs qbittorrent` on first start. |
| iptv | Threadfin `:34400/web`, tvheadend `:9981`. The channel-list pipeline (iptv-org → probe → M3U/XMLTV) is in homelab-ha-toolkit `iptv/`; see `docs/lessons.md` for the tvheadend notes. |
| mail | Stalwart admin at `:8090` (initial password in `docker logs stalwart`). Open 25/465/587/993 on the router to this host; set MX, SPF, DKIM and DMARC records. If the router has no NAT loopback, add split DNS for the mail hostname. |
| remote-access | Create the tunnel in Cloudflare Zero Trust, paste its token in your secrets, re-run. See `docs/cloudflare.md`. |
| sync | Syncthing `:8384`; set a GUI password first. |
| photos | Immich at `:2283`, create the admin. Photos go to `PHOTOS_DIR`. Set `IMMICH_DB_PASSWORD` in secrets **before** the first start (the database keeps the first password). |
| ai | `docker exec ollama ollama pull qwen3:8b` (or any model), then HA's Ollama integration at `http://<host>:11434`. NVIDIA GPU: install the NVIDIA Container Toolkit and add `gpus: all` to the ollama service. |
| youtube | Invidious at `:3000`. Generate `INVIDIOUS_HMAC_KEY` and a 16-character `INVIDIOUS_COMPANION_KEY` in secrets first; set `INVIDIOUS_DOMAIN` (and `INVIDIOUS_HTTPS_ONLY=true`, `INVIDIOUS_EXTERNAL_PORT=443` behind a tunnel). |
| stremio | Put a stremio-web build in `${DATA_DIR}/stremio-web`; web app at `:8095`, streaming server on the host network (`:11470`). In the web app, set the streaming server URL to your server. |
| dns | Edit `${DATA_DIR}/dnsmasq/dnsmasq.conf` (your hostnames → LAN IPs) and point your router's DHCP DNS at this host. DDNS needs a Cloudflare API token with DNS edit rights on the zone (`CLOUDFLARE_DNS_TOKEN`). |
| rclone | `docker compose --env-file .env run --rm rclone-dlna config` to add the remote, then restart; TVs see it as a DLNA server. |
| tailscale | Create an auth key in the Tailscale admin console (`TAILSCALE_AUTHKEY`). Advertise LAN routes with `TAILSCALE_EXTRA_ARGS=--advertise-routes=192.0.2.0/24` and approve them in the console. |
| iptv (extras) | `epg-grabber` builds a guide from `${DATA_DIR}/epg/channels.xml`; `iptv-public` serves `${DATA_DIR}/iptv-public/www` at a random secret path printed on first install (keep it secret: anyone with the link can watch). |
| notes-vault-patches | Optional, for the [Notes Vault](https://github.com/FezVrasta/ha-notes-vault) panel (HACS): pictures and HTML/PDF reports from your Obsidian vault, a readable folder tree on HA 2026.10, history folders newest first. Run `vault_files_server.py` where the vault lives, then `modules/notes-vault-patches/apply.sh` on the HA host. See its README. |
