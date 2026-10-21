"""Google Maps saved places -> Home Assistant zones.

Reads every saved list, the starred places and the labelled places of the Google account signed in to its own
browser profile, and keeps one HA zone per place: new saves are added, moved or renamed ones updated, unsaved ones
removed. It only ever touches zones it created (or took over on its first run), listed in its state file.

Google has no API for saved lists, so this reads what Google Maps' own web page loads: the `entitylist/getlist`
answer for each list, and for starred and labelled places the pin in the address after opening each one. If Google
changes that page the sync fails and says so in HA; it never deletes zones after a failed read.

    python gmaps_zones.py --login   open the profile in a normal browser window once, to sign in to Google by hand
    python gmaps_zones.py --dry     read and show what would change, without touching HA
    python gmaps_zones.py           read and sync now
    python gmaps_zones.py --watch   keep running: sync when HA's button is pressed and once a day
    (--config PATH: settings file, default gmaps_zones.json next to this script)
"""
from __future__ import annotations

import json, math, os, re, shutil, subprocess, sys, time
from datetime import datetime

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
SAVED = "https://www.google.com/maps/@20,0,3z/data=!4m2!10m1!1e"  # + 1 lists, 2 labelled places
STARRED, LABELLED = "★", "Labelled"
SAME_M = 3  # the same spot saved in two lists; neighbouring bars can be 12 m apart
ADOPT_M = 10  # first run: an existing zone this close to a place is taken over (a place pin vs the map centre)
BROWSERS = {  # channel -> executable for --login (a normal window: Google refuses sign-ins in automated browsers)
    "msedge": [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", "microsoft-edge", "microsoft-edge-stable"],
    "chrome": [r"C:\Program Files\Google\Chrome\Application\chrome.exe", "google-chrome", "google-chrome-stable"],
}
DEFAULTS = {
    "home_assistant": {"url": "http://homeassistant.local:8123", "token_env": "HA_TOKEN"},
    "profile": "~/.gmaps-zones-profile", "browser": {"channel": "msedge", "executable": ""}, "locale": "en-US",
    "button": "input_button.sync_google_maps", "daily_at": "04:45", "sensor": "sensor.google_maps_places",
    "radius": 30, "skip_near_home_m": 100, "icons": {}, "default_icon": "mdi:map-marker", "label_icon": "mdi:tag",
    "exclude": [],
}


def log(*a):
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)


def load_config(path: str) -> dict:
    cfg = {**DEFAULTS, **json.load(open(path, encoding="utf-8"))}
    cfg["home_assistant"] = {**DEFAULTS["home_assistant"], **cfg["home_assistant"]}
    cfg["browser"] = {**DEFAULTS["browser"], **cfg["browser"]}
    cfg["profile"] = os.path.expanduser(os.path.expandvars(cfg["profile"]))
    base = os.path.splitext(os.path.abspath(path))[0]
    cfg["_state"], cfg["_last_read"] = base + "-state.json", base + "-last-read.json"
    return cfg


def dist_m(a, b) -> float:
    k = math.pi / 180
    x = (b[1] - a[1]) * k * math.cos((a[0] + b[0]) / 2 * k)
    return 6371000 * math.hypot(x, (b[0] - a[0]) * k)


def excluder(patterns: list[str]):
    """A test for `exclude`: patterns (case-insensitive) matched against a place's name and address."""
    rx = re.compile("|".join(f"(?:{p})" for p in patterns), re.I) if patterns else None
    return lambda text: bool(rx and rx.search(text))


def drop_excluded(lists: dict, unread: list, patterns: list[str]) -> tuple[dict, list]:
    """Leave out excluded places (e.g. old home addresses): they never become zones, nor appear in the sensor,
    notifications or the last-read file. Zones made for them earlier then get deleted like unsaved places."""
    hit = excluder(patterns)
    return ({k: [p for p in v if not hit(p["name"] + " " + p.get("addr", ""))] for k, v in lists.items()},
            [n for n in unread if not hit(n)])


# ---------- reading Google Maps ----------

