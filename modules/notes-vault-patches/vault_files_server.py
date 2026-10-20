"""Read-only server for an Obsidian vault's pictures and HTML/PDF reports, for Home Assistant's Notes Vault panel.

Notes Vault (HACS) shows `![[picture.jpg]]` as plain text. With the patches in this folder it shows the picture, served
by this script from the machine that holds the vault, so pictures never have to be copied to the Home Assistant host.

    GET /vault-img/<key>/<path in the vault or bare file name>   -> the file (images, .html, .pdf) or 404
    GET /vault-img/<key>/reel/<code>        -> 302 to a public Instagram reel's video (needs yt-dlp; no login)
    GET /vault-img/<key>/maps?u=<short link> -> 302 to Google's keyless map for a maps.app.goo.gl link

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
import json, os, re, threading, time, urllib.parse, urllib.request
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


def maps_embed_url(url):
    """Google's keyless map embed for a full Google Maps link (coordinates, ?query=/?q=, or a /place/ or /search/ name);
    "" for directions or anything that isn't a Google Maps place. Patch 11 and the Beeper card use the same rules."""
    u = urllib.parse.urlsplit(url)
    host = u.hostname or ""
    if not re.search(r"(^|\.)google\.[a-z.]+$", host) or "/maps" not in u.path + "/" + host or "/maps/dir/" in u.path:
        return ""
    qs = urllib.parse.parse_qs(u.query)
    m = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)(?:,(\d+(?:\.\d+)?)z)?", u.path)
    place = re.search(r"/maps/(?:place|search)/([^/@]+)", u.path)
    q = ((qs.get("query") or qs.get("q") or [""])[0] or (urllib.parse.unquote_plus(place.group(1)) if place else "")
         or (f"{m.group(1)},{m.group(2)}" if m else ""))
    zoom = round(float(m.group(3))) if m and m.group(3) else 15
    return f"https://maps.google.com/maps?q={urllib.parse.quote(q)}&z={zoom}&output=embed" if q else ""


REELS, MAPS = {}, {}  # reel code -> (time, video URL; Instagram's links expire), short link -> embed URL


def reel_video(code):
    t, url = REELS.get(code, (0, ""))
    if time.time() - t > 1200:
        import yt_dlp  # optional dependency, only for reels
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True, "format": "best[ext=mp4]/best"}) as y:
            url = (y.extract_info(f"https://www.instagram.com/reel/{code}/", download=False) or {}).get("url", "")
        REELS[code] = (time.time(), url)
    return url


def short_map(link):
    if link not in MAPS:
        req = urllib.request.Request(link, headers={"User-Agent": "Mozilla/5.0"})
        final = urllib.request.urlopen(req, timeout=15).geturl()
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(final).query)
        if "consent.google" in final and q.get("continue"):  # EU consent page: the real address is in "continue"
            final = q["continue"][0]
        MAPS[link] = maps_embed_url(final)
    return MAPS[link]


class Handler(BaseHTTPRequestHandler):
    def _redirect(self, url):
        if not url.startswith("https://"):
            self.send_error(404); return
        self.send_response(302); self.send_header("Location", url); self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def do_GET(self):
        parts = urllib.parse.urlsplit(self.path)
        rel = urllib.parse.unquote(parts.path)
        tail = rel.removeprefix(PREFIX)
        if rel.startswith(PREFIX) and (m := re.fullmatch(r"reel/([\w-]{5,40})", tail)):
            try:
                return self._redirect(reel_video(m.group(1)))
            except Exception as e:
                print("reel not resolved:", type(e).__name__); self.send_error(404); return
        if rel.startswith(PREFIX) and tail == "maps":
            link = (urllib.parse.parse_qs(parts.query).get("u") or [""])[0]
            if not re.match(r"https://(maps\.app\.goo\.gl|goo\.gl/maps)/[\w-]+$", link):
                self.send_error(404); return
            try:
                return self._redirect(short_map(link))
            except Exception as e:
                print("map not resolved:", type(e).__name__); self.send_error(404); return
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
