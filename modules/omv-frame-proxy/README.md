# OMV frame proxy

Shows the **openmediavault** web UI inside a Home Assistant iframe card, **already logged in**.

OMV can't be framed as-is: it sends `X-Frame-Options: SAMEORIGIN`, its session cookie is `SameSite=Strict`,
and the OMV 7 workbench keeps its own "logged in" flag in the tab's `sessionStorage`. This small proxy
(Python standard library only):

- keeps its own OMV session (browser cookies are ignored, logout is a no-op, it logs in again on 401);
- answers the UI's login request with that session, whatever is typed;
- removes `X-Frame-Options`;
- sets the workbench's `sessionStorage` flag on page load, so it opens on the dashboard.

**It listens on `127.0.0.1` only and gives admin access to whoever reaches it.** Put it behind something that
authenticates, e.g. a Cloudflare Tunnel on the same host with a Cloudflare Access application (see
`docs/cloudflare.md`). Never publish the port on your LAN.

## Install (on any Linux host that can reach OMV; Python 3)

```bash
sudo install -m 755 omv_frame_proxy.py /opt/omv_frame_proxy.py
sudo mkdir -p /etc/omv-frame-proxy && sudo chmod 700 /etc/omv-frame-proxy
sudo tee /etc/omv-frame-proxy/omv.json >/dev/null <<'EOF'
{"upstream": "http://OMV-IP", "username": "admin", "password": "OMV-PASSWORD", "port": 8097}
EOF
sudo chmod 600 /etc/omv-frame-proxy/omv.json
sudo install -m 644 omv-frame-proxy.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now omv-frame-proxy
```

Then route a hostname to `http://127.0.0.1:8097` (Cloudflare Tunnel ingress) behind Access, and add a
Home Assistant iframe card pointing at it. Sign in to Access once in a normal tab per browser (Access's
login page itself can't be framed); give the Access app `SameSite=None` cookies so the frame keeps the session.