def parse_getlist(text: str) -> tuple[str, list[dict]]:
    """A list's name and places from Google Maps' getlist answer (JSON after the `)]}'` guard line)."""
    lst = json.loads(text[text.index("\n") + 1:])[0]
    places = []
    for e in lst[8] or []:
        pos = (e[1] or [None] * 6)[5] or []
        if len(pos) >= 4 and pos[2] is not None:
            addr = (e[1][4] if len(e[1]) > 4 else "") or ""
            places.append({"name": e[2] or addr, "addr": addr, "lat": pos[2], "lng": pos[3]})
    return lst[4], places


def coords_from_url(url: str):
    """The place's own pin from the address after opening it; the map centre only when zoomed in on the place.
    !8m2!3d<lat>!4d<lng> is the pin: areas (e.g. a neighbourhood) carry other !3d!4d pairs that are not the place,
    and zoomed out the map centre can be hundreds of km off."""
    m = re.search(r"!8m2!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url) or \
        re.search(r"/maps/place/[^@]*@(-?\d+\.\d+),(-?\d+\.\d+),(1[4-9]|2\d)(?:\.\d+)?z", url)
    return (float(m.group(1)), float(m.group(2))) if m else None


def empty_list_row(text: str) -> bool:
    """A list row whose last line ends in "0 <places>" (any language): Google sends no list answer to wait for."""
    last = text.strip().splitlines()[-1] if text.strip() else ""
    return bool(re.search(r"(^|\D)0\s+\S+\s*$", last))


def free_profile(profile: str) -> None:
    """Browsers keep running in the background after their window closes (e.g. after --login) and hold the profile."""
    if os.name == "nt":
        subprocess.run(["powershell", "-NoProfile", "-c",
                        "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "
                        f"'*--user-data-dir={profile}*' -and $_.CommandLine -notlike '*--type=*' }} | "
                        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"],
                       capture_output=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    else:
        subprocess.run(["pkill", "-f", f"--user-data-dir={profile}"], capture_output=True)
    time.sleep(2)


def read_saved(cfg: dict, headless=True) -> tuple[dict[str, list[dict]], list[str], list[str]]:
    """({list name: [{name, addr, lat, lng}]}, unread, broken); starred and labelled places come as the lists
    STARRED and LABELLED. unread: places seen by name but not located (still saved: keep their zones).
    broken: lists that did not load (their contents are unknown: delete nothing)."""
    from playwright.sync_api import sync_playwright
    lists: dict[str, list[dict]] = {}
    unread: list[str] = []
    broken: list[str] = []
    answers = [0]
    free_profile(cfg["profile"])
    with sync_playwright() as p:
        b = cfg["browser"]
        ctx = p.chromium.launch_persistent_context(
            cfg["profile"], headless=headless, locale=cfg["locale"], viewport={"width": 1400, "height": 900},
            **({"channel": b["channel"]} if b["channel"] in BROWSERS else {}))
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            def on_response(r):
                if "/maps/preview/entitylist/getlist" in r.url:
                    try:
                        name, places = parse_getlist(r.text())
                        lists[name] = places
                        answers[0] += 1
                    except Exception as e:
                        log("unreadable list answer:", type(e).__name__)
            page.on("response", on_response)

            # list/label rows carry their name in Google's large body text, places inside a list in the headline text
            ROWS, ITEMS = ("[role=tabpanel] button:has(.fontBodyLarge)", ".fontBodyLarge"), \
                          ("[role=main] button:has(.fontHeadlineSmall)", ".fontHeadlineSmall")
            # long lists only render what has been scrolled to; scroll whichever side panels can scroll
            SCROLL = """by => { for (const e of document.querySelectorAll('[role=main] *'))
                         if (e.scrollHeight > e.clientHeight + 20 && getComputedStyle(e).overflowY != 'visible')
                           e.scrollTop = by ? e.scrollTop + by : e.scrollHeight; }"""

            def open_tab(n):
                page.goto(SAVED + str(n), wait_until="domcontentloaded")
                page.wait_for_timeout(4000)
                if "accounts.google.com" in page.url or not page.locator("[role=tab]").count():
                    raise RuntimeError("not signed in to Google (run: python gmaps_zones.py --login)")

            def names(kind):
                for _ in range(12):
                    page.evaluate(SCROLL, 0)
                    page.wait_for_timeout(500)
                return [t.strip() for t in page.locator(f"{kind[0]} {kind[1]}").all_inner_texts()]

            def open_each(kind, on_open, failed):
                """Open every row by name (positions shift: going back re-renders the list), then come back.
                on_open(name, row text, whether a list answer arrived); rows that won't open go to `failed`."""
                for name in names(kind):
                    row = page.locator(kind[0]).filter(has=page.locator(kind[1], has_text=name)).first
                    for _ in range(15):
                        if row.count():
                            break
                        page.evaluate(SCROLL, 600)
                        page.wait_for_timeout(400)
                    before, n = page.url, answers[0]
                    try:
                        row.scroll_into_view_if_needed(timeout=5000)
                        text = row.inner_text(timeout=5000)
                        row.click(timeout=5000)
                        page.wait_for_function("u => location.href !== u", arg=before, timeout=15000)
                    except Exception:
                        failed.append(name)
                        continue
                    page.wait_for_timeout(2500)
                    on_open(name, text, answers[0] > n)
                    page.go_back()
                    page.wait_for_timeout(1500)

            def place(into):
                def one(name, text, _):
                    for _ in range(16):  # the pin reaches the address a moment after the page opens
                        if "!8m2!3d" in page.url:
                            break
                        page.wait_for_timeout(500)
                    pos = coords_from_url(page.url)
                    if pos:  # the row's text holds the address (labelled places are named e.g. just "Home")
                        into.append({"name": name, "addr": " ".join(text.split()), "lat": pos[0], "lng": pos[1]})
                    else:
                        unread.append(name)  # e.g. an area with no pin: still saved, just not locatable
                return one

            def read_list(name, text, answered):
                if "!3e4" in page.url:  # the starred list: no list answer, each place is opened instead
                    lists[STARRED] = []
                    open_each(ITEMS, place(lists[STARRED]), unread)
                elif not answered and not empty_list_row(text):
                    broken.append(name)

            open_tab(1)
            open_each(ROWS, read_list, broken)
            open_tab(2)
            lists[LABELLED] = []
            open_each(ROWS, place(lists[LABELLED]), unread)
        finally:
            ctx.close()
    if not any(lists.values()):
        raise RuntimeError("read no places at all; Google Maps' page may have changed")
    return lists, unread, broken


# ---------- planning the HA side ----------

def wanted_zones(lists: dict[str, list[dict]], cfg: dict, home) -> list[dict]:
    """One zone per place; the same spot in several lists counts once, in the first: labelled places, then the
    lists in the order of the `icons` setting, then the rest by name. Places near HA's home are left to it."""
    rank = list(cfg["icons"])
    order = sorted(lists, key=lambda n: (n != LABELLED, rank.index(n) if n in rank else len(rank), n))
    out: list[dict] = []
    for name in order:
        icon = cfg["label_icon"] if name == LABELLED else cfg["icons"].get(name, cfg["default_icon"])
        for p in lists[name]:
            where = (p["lat"], p["lng"])
            if home and dist_m(where, home) < cfg["skip_near_home_m"]:
                continue
            if any(dist_m(where, (o["latitude"], o["longitude"])) < SAME_M or o["name"] == p["name"] for o in out):
                continue
            out.append({"name": p["name"], "latitude": round(p["lat"], 6), "longitude": round(p["lng"], 6),
                        "icon": cfg["icons"].get(p["name"], icon), "radius": cfg["radius"], "passive": False})
    return out


def plan(wanted: list[dict], zones: list[dict], owned: set[str], adopt: bool, protect=frozenset()) -> dict:
    """What to create, update and delete. Matching is by name; only owned zones are updated or deleted.
    adopt (first run): existing zones with a wanted name (or within ADOPT_M) become owned instead of duplicated.
    protect: names of places still saved but not located this time; their zones stay as they are."""
    by_name = {z["name"]: z for z in zones}
    create, update, skipped = [], [], []
    keep = {z["id"] for z in zones if z["name"] in protect and (z["id"] in owned or adopt)}
    for w in wanted:
        z = by_name.get(w["name"])
        if z is None and adopt:
            z = next((o for o in zones if o["id"] not in keep and o["name"] not in {x["name"] for x in wanted}
                      and dist_m((o["latitude"], o["longitude"]), (w["latitude"], w["longitude"])) < ADOPT_M), None)
        if z is None:
            create.append(w)
        elif z["id"] in owned or adopt:
            keep.add(z["id"])
            if any(abs(z[k] - v) > 1e-5 if k in ("latitude", "longitude") else z.get(k) != v
                   for k, v in w.items()):  # under ~1 m is rounding, not a move
                update.append({"zone_id": z["id"], **w})
        else:
            skipped.append(w["name"])  # a zone of the user's own has that name: leave it alone
    delete = sorted(i for i in owned if i not in keep and i in {z["id"] for z in zones})
    return {"create": create, "update": update, "delete": delete, "keep": keep, "skipped": skipped}


# ---------- talking to Home Assistant ----------

class HA:
    """Zones can only be edited over HA's websocket API; states and services go over REST."""

    def __init__(self, url: str, token: str):
        import websocket
        self.url, self.token, self.n = url.rstrip("/"), token, 0
        self.ws = websocket.create_connection(re.sub(r"^http", "ws", self.url) + "/api/websocket", timeout=30)
        self.ws.recv()
        self.ws.send(json.dumps({"type": "auth", "access_token": token}))
        if json.loads(self.ws.recv())["type"] != "auth_ok":
            raise RuntimeError("Home Assistant refused the token")

    def call(self, type_, **kw):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "type": type_, **kw}))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("id") == self.n and r.get("type") == "result":
                if not r["success"]:
                    raise RuntimeError(f"{type_}: {r['error'].get('message')}")
                return r["result"]

    def rest(self, path, body):
        requests.post(f"{self.url}/api/{path}", json=body, timeout=20,
                      headers={"Authorization": "Bearer " + self.token}).raise_for_status()

    def close(self):
        self.ws.close()


