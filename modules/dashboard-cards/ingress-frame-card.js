// custom:ingress-frame-card — shows a hass_ingress panel inside a dashboard (e.g. a terminal or any web app proxied by hass_ingress).
// The stock iframe card can't: hass_ingress needs its session cookie (asked for here over HA's own websocket,
// so HA's sign-in is the only sign-in) plus the panel's token in the URL.
let session = "", timer;
async function newSession(hass) {
  session = (await hass.callWS({ type: "ha-ingress/session" })).session;
  document.cookie = `ha_ingress_session=${session};path=/api/ingress/;SameSite=Strict${location.protocol === "https:" ? ";Secure" : ""}`;
}
class IngressFrameCard extends HTMLElement {
  setConfig(c) {
    if (!c.panel) throw new Error("ingress-frame-card: «panel» is required");
    this._c = c;
  }
  set hass(hass) {
    this._hass = hass;
    const token = hass.panels?.[this._c.panel]?.config?.token?.value;
    if (!token || this._token === token) return;
    if (this._token) return;  // keep the open terminal; a new token only matters on the next load
    this._token = token;
    this._open(hass, token);
  }
  async _open(hass, token) {
    await newSession(hass);
    timer ??= setInterval(async () => {  // keep the session alive while HA is open
      try { await this._hass.callWS({ type: "ha-ingress/validate_session", session }); } catch { await newSession(this._hass); }
    }, 60000);
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `<ha-card style="height:100%;overflow:hidden">
      <iframe src="/api/ingress/${token}/" style="border:0;width:100%;height:100%;display:block"
              allow="clipboard-read; clipboard-write"></iframe></ha-card>`;
  }
  getCardSize() { return 12; }
  getGridOptions() { return { columns: "full", rows: 15 }; }
}
customElements.define("ingress-frame-card", IngressFrameCard);
