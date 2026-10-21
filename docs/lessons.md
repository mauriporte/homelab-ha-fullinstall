# Lessons learned (things that cost hours, so you don't have to)

## VPN
- **ProtonVPN free allows 2 simultaneous tunnels.** A 3rd connection silently kills the oldest one: the old
  client still says "connected/healthy" but passes no traffic (gluetun logs DNS-over-TLS timeouts).
- Free accounts get `AUTH_FAILED` on paid servers: set `FREE_ONLY=on` in gluetun.
- A server in an old `.ovpn` can stop accepting new connections while existing sessions keep working; it only
  shows up after a reconnect (TLS handshake timeout on every port). gluetun's built-in provider list avoids it.
- gluetun only uses the **first** `remote` of a custom `.ovpn`; UDP 5060 (SIP) is often intercepted by ISP routers.
- Bind qBittorrent to `tun0`: if the compose file is ever reset, it downloads nothing instead of leaking your IP.

## DD-WRT as a VPN access point
- After a reboot, DD-WRT (access-point mode, WAN disabled) can add `iptables -t raw -A PREROUTING -j NOTRACK`.
  Without connection tracking, NAT replies from the VPN never reach WiFi clients (the router itself still
  works, which is misleading). Fix in Administration → Commands → Save Firewall:
  `iptables -t raw -D PREROUTING -j NOTRACK 2>/dev/null`
- Its web UI fills certificates, keys and checkboxes with JavaScript: a script that re-submits a whole page
  wipes them. Send only the fields you change; DD-WRT keeps the rest.
- `apply.cgi` needs a `Referer` header from the router's own host, or it answers 400.

## Home Assistant dashboards
- **Equal-height columns** in a sections view: put the row in one full-width section and fix card heights with
  card-mod (`ha-card { height: …px }`). A `history-graph` only resizes when it sits directly in the grid, not
  inside a vertical/horizontal stack.
- A grid card with fixed `rows` gets a scrollbar when its content is taller; leave `rows` out so it grows.
- Cards in the same grid row stretch to the tallest one: wrap a group in a `vertical-stack` to avoid it.
- Collapsible groups: one `input_boolean` per group; the heading's tap toggles it; the cards below have a
  `state` visibility condition on it. Two chevron badges (up when on, down when off) make it obvious.
- Sidebar names of built-in panels can be changed with the `frontend/update_panel` WebSocket command.
- HA has no "read" state for notifications: copy each persistent notification into a To-do list (automation on
  the `persistent_notification` trigger) if you want a history after dismissing them.

## Embedding pages in HA iframes
- See `docs/cloudflare.md`. Typical blockers: `X-Frame-Options`, `SameSite=Strict` cookies, app-side
  "logged in" flags in `sessionStorage` (OMV), the Access login page refusing to be framed.

## Google Maps saved places (modules/google-maps-zones)
- No API: each saved list arrives in the page as one `maps/preview/entitylist/getlist` answer (with coordinates), but
  the **starred** list makes no such request: each place has to be opened and its pin read from the address.
- The pin is `!8m2!3d<lat>!4d<lng>`. Areas (a neighbourhood) carry other `!3d!4d` pairs, and the map centre (`@lat,lng`)
  is hundreds of km off while zoomed out: one zone landed in the Atlantic before this was fixed.
- Opening places by their position in the list breaks: going back re-renders it and only part of it is loaded until
  scrolled. Open them by name.
- A partial read looks exactly like "you unsaved these": only delete when every list loaded, and keep zones of places
  that were seen but couldn't be located.
- Google refuses sign-ins in automated browsers: sign in once in a normal window on the same profile, then automate.
  Browsers keep running in the background after that window closes and lock the profile.
- HA's map and Zones list hide passive zones, and HA drops an idle websocket during a minutes-long read (connect after).

## tvheadend / IPTV
- tvheadend's HTTP client fails on some ffmpeg-buffered streams; an IPTV network fed by a `pipe://ffmpeg …`
  playlist works. Keep that playlist in sync with the mux list, or a restart can drop every mux and service.
- Threadfin reads the buffer type **per playlist**; setting only the global buffer leaves it half-on.

## Servers
- Raspberry Pi: per-container RAM reads 0 until the memory cgroup is enabled (`cgroup_enable=memory
  cgroup_memory=1` in `/boot/firmware/cmdline.txt`).
- Broad `find /` on a low-memory host with network mounts can push it into swap death; scope your searches.
