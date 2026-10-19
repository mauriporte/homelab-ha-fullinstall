D = "/config/custom_components/notes_vault/frontend/"

# notes-vault.js: the helper also gives URLs for HTML/PDF; cards show those as a link (ha-markdown drops iframes)
p = D + "notes-vault.js"
s = open(p, encoding="utf-8").read()
s = s.replace(r"if (!/\.(png|jpe?g|gif|webp)$/i.test(target)) return null;",
              r"if (!/\.(png|jpe?g|gif|webp|html|pdf)$/i.test(target)) return null;")
old = "      if (globalThis.__nvImg?.(target.trim())) return `![${fileName(target)}](${globalThis.__nvImg(target.trim())})`;"
new = ("      if (globalThis.__nvImg?.(target.trim())) return /\\.(html|pdf)$/i.test(target.trim())\n"
       "        ? `[📄 ${fileName(target)}](${globalThis.__nvImg(target.trim())})`\n"
       "        : `![${fileName(target)}](${globalThis.__nvImg(target.trim())})`;")
if "📄 ${fileName(target)}" not in s:
    assert s.count(old) == 1, "card branch"
    s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)

# editor.js: in the Notes page an HTML/PDF embed is shown inline in a sandboxed frame, with a link to open it full size
p = D + "editor.js"
s = open(p, encoding="utf-8").read()
old = ('let e=document.createElement("img");e.src=this.href;e.alt=this.label;'
       'e.style.cssText="display:block;max-width:100%;max-height:500px;border-radius:8px;margin:4px 0";return e')
new = ('if(/\\.(html|pdf)(\\?|$)/i.test(this.href)){let w=document.createElement("div"),a=document.createElement("a"),f=document.createElement("iframe");'
       'let u=this.href+"?t="+Date.now();a.href=u;a.target="_blank";a.rel="noopener";a.textContent="Abrir en pestaña nueva";'
       'f.src=u;f.setAttribute("sandbox","allow-popups allow-popups-to-escape-sandbox");'
       'f.style.cssText="display:block;width:100%;height:80vh;border:1px solid var(--divider-color);border-radius:8px;margin:4px 0;background:#fff";'
       'w.append(a,f);return w}' + old)
if "Abrir en pestaña nueva" not in s:
    assert s.count(old) == 1, "editor widget"
    s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("patched html embeds")
