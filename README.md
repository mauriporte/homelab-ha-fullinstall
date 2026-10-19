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
| `media` | Jellyfin, Jellyseerr, Sonarr, Radarr, Lidarr, Prowlarr, FlareSolverr |
| `vpn-downloads` | qBittorrent that can only reach the internet through a VPN (gluetun kill switch) |
| `iptv` | Threadfin (Jellyfin Live TV) + tvheadend (Kodi) |
| `mail` | Stalwart mail server |
| `remote-access` | Cloudflare Tunnel connector |
| `sync` | Syncthing |

Extras outside Docker: [`modules/omv-frame-proxy`](modules/omv-frame-proxy) shows the openmediavault UI
inside a Home Assistant iframe, already logged in.

## Install

```bash
git clone https://github.com/mauriporte/homelab-ha-fullinstall && cd homelab-ha-fullinstall
./install.sh            # first run: installs Docker if needed and creates .env
nano .env               # paths, timezone, ports
./install.sh            # pick modules (or: ./install.sh homeassistant monitoring media)
```

Then follow [docs/modules.md](docs/modules.md) for each module's first-run steps.

## Secrets

Keep passwords and tokens in `secrets.enc.env`, encrypted with your age key; `install.sh` decrypts it at start.
See [docs/secrets.md](docs/secrets.md). `secrets.example.env` lists the names.

## Related

- [homelab-ha-toolkit](https://github.com/mauriporte/homelab-ha-toolkit): Home Assistant dashboard generators
  (servers dashboard with gauges, apps grid and per-app table; Android TV remote) and the IPTV channel pipeline.
- [ha-vnc-control](https://github.com/mauriporte/ha-vnc-control): VNC desktops inside Home Assistant.
- [ha-terminal-control](https://github.com/mauriporte/ha-terminal-control): a terminal (Claude Code) inside Home Assistant.
- [docs/cloudflare.md](docs/cloudflare.md): the tunnel + Access pattern, including pages embedded in HA.
- [docs/lessons.md](docs/lessons.md): gotchas that cost hours (VPN limits, DD-WRT, dashboards, IPTV).

## License

MIT
