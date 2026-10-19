D = "/config/custom_components/notes_vault/frontend/"

# A plain link to a vault file the watcher serves ([[report.pdf]]) opens that file in a new tab, instead of
# resolving to a (non-existent) note. Embeds (![[...]]) are handled by 01/04.
p = D + "notes-vault.js"
s = open(p, encoding="utf-8").read()
old = """  _resolveLink(target) {
    const inPanel = this._variant === "panel";"""
new = """  _resolveLink(target) {
    const served = globalThis.__nvImg?.(target.trim());  // local patch: vault file served by the PC
    if (served) return { href: served, label: fileName(target), exists: true };
    const inPanel = this._variant === "panel";"""
if "local patch: vault file served by the PC" not in s:
    assert s.count(old) == 1, "resolveLink"
    s = s.replace(old, new)
old = """      const shown = label || fileName(target);
      const link = links?.[target.trim()];"""
new = """      const shown = label || fileName(target);
      if (globalThis.__nvImg?.(target.trim())) return `[${shown}](${globalThis.__nvImg(target.trim())})`;  // local patch
      const link = links?.[target.trim()];"""
if "return `[${shown}](${globalThis.__nvImg" not in s:
    assert s.count(old) == 1, "card links"
    s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)

p = D + "editor.js"
s = open(p, encoding="utf-8").read()
old = ":new gs(u[1]?`\\u{1F5BC} ${b}`:b,g?.href||null,{unresolved:!g?.exists})"
new = ":new gs(u[1]?`\\u{1F5BC} ${b}`:b,g?.href||null,{unresolved:!g?.exists,external:/\\/vault-img\\//.test(g?.href||\"\")})"
if "external:/\\/vault-img" not in s:
    assert s.count(old) == 1, s.count(old)
    s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("patched file links")