def token(cfg) -> str:
    t = os.environ.get(cfg["home_assistant"]["token_env"], "")
    if not t:
        sys.exit(f"set the environment variable {cfg['home_assistant']['token_env']} to a Home Assistant long-lived token")
    return t


def load_state(cfg) -> dict:
    try:
        return json.load(open(cfg["_state"], encoding="utf-8"))
    except FileNotFoundError:
        return {}


def save_state(cfg, s: dict) -> None:
    json.dump(s, open(cfg["_state"], "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def report(ha: HA, cfg: dict, state: str, attrs: dict, note: str = "") -> None:
    ha.rest(f"states/{cfg['sensor']}", {"state": state, "attributes": {
        "friendly_name": "Google Maps saved places", "icon": "mdi:map-marker-star", **attrs}})
    if note:
        ha.rest("services/persistent_notification/create",
                {"notification_id": "google_maps_zones", "title": "Google Maps → zones", "message": note})


def sync(cfg: dict, dry=False) -> dict:
    """Read Google Maps and bring HA's zones in line; report to HA (sensor, plus a notification on change/failure)."""
    st = load_state(cfg)
    when = datetime.now().astimezone().isoformat(timespec="seconds")
    connect = lambda: HA(cfg["home_assistant"]["url"], token(cfg))  # after reading: HA drops an idle websocket
    try:
        lists, unread, broken = read_saved(cfg)
        lists, unread = drop_excluded(lists, unread, cfg["exclude"])
        json.dump({"lists": lists, "unread": unread, "broken": broken}, open(cfg["_last_read"], "w", encoding="utf-8"),
                  indent=1, ensure_ascii=False)  # to check what was read without reading again
    except Exception as e:
        if not dry:
            ha = connect()
            report(ha, cfg, "error", {"last_try": when, "error": str(e)[:250], "last_sync": st.get("last_sync")},
                   f"Could not read Google Maps: {str(e)[:250]}")
            ha.close()
        raise
    ha = connect()
    try:
        conf, zones = ha.call("get_config"), ha.call("zone/list")
        p = plan(wanted_zones(lists, cfg, (conf["latitude"], conf["longitude"])), zones,
                 set(st.get("owned", [])), adopt="owned" not in st, protect=set(unread))
        held = p["delete"] if broken else []  # a list didn't load: what's in it is unknown, so delete nothing
        p["delete"] = [] if broken else p["delete"]
        counts = {k: len(p[k]) for k in ("create", "update", "delete")}
        log("lists:", {k: len(v) for k, v in lists.items()}, "changes:", counts, "skipped:", p["skipped"],
            "unread:", unread, "broken:", broken)
        if dry:
            return p
        owned = set(p["keep"]) | set(held)
        for z in p["create"]:
            owned.add(ha.call("zone/create", **z)["id"])
        for z in p["update"]:
            ha.call("zone/update", **z)
        for i in p["delete"]:
            ha.call("zone/delete", zone_id=i)
            owned.discard(i)
        st.update(owned=sorted(owned), last_sync=when)
        save_state(cfg, st)
        hit, names = excluder(cfg["exclude"]), {z["id"]: z["name"] for z in zones}
        gone = [names[i] for i in p["delete"]]
        hidden = sum(map(hit, gone))
        changes = [f"+ {z['name']}" for z in p["create"]] + [f"~ {z['name']}" for z in p["update"]] + \
                  [f"- {n}" for n in gone if not hit(n)] + \
                  ([f"- {hidden} excluded zone(s)"] if hidden else [])  # never name an excluded place
        note = ("Zone changes:\n" + "\n".join(changes[:40])) if changes else ""
        if broken:
            note += ("\n\n" if note else "") + "Lists that did not load (no zone was deleted): " + ", ".join(broken)
        report(ha, cfg, str(len(owned)), {"last_sync": when, "lists": {k: len(v) for k, v in lists.items()},
                                          "added": counts["create"], "updated": counts["update"],
                                          "removed": counts["delete"], "skipped": p["skipped"],
                                          "unread": unread, "broken": broken}, note)
        return p
    finally:
        ha.close()


def due(cfg: dict, st: dict, now: datetime, pressed: str | None) -> str:
    """Why a sync should run now ("button", "daily" or ""). Updates st. pressed: the button's state (the time it was
    last pressed); the first time it is seen it is only remembered."""
    why = ""
    if pressed is not None:
        if "button_seen" in st and pressed != st["button_seen"]:
            why = "button"
        st["button_seen"] = pressed
    today = now.date().isoformat()
    if cfg.get("daily_at") and now.strftime("%H:%M") >= cfg["daily_at"] and st.get("daily_done") != today:
        why, st["daily_done"] = why or "daily", today
    return why


def watch(cfg: dict) -> None:
    """Check every minute whether HA's button was pressed or the daily time has come, then sync."""
    log(f"watching {cfg['button'] or '(no button)'}, daily at {cfg.get('daily_at') or '(never)'}")
    while True:
        try:
            pressed = None
            if cfg["button"]:
                r = requests.get(f"{cfg['home_assistant']['url'].rstrip('/')}/api/states/{cfg['button']}", timeout=20,
                                 headers={"Authorization": "Bearer " + token(cfg)})
                pressed = r.json()["state"] if r.ok else None
            st = load_state(cfg)
            why = due(cfg, st, datetime.now(), pressed)
            save_state(cfg, st)
            if why:
                log("sync started by", why)
                sync(cfg)
        except Exception as e:  # HA restarting, Google page changed: say so and try again next time
            log("sync failed:", type(e).__name__, str(e)[:200])
        time.sleep(60)


def login(cfg: dict) -> None:
    """Open the profile in a normal (not automated) browser window at Google's sign-in page."""
    exe = cfg["browser"]["executable"] or next(
        (c for c in BROWSERS.get(cfg["browser"]["channel"], []) if os.path.isfile(c) or shutil.which(c)), "")
    if not exe:
        sys.exit("no browser found: set browser.executable in the settings")
    os.makedirs(cfg["profile"], exist_ok=True)
    subprocess.Popen([exe, f"--user-data-dir={cfg['profile']}", "--no-first-run",
                      "https://accounts.google.com/ServiceLogin?continue=https://www.google.com/maps"])
    print("Sign in to Google in the browser window that opened, then close it.")


if __name__ == "__main__":
    args = sys.argv[1:]
    path = args[args.index("--config") + 1] if "--config" in args else os.path.join(HERE, "gmaps_zones.json")
    config = load_config(path)
    if "--login" in args:
        login(config)
    elif "--watch" in args:
        watch(config)
    else:
        result = sync(config, dry="--dry" in args)
        print(json.dumps({k: (len(v) if k != "skipped" else v) for k, v in result.items()}, ensure_ascii=False))
