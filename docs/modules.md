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
