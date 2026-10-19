"""Read-only server for an Obsidian vault's pictures and HTML/PDF reports, for Home Assistant's Notes Vault panel.

Notes Vault (HACS) shows `![[picture.jpg]]` as plain text. With the patches in this folder it shows the picture, served
by this script from the machine that holds the vault, so pictures never have to be copied to the Home Assistant host.

    GET /vault-img/<key>/<path in the vault or bare file name>   -> the file (images, .html, .pdf) or 404

- Only files under the folders you list are served; nothing else in the vault (notes included) is reachable.
- Every path carries a secret key: put this behind a tunnel only with the key, or behind an access login.
- HTML is served with `Content-Security-Policy: sandbox`, so a report cannot run scripts on Home Assistant's address.
- Every minute it publishes `sensor.vault_images` (attributes `key`, `lan`) to Home Assistant; the patched panel reads
  the key from there, so the key never appears in files Home Assistant serves without a login.

Config: environment variables
    VAULT=/path/to/vault  FOLDERS="90-assets,20-dashboards/Reports"  PORT=8796  KEY=<random>
    LAN=http://<this-host>:8796   HA_URL=http://<ha-host>:8123  HA_TOKEN=<long-lived token>
Run: python vault_files_server.py   (generate a key with: python -c "import secrets; print(secrets.token_urlsafe(18))")
"""
import json, os, threading, time, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VAULT = os.path.realpath(os.environ["VAULT"])
ROOTS = [os.path.realpath(os.path.join(VAULT, d.strip())) for d in os.environ.get("FOLDERS", "90-assets").split(",")]
PORT, KEY = int(os.environ.get("PORT", 8796)), os.environ["KEY"]
PREFIX = f"/vault-img/{KEY}/"
TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp",
         ".html": "text/html; charset=utf-8", ".pdf": "application/pdf"}
names = {}


def by_name(name):
    """Notes embed files by bare name, as Obsidian resolves them: look it up under the served folders."""
    if name not in names:
        names.clear()
        for root in ROOTS:
            for d, _, fs in os.walk(root):
                for f in fs:
                    names.setdefault(f, os.path.join(d, f))
    return names.get(name, "")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        rel = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
        tail = rel.removeprefix(PREFIX)
        f = os.path.realpath(by_name(tail) if "/" not in tail else os.path.join(VAULT, tail))
        kind = TYPES.get(os.path.splitext(f)[1].lower())
        if not rel.startswith(PREFIX) or not kind or not any(f.startswith(r + os.sep) for r in ROOTS) or not os.path.isfile(f):
            self.send_error(404); return
        body = open(f, "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", kind); self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "private, max-age=86400" if kind.startswith("image/") else "no-cache")
        if kind.startswith("text/html"):
            self.send_header("Content-Security-Policy", "sandbox allow-popups allow-popups-to-escape-sandbox")
        self.end_headers(); self.wfile.write(body)

    def log_message(self, *a):
        pass


def publish_key():
    """sensor.vault_images in Home Assistant: readable only with a Home Assistant login."""
    ha, token = os.environ.get("HA_URL"), os.environ.get("HA_TOKEN")
    if not (ha and token):
        return
    while True:
        try:
            body = json.dumps({"state": "on", "attributes": {"friendly_name": "Vault files", "key": KEY,
                                                             "lan": os.environ.get("LAN", "")}}).encode()
            urllib.request.urlopen(urllib.request.Request(f"{ha}/api/states/sensor.vault_images", data=body, method="POST",
                                   headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"}), timeout=20)
        except OSError as e:
            print("could not publish sensor.vault_images:", e)
        time.sleep(60)


if __name__ == "__main__":
    threading.Thread(target=publish_key, daemon=True).start()
    print(f"serving {', '.join(ROOTS)} on :{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
