import os

D = "/config/custom_components/notes_vault/frontend/"

# An Instagram reel link in a note (/reel/ or /tv/; /p/ is usually a photo) keeps the link and gets a
# «▶ Ver reel» button that plays the video inline. The video comes from vault_files_server.py
# (/vault-img/<key>/reel/<code>, resolved with yt-dlp, no Instagram login), like the notes' pictures (patch 01).
p = D + "editor.js"
s = open(p, encoding="utf-8").read()
old = "return g?(o.push(I.replace({widget:new gs(g[1]||g[2],g[2]"
new = ("{let ig=g&&/^https?:\\/\\/(?:www\\.)?instagram\\.com\\/(?:[\\w.]+\\/)?(?:reels?|tv)\\/([\\w-]{5,})/i.exec(g[2]);"
       "let vi=document.querySelector(\"home-assistant\")?.hass?.states?.[\"sensor.vault_images\"]?.attributes;"
       "if(ig&&vi?.key){o.push(I.replace({widget:new(globalThis.__nvReelW??=class extends ue{"
       "constructor(l,h,c,s){super(),this.l=l,this.h=h,this.c=c,this.s=s}"
       "eq(e){return e.h===this.h&&e.l===this.l}"
       "toDOM(){let w=document.createElement(\"span\"),a=document.createElement(\"a\"),b=document.createElement(\"button\");"
       "a.href=this.h;a.target=\"_blank\";a.rel=\"noopener noreferrer\";a.textContent=this.l;"
       "b.textContent=\"\\u25B6 Ver reel\";b.style.cssText=\"margin-left:8px;font:inherit;font-size:13px;padding:2px 10px;border-radius:6px;border:none;cursor:pointer;color:var(--text-primary-color,#fff);background:var(--primary-color)\";"
       "b.addEventListener(\"click\",()=>{let v=document.createElement(\"video\");v.controls=v.autoplay=v.playsInline=true;v.src=this.s;"
       "v.style.cssText=\"display:block;max-width:360px;max-height:560px;border-radius:8px;margin:6px 0;background:#000\";"
       "v.addEventListener(\"error\",()=>{v.replaceWith(document.createTextNode(\" (no se pudo reproducir: \\u00bfcuenta privada?)\"))},{once:true});"
       "w.append(v);b.remove()},{once:true});w.append(a,b);return w}"
       "ignoreEvent(){return!0}})(g[1]||g[2],g[2],ig[1],(location.protocol===\"https:\"?\"\":vi.lan||\"\")+\"/vault-img/\"+encodeURIComponent(vi.key)+\"/reel/\"+encodeURIComponent(ig[1]))}).range(u.from,u.to));return!1}}"
       + old)
a = s.find("{let ig=g&&")
if a != -1:  # an earlier version of this patch: take it out first
    s = s[:a] + s[s.index("return!1}}", a) + len("return!1}}"):]  # only this patch's own block
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
os.utime(D + "notes-vault.js")  # editor.js is loaded with notes-vault.js's ?v=<mtime>
print("patched reel player")
