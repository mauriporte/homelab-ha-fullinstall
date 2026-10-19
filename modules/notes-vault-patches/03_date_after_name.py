p = "/config/custom_components/notes_vault/frontend/notes-vault.js"
s = open(p, encoding="utf-8").read()
old = """          <ha-icon slot="graphic" icon="mdi:file-document-outline"></ha-icon>
          ${escapeHtml(label(note))}"""
new = """          <ha-icon slot="graphic" icon="mdi:file-document-outline"></ha-icon>
          ${escapeHtml(label(note).replace(/^(\d{4}-\d{2}-\d{2}) (.+)$/, "$2 · $1"))}"""
if "$2 · $1" not in s:
    assert s.count(old) == 1, s.count(old)
    s = s.replace(old, new)  # local patch: in the tree, "2026-10-19 Name" shows as "Name · 2026-10-19" (order unchanged)
open(p, "w", encoding="utf-8").write(s)
print("patched")
