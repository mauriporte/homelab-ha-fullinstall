p = "/config/custom_components/notes_vault/frontend/editor.js"
s = open(p, encoding="utf-8").read()
old = 'w.append(a,f);return w}'
new = ('w.append(a,f);'
       # local patch: ![[report.html|abierto: title]] / |plegado: title -> a collapsible section (open or folded)
       'let k=/^(abierto|plegado):\\s*(.*)$/.exec(this.label||"");'
       'if(k){let D=document.createElement("details"),S=document.createElement("summary");'
       'S.textContent=k[2];S.style.cssText="cursor:pointer;font-weight:600;font-size:1.15em;margin:8px 0";'
       'D.open=k[1]==="abierto";D.append(S,w);return D}'
       'return w}')
if "abierto|plegado" not in s:
    assert s.count(old) == 1, s.count(old)
    s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("patched collapsible reports")
