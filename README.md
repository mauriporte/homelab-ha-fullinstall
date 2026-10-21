# homelab-ha-fullinstall

A self-hosted homelab around **Home Assistant**, installable on a fresh Linux server with one script:
pick the modules you want, fill in one settings file, run `./install.sh`.

Everything runs in Docker (one `compose.yaml`, one profile per module). Secrets stay encrypted in the repo
with **sops + age**. Remote access goes through **Cloudflare Tunnel + Access**, so no router ports are opened
(except mail, if you want it).

| Module | What you get |
| --- | --- |
| `homeassistant` | Home Assistant (host network) with a starter config, packages folder and thin-margin themes |
| `monitoring` | Uptime Kuma + Glances (host metrics for HA) |
| `portainer` | Portainer (HA's Portainer integration then gives a start/stop switch per container) |
| `media` | Jellyfin, Jellyseerr, Sonarr, Radarr, Lidarr, Prowlarr, Jackett, FlareSolverr |
| `vpn-downloads` | qBittorrent that can only reach the internet through a VPN (gluetun kill switch) |
| `iptv` | Threadfin (Jellyfin Live TV) + tvheadend (Kodi) |
| `mail` | Stalwart mail server |
| `remote-access` | Cloudflare Tunnel connector |
| `sync` | Syncthing |
| `photos` | Immich (photos and videos, face/object search) |
| `ai` | Ollama (local LLMs for HA Assist) |
| `youtube` | Invidious (private YouTube front-end) + companion + database |
| `stremio` | Stremio streaming server + self-hosted web app |
| `dns` | Cloudflare DDNS + dnsmasq split DNS |
| `rclone` | An rclone remote (e.g. Google Drive) served over DLNA to TVs |
| `tailscale` | Tailscale node |

**Roles** (presets in `roles/`): `ha-server`, `media-server`, `pi`, `all-in-one`: `./install.sh --role media-server`.
Run the installer on each machine with its role to spread the modules over several servers.

Extras outside Docker: [`modules/omv-frame-proxy`](modules/omv-frame-proxy) shows the openmediavault UI
inside a Home Assistant iframe, already logged in. [`modules/dashboard-cards`](modules/dashboard-cards) has two small dashboard
modules: a card that shows a hass_ingress panel inside a dashboard (works in the mobile apps too), and your own hints
in empty text fields. [`modules/google-maps-zones`](modules/google-maps-zones) keeps one HA zone per place saved in
Google Maps (lists, starred, labelled), on a button in HA and daily; it runs on a desktop with Chrome or Edge.

## Install

```bash
git clone https://github.com/mauriporte/homelab-ha-fullinstall && cd homelab-ha-fullinstall
./install.sh            # first run: installs Docker if needed and creates .env
nano .env               # paths, timezone, ports
./install.sh            # pick modules (or: ./install.sh homeassistant monitoring, or --role ha-server)
```

Then follow [docs/modules.md](docs/modules.md) for each module's first-run steps.

## Secrets

Keep passwords and tokens in `secrets.enc.env`, encrypted with your age key; `install.sh` decrypts it at start.
See [docs/secrets.md](docs/secrets.md). `secrets.example.env` lists the names.

## Related

- [homelab-ha-toolkit](https://github.com/mauriporte/homelab-ha-toolkit): Home Assistant dashboard generators
  (servers dashboard: equal-height summary/storage/network row, apps grid and per-app table; Android TV remote) and the IPTV channel pipeline.
- [ha-vnc-control](https://github.com/mauriporte/ha-vnc-control): VNC desktops inside Home Assistant.
- [ha-ddwrt-monitor](https://github.com/mauriporte/ha-ddwrt-monitor): DD-WRT router/AP monitoring for Home Assistant.
- [ha-terminal-control](https://github.com/mauriporte/ha-terminal-control): a terminal (Claude Code) inside Home Assistant.
- [docs/cloudflare.md](docs/cloudflare.md): the tunnel + Access pattern, including pages embedded in HA.
- [docs/lessons.md](docs/lessons.md): gotchas that cost hours (VPN limits, DD-WRT, dashboards, IPTV).

## License

MIT
