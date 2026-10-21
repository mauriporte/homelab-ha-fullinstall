# Google Maps zones

Keeps one **Home Assistant zone** per place saved in **Google Maps**: every list (Want to go, Favorites, your own),
the starred places and the labelled ones (Home, Work…). New saves are added, moved or renamed places updated,
unsaved ones removed. The zones show on HA's map and its Zones list, and people's state becomes the place's name
while they are there.

It runs on a computer with a desktop and Chrome or Edge (Windows or Linux), not in Docker: Google has no API for
saved lists, so it reads the Google Maps web page itself, in a hidden browser on its own profile
([Playwright](https://playwright.dev/python/)).

## What it does and doesn't touch

- It only changes zones it created, listed in `gmaps_zones-state.json`. Zones you make yourself are never edited or
  deleted; if one has the same name as a saved place, that place is skipped.
- On its **first** run it takes over existing zones with the same name (or within 10 m), so zones you already made
  from the same places aren't duplicated.
- A place it sees in a list but can't locate (an area with no pin, a slow page) **keeps its zone**. If a whole list
  fails to load, **nothing is deleted** that run. If the page can't be read at all, nothing changes and HA says why.
- The same spot saved in several lists becomes one zone, with the icon of the first list in `icons` that has it
  (that order is the priority). Places near HA's home are left to the home zone.
- `exclude`: patterns (case-insensitive, regular expressions) matched against each place's name and address, e.g.
  an old home street. Those places never become zones and never appear in the sensor, notifications or
  `gmaps_zones-last-read.json`; zones made for them earlier are deleted.

## Install

```bash
cd modules/google-maps-zones
python3 -m venv venv && venv/bin/pip install -r requirements.txt     # Windows: venv\Scripts\pip
cp gmaps_zones.example.json gmaps_zones.json                          # then edit it (never committed)
```

- `home_assistant.url`; the token is **not** in the file: put a long-lived token (HA profile → Security) in the
  environment variable named in `home_assistant.token_env` (default `HA_TOKEN`).
- `browser.channel`: `msedge` or `chrome` (an installed browser, no download), or `chromium` after
  `venv/bin/playwright install chromium`. `browser.executable` only if `--login` can't find it.
- `locale`: the Google Maps language. List names come in your account's language either way; use those names in
  `icons` (they're in the sensor's `lists` attribute after the first run).
- In HA, create the button: Settings → Devices & services → Helpers → Create helper → Button, named so its entity
  is `button` (default `input_button.sync_google_maps`).

Sign in once (a normal browser window opens on the tool's own profile; sign in, then close it):

```bash
venv/bin/python gmaps_zones.py --login
venv/bin/python gmaps_zones.py --dry     # read and show what would change (takes a few minutes)
venv/bin/python gmaps_zones.py           # sync now
```

Keep it running so HA's button and the daily sync (`daily_at`) work: `gmaps_zones.py --watch`.

- **Linux:** `gmaps-zones.service` is a systemd user service. Put `HA_TOKEN=...` in `~/.config/gmaps-zones.env`
  (`chmod 600`), copy the unit to `~/.config/systemd/user/`, then `systemctl --user enable --now gmaps-zones`
  (and `loginctl enable-linger $USER` so it runs without a login).
- **Windows:** a Task Scheduler task at logon running `venv\Scripts\pythonw.exe gmaps_zones.py --watch` in this
  folder, with `HA_TOKEN` set as a user environment variable.

## In Home Assistant

- `sensor.google_maps_places` (the `sensor` setting): number of zones it keeps; attributes `last_sync`, `lists`
  (places per list), `added`, `updated`, `removed`, `skipped`, `unread`, `broken`; `error` when reading failed.
- A persistent notification `google_maps_zones` when zones changed, a list didn't load, or reading failed.

A card for a dashboard:

```yaml
type: vertical-stack
cards:
  - type: tile
    entity: input_button.sync_google_maps
    name: Sync now
    icon: mdi:sync
    hide_state: true
    tap_action: {action: perform-action, perform_action: input_button.press, target: {entity_id: input_button.sync_google_maps}}
  - type: markdown
    content: >-
      {% set s = 'sensor.google_maps_places' %}
      **{{ states(s) }} zones**, last sync {{ state_attr(s, 'last_sync') }}
      {% if state_attr(s, 'unread') %}<br>Not locatable (kept): {{ state_attr(s, 'unread') | join(', ') }}{% endif %}
```

## Good to know

- Reading takes about 3 minutes for ~70 places: lists come from the page's own data, but starred and labelled
  places are opened one by one to read their pin from the address.
- Google can change its page at any time; the sync then fails loudly and changes nothing. The sign-in can also
  expire: run `--login` again.
- HA's map hides *passive* zones, so the zones are normal ones: a person inside one shows that place's name instead
  of `not_home`. Check automations that test for `not_home` before using it.
- `gmaps_zones-last-read.json` holds what the last run read, to check a result without reading again. It contains
  your places: keep it (and the profile folder, which holds your Google sign-in) private.

Tests: `venv/bin/python -m pytest test_gmaps_zones.py`
