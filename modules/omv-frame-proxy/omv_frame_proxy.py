#!/usr/bin/env python3
"""OMV frame proxy: the openmediavault web UI, always logged in, embeddable in a Home Assistant iframe.

Listens on 127.0.0.1 only: put it behind something that authenticates (e.g. a Cloudflare Tunnel + Access).
It keeps its own OMV session (login from the JSON file in $OMV_PROXY_CONFIG, root-only), so the frame is always logged in:
browser cookies are ignored, the UI's login request is answered with that session, and logout is a no-op.
It drops X-Frame-Options so Home Assistant can frame it.
"""
import http.client, http.server, json, os, threading, urllib.parse

CFG = json.load(open(os.environ.get("OMV_PROXY_CONFIG", "/etc/omv-frame-proxy/omv.json")))
UP = urllib.parse.urlsplit(CFG["upstream"])
PORT = int(CFG.get("port", 8097))
SKIP_REQ = {"connection", "keep-alive", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade",
            "host", "cookie", "content-length", "accept-encoding"}
SKIP_RESP = {"x-frame-options", "set-cookie", "connection", "keep-alive", "transfer-encoding", "content-length"}
# The workbench keeps its own "logged in" flag in sessionStorage; set it before the app starts so it skips #/login.
AUTOLOGIN = ("<script>sessionStorage.setItem('username'," + json.dumps(CFG["username"]) + ");"
             "sessionStorage.setItem('permissions','{\"role\":\"admin\"}');"
             "if(!location.hash||location.hash.indexOf('#/login')===0)location.hash='#/dashboard';</script>").encode()
lock = threading.Lock()
session = {"cookie": None}


def upstream(method, path, body=None, headers=None):
    c = http.client.HTTPConnection(UP.hostname, UP.port or 80, timeout=120)
    try:
        c.request(method, path, body=body, headers=headers or {})
        r = c.getresponse()
        return r.status, r.getheaders(), r.read()
    finally:
        c.close()


def login():
    body = json.dumps({"service": "Session", "method": "login",
                       "params": {"username": CFG["username"], "password": CFG["password"]}})
    status, headers, data = upstream("POST", "/rpc.php", body, {"Content-Type": "application/json"})
    cookies = [v.split(";")[0] for k, v in headers if k.lower() == "set-cookie"]
    if status != 200 or not cookies:
        raise RuntimeError(f"OMV login failed: HTTP {status}")
    session["cookie"] = "; ".join(cookies)
    return status, headers, data


def rpc_call(body):
    try:
        return json.loads(body or b"{}")
    except ValueError:
        return {}


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # quiet; systemd journal only gets errors
        pass

    def proxy(self):
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0)) or None
        call = rpc_call(body) if self.path.startswith("/rpc.php") else {}
        if call.get("service") == "Session" and call.get("method") == "logout":
            return self.reply(200, [("Content-Type", "application/json")], b'{"response":null,"error":null}')
        with lock:
            if call.get("service") == "Session" and call.get("method") == "login":
                return self.reply(*login())  # whatever was typed, the stored login is used
            if not session["cookie"]:
                login()
            cookie = session["cookie"]
        index = self.path.split("?")[0] in ("/", "/index.html")
        skip = SKIP_REQ | ({"if-none-match", "if-modified-since"} if index else set())  # index is always sent fresh
        headers = {k: v for k, v in self.headers.items() if k.lower() not in skip}
        headers["Cookie"] = cookie
        status, rh, data = upstream(self.command, self.path, body, headers)
        if status == 401:  # session expired: log in again and retry once
            with lock:
                login()
                headers["Cookie"] = session["cookie"]
            status, rh, data = upstream(self.command, self.path, body, headers)
        if index and b"<head>" in data:
            data = data.replace(b"<head>", b"<head>" + AUTOLOGIN, 1)
            rh = [(k, v) for k, v in rh if k.lower() not in ("etag", "last-modified")] + [("Cache-Control", "no-store")]
        self.reply(status, rh, data)

    def reply(self, status, headers, data):
        self.send_response(status)
        for k, v in headers:
            if k.lower() not in SKIP_RESP:
                self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = do_PATCH = do_OPTIONS = proxy


if __name__ == "__main__":
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
