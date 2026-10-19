p = "/config/custom_components/notes_vault/frontend/notes-vault.js"
s = open(p, encoding="utf-8").read()
old = """${escapeHtml(label(note).replace(/^(\\d{4}-\\d{2}-\\d{2}) (.+)$/, "$2 · $1"))}"""
new = """${escapeHtml(newestFirst ? label(note) : label(note).replace(/^(\\d{4}-\\d{2}-\\d{2}) (.+)$/, "$2 · $1"))}"""
if "newestFirst ? label(note)" not in s:  # local patch: Historial keeps "2026-10-18 - Home Info" (date first)
    assert s.count(old) == 1, s.count(old)
    s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("patched historial date first")
