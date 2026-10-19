D = "/config/custom_components/notes_vault/frontend/"

# notes-vault.js: one helper for the image URL (also used by editor.js), cards use it
p = D + "notes-vault.js"
s = open(p, encoding="utf-8").read()
end = s.index("      return `*${label || fileName(target)}*`;")
start = s.find("      // local patch: vault images")
start = end if start < 0 or start > end else start  # fresh file: insert right before the return
s = s[:start] + r"""      // local patch: vault images come from the vault file server (vault_files_server.py)
      if (globalThis.__nvImg?.(target.trim())) return `![${fileName(target)}](${globalThis.__nvImg(target.trim())})`;
""" + s[end:]
helper = r"""
// local patch: URL of a vault file, served by vault_files_server.py; the key is in an HA sensor
globalThis.__nvImg = (target) => {
  if (!/\.(png|jpe?g|gif|webp)$/i.test(target)) return null;
  const img = document.querySelector("home-assistant")?.hass?.states?.["sensor.vault_images"]?.attributes;
  if (!img?.key) return null;
  const base = location.protocol === "https:" ? "" : img.lan;
  return `${base}/vault-img/${img.key}/${target.split("/").map(encodeURIComponent).join("/")}`;
};
"""
if "globalThis.__nvImg = " not in s:
    anchor = "const renderWikilinks = "
    s = s.replace(anchor, helper.lstrip("\n") + "\n" + anchor, 1)
open(p, "w", encoding="utf-8").write(s)

# editor.js: an image embed becomes an <img> widget instead of a "🖼 label" link
p = D + "editor.js"
s = open(p, encoding="utf-8").read()
old = "o.push(I.replace({widget:new gs(u[1]?`\\u{1F5BC} ${b}`:b,g?.href||null,{unresolved:!g?.exists})}).range(d,p))"
new = ("o.push(I.replace({widget:u[1]&&globalThis.__nvImg?.(m)?new(globalThis.__nvImgW??=class extends gs{toDOM(){"
       "let e=document.createElement(\"img\");e.src=this.href;e.alt=this.label;e.style.cssText=\"display:block;max-width:100%;max-height:500px;border-radius:8px;margin:4px 0\";return e}})"
       "(b,globalThis.__nvImg(m)):new gs(u[1]?`\\u{1F5BC} ${b}`:b,g?.href||null,{unresolved:!g?.exists})}).range(d,p))")
if "__nvImgW" not in s:
    assert s.count(old) == 1, s.count(old)
    s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("patched both")
