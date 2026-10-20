D = "/config/custom_components/notes_vault/frontend/"

# A Google Maps link in a note is shown as a
# «🗺 Ver mapa» button (the link text was redundant next to it) that shows Google's keyless map embed under it. Full links say the place themselves (same
# rules as vault_files_server.py maps_embed_url); share links (maps.app.goo.gl) go through
# vault_files_server.py: /vault-img/<key>/maps?u= (it follows the short link once). Nothing loads until tapped.
import os

p = D + "editor.js"
s = open(p, encoding="utf-8").read()
old = "return g?(o.push(I.replace({widget:new gs(g[1]||g[2],g[2]"
new = ("{let gm=g&&/^https?:\\/\\/(?:(?:www\\.|maps\\.)?google\\.[a-z.]+\\/maps|maps\\.google\\.[a-z.]+\\/|maps\\.app\\.goo\\.gl\\/|goo\\.gl\\/maps\\/)/i.test(g[2]),em=\"\";"
       "if(gm){let vi=document.querySelector(\"home-assistant\")?.hass?.states?.[\"sensor.vault_images\"]?.attributes;"
       "if(/goo\\.gl/i.test(g[2])){if(vi?.key)em=(location.protocol===\"https:\"?\"\":vi.lan||\"\")+\"/vault-img/\"+encodeURIComponent(vi.key)+\"/maps?u=\"+encodeURIComponent(g[2].split(\"?\")[0])}"
       "else{try{let x=new URL(g[2]),c=x.pathname.match(/@(-?\\d+\\.\\d+),(-?\\d+\\.\\d+)(?:,(\\d+(?:\\.\\d+)?)z)?/),pl=x.pathname.match(/\\/maps\\/(?:place|search)\\/([^/@]+)/),"
       "q=x.searchParams.get(\"query\")||x.searchParams.get(\"q\")||(pl?decodeURIComponent(pl[1].replace(/\\+/g,\" \")):\"\")||(c?c[1]+\",\"+c[2]:\"\");"
       "if(q&&!/\\/maps\\/dir\\//.test(x.pathname))em=\"https://maps.google.com/maps?q=\"+encodeURIComponent(q)+\"&z=\"+(c&&c[3]?Math.round(+c[3]):15)+\"&output=embed\"}catch(e){}}}"
       "if(em){o.push(I.replace({widget:new(globalThis.__nvMapW??=class extends ue{"
       "constructor(l,h,s){super(),this.l=l,this.h=h,this.s=s}"
       "eq(e){return e.h===this.h&&e.l===this.l}"
       "toDOM(){let w=document.createElement(\"span\"),a=document.createElement(\"a\"),b=document.createElement(\"button\");"
       "a.href=this.h;a.target=\"_blank\";a.rel=\"noopener noreferrer\";a.textContent=this.l;"
       "b.textContent=\"\\u{1F5FA} Ver mapa\";b.style.cssText=\"margin-left:8px;font:inherit;font-size:13px;padding:2px 10px;border-radius:6px;border:none;cursor:pointer;color:var(--text-primary-color,#fff);background:var(--primary-color)\";"
       "b.addEventListener(\"click\",()=>{let f=document.createElement(\"iframe\");f.src=this.s;f.loading=\"lazy\";"
       "f.setAttribute(\"sandbox\",\"allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox\");"
       "f.style.cssText=\"display:block;width:100%;max-width:520px;height:300px;border:0;border-radius:8px;margin:6px 0\";"
       "w.append(f);b.remove()},{once:true});w.append(b);return w}"
       "ignoreEvent(){return!0}})(g[1]||g[2],g[2],em)}).range(u.from,u.to));return!1}}"
       + old)
a = s.find("{let gm=g&&")
if a != -1:  # an earlier version of this patch: take it out first
    s = s[:a] + s[s.index("return!1}}", a) + len("return!1}}"):]  # only this patch's own block
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
os.utime(D + "notes-vault.js")  # editor.js is loaded with notes-vault.js's ?v=<mtime>
print("patched map preview")
