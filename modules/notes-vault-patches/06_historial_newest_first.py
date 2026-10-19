p = "/config/custom_components/notes_vault/frontend/notes-vault.js"
s = open(p, encoding="utf-8").read()
old = "    for (const note of files.sort((a, b) => label(a).localeCompare(label(b)))) {"
new = ("    const newestFirst = baseName(folder) === \"Historial\";  // local patch: history folders list the newest on top\n"
       "    for (const note of files.sort((a, b) => (newestFirst ? -1 : 1) * label(a).localeCompare(label(b)))) {")
if "history folders list the newest on top" not in s:
    assert s.count(old) == 1, s.count(old)
    s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("patched historial order")
