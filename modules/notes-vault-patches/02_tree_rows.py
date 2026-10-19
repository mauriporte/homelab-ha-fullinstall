p = "/config/custom_components/notes_vault/frontend/notes-vault.js"
s = open(p, encoding="utf-8").read()
css = """
  /* local patch: HA 2026.10 dropped ha-list/ha-list-item; draw the rows ourselves while they are undefined */
  ha-list:not(:defined) { display: block; padding: 4px 0; }
  ha-list-item:not(:defined) {
    display: flex; align-items: center; flex-wrap: wrap; column-gap: 12px; min-height: 36px;
    padding: 2px 12px 2px var(--mdc-list-side-padding-left, 16px); cursor: pointer; border-radius: 8px;
    line-height: 1.3; overflow-wrap: anywhere;
  }
  ha-list-item:not(:defined):hover { background: var(--secondary-background-color); }
  ha-list-item:not(:defined)[activated] { background: rgba(var(--rgb-primary-color), 0.15); color: var(--primary-color); }
  ha-list-item:not(:defined) > ha-icon { flex: none; --mdc-icon-size: 20px; color: var(--secondary-text-color); }
  ha-list-item:not(:defined) > [slot="secondary"] { flex-basis: 100%; padding-left: 32px; font-size: 12px; color: var(--secondary-text-color); }
"""
if "local patch: HA 2026.10 dropped" not in s:
    anchor = "  ha-list-item { --mdc-list-item-graphic-margin: 16px; }\n"
    assert s.count(anchor) == 1
    s = s.replace(anchor, anchor + css, 1)
    a2 = "const STYLE = `\n"  # the cards' style (linked mentions use ha-list too)
    assert s.count(a2) == 1
    s = s.replace(a2, a2 + css.lstrip("\n"), 1)
open(p, "w", encoding="utf-8").write(s)
print("patched")
