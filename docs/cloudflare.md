# Remote access with Cloudflare Tunnel + Access

A tunnel gives each app a public `https://app.example.com` without opening router ports. Cloudflare
Access in front of it asks for an email one-time code (or another login) before anything reaches your app.

## Pattern that works well

1. **One tunnel per server**, connector running on that server (`remote-access` module, host network).
   Route hostnames to `http://localhost:<port>` or LAN IPs. Keep Home Assistant's own hostname on the tunnel
   whose connector runs on the HA host, so HA stays reachable when another box is down.
2. **Order when adding a hostname:** create the Access application first, then the tunnel route, then the DNS
   record (proxied CNAME to `<tunnel-id>.cfargotunnel.com`). The hostname is never reachable unprotected.
3. **Admin UIs** (router, NAS, terminals, VNC): always behind Access. Their own login stays as a second layer.
4. **Pages embedded in Home Assistant iframes:**
   - give the Access app `SameSite=None` cookies, otherwise the frame loses the session;
   - sign in once per browser in a normal tab: the Access login page can't be shown inside a frame
     (the frame shows "refused to connect" until you do);
   - the app itself must allow framing: send `Content-Security-Policy: frame-ancestors 'self' https://your-ha`
     instead of `X-Frame-Options: DENY` (or proxy it, like `modules/omv-frame-proxy`).
5. **Session length:** long Access sessions (e.g. 730 h) for your own devices avoid frequent codes.

## Gotchas

- Free Universal SSL covers only one subdomain level: use `portainer-server1.example.com`, not
  `portainer.server1.example.com`.
- Some router web UIs (DD-WRT) reject saving settings when the request comes from another hostname
  (Referer check). Viewing works through the tunnel; save changes from the LAN if you hit "Bad Request".
