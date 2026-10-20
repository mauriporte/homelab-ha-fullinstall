# Notes Vault patches

Local fixes for [Notes Vault](https://github.com/FezVrasta/ha-notes-vault) (HACS, tested on v0.9.0 with Home Assistant
2026.10). A HACS update of Notes Vault overwrites them: run `apply.sh` again afterwards.

| Patch | What it does |
| --- | --- |
| `01_images.py` | `![[picture.jpg]]` shows the picture (cards and the Notes page) instead of its file name |
| `02_tree_rows.py` | HA 2026.10 removed `ha-list`/`ha-list-item`; the folder tree and lists rendered as one paragraph. This draws them as rows again (only while those elements are undefined) |
| `03_date_after_name.py` | In the tree, `2026-10-19 Name` shows as `Name · 2026-10-19` (order unchanged) |
| `04_html_embeds.py` | `![[report.html]]` / `.pdf` show inline in a sandboxed frame with an "open in new tab" link |
| `05_file_links.py` | A plain link to a served file (`[[report.pdf]]`) opens it in a new tab instead of creating an empty note |
| `06_historial_newest_first.py` | Notes in any folder named `Historial` are listed newest first |
| `07_historial_date_first.py` | ...and keep their date first (`2026-10-18 - Report`) |
| `08_collapsible_reports.py` | `![[r.html\|abierto: Title]]` / `\|plegado: Title` embeds fold, open or folded |
| `10_reel_player.py` | An Instagram reel link (`/reel/`, `/tv/`) gets "▶ Ver reel": plays the video inline (needs `yt-dlp` next to the server) |
| `11_map_preview.py` | A Google Maps link becomes a "🗺 Ver mapa" button that shows Google's keyless map under it (short `maps.app.goo.gl` links go through the server) |

## Setup

1. Run `vault_files_server.py` on the machine that holds the vault (see its docstring for the environment variables).
   It serves only the folders you list, behind a secret key, and publishes `sensor.vault_images` so the panel can build
   the URLs. Open its port only to your LAN. For reels (patch 10) install `yt-dlp` (`pip install yt-dlp`); public
   reels only, without logging in to Instagram.
2. For remote viewing, route `^/vault-img/` on your Home Assistant hostname to that machine (for example a Cloudflare
   Tunnel ingress rule with a `path`); same origin, so no extra login is needed in the browser.
3. Apply the patches on the Home Assistant host (`HA_CONTAINER` defaults to `homeassistant`):

       ./apply.sh

4. Reload Notes Vault (Settings > Devices & services > Notes Vault > Reload) and refresh the browser: the script URL
   carries the file's modification time, so the new code loads.

The patches are idempotent (running them twice changes nothing) and each one keeps a marker comment `local patch`.
Keep a copy of the originals before the first run if you want to roll back:
`docker exec homeassistant cp /config/custom_components/notes_vault/frontend/notes-vault.js /config/notes-vault.js.orig`
(and the same for `editor.js`).
