"""Pre-commit secret guard: refuses a commit whose staged files hold a plaintext secret, in any repo, private or public.

Run by tools/pre-commit (install for every repo: copy both files to a folder and `git config --global core.hooksPath <folder>`). Scans only what is being committed
(the staged version of each added/changed file). Skips binary files and sops-encrypted files (*.enc, *.enc.*).
A false positive can be allowed per repo with path globs, one per line, in .secretguard-allow at the repo root.
`python secret_guard.py --self-test` checks the patterns.
"""
import fnmatch, os, re, subprocess, sys

PATTERNS = [
    ("private key", re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")),
    ("JWT / OAuth token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("Microsoft refresh token", re.compile(r"\b[01]\.A[A-Za-z0-9_-]{100,}")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("Cloudflare / API token", re.compile(r"\b(?:bdapi|sk|xox[bap])[-_][A-Za-z0-9_-]{20,}")),
    ("age secret key", re.compile(r"AGE-SECRET-KEY-1[0-9A-Z]{50,}")),
    ("Telegram bot token", re.compile(r"\b\d{8,10}:AA[A-Za-z0-9_-]{30,}")),
    ("secret value", re.compile(
        r"""(?ix)["']?(?:refresh_?token|access_?token|client_?secret|secret|password|passwd|api_?key|apikey|auth_?token|token
        |sessionid|private_?key)["']?\s*[:=]\s*["']?(?P<v>[^\s"',}{]{16,})""")),
]
PLACEHOLDER = re.compile(r"^(\{\{|\$\{?|<|%|ENC\[|!secret|example|change|your|xxx|\*{3})|example|placeholder|changeme|dummy",
                         re.I)


#: Code, not a value: calls, indexing, attribute access (name.attr), URLs
CODE = re.compile(r"[()\[\]]|^[A-Za-z_]\w*\.[A-Za-z_]|^(https?:|(self|this|process|os|env|cfg|config|headers|data|args|kw|opts)\b)",
                  re.I)


def suspicious(text):
    """(line number, kind, redacted snippet) for each secret-looking match."""
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        for kind, rx in PATTERNS:
            for m in rx.finditer(line):
                v = m.groupdict().get("v") or m.group(0)
                if kind == "secret value" and (PLACEHOLDER.search(v) or CODE.search(v)
                                               or not (re.search(r"\d", v) and re.search(r"[A-Za-z]", v))):
                    continue  # templates, placeholders, code expressions, words: not a secret
                hits.append((n, kind, v[:4] + "…" + f"({len(v)} chars)"))
    return hits


def git(*a):
    return subprocess.run(["git", *a], capture_output=True)


def main():
    root = git("rev-parse", "--show-toplevel").stdout.decode().strip()
    allow_file = os.path.join(root, ".secretguard-allow")
    allow = [l.strip() for l in open(allow_file, encoding="utf-8") if l.strip() and not l.startswith("#")] \
        if os.path.exists(allow_file) else []
    files = git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z").stdout.decode().split("\0")
    found = []
    for f in filter(None, files):
        if re.search(r"\.enc(\.|$)", f) or any(fnmatch.fnmatch(f, g) for g in allow):
            continue
        blob = git("show", f":{f}").stdout
        if b"\0" in blob[:8000]:
            continue  # binary
        found += [(f, *h) for h in suspicious(blob.decode("utf-8", "replace"))]
    if found:
        print("secret_guard: COMMIT BLOCKED - plaintext secrets in staged files:", file=sys.stderr)
        for f, n, kind, snip in found[:50]:
            print(f"  {f}:{n}  {kind}  {snip}", file=sys.stderr)
        print("Encrypt them (sops) or keep them out of git. A false positive: add its path to .secretguard-allow.",
              file=sys.stderr)
        sys.exit(1)


def self_test():
    j = lambda *parts: "".join(parts)  # samples are assembled at run time, so no scanner sees a secret in this file
    bad = [j('"refresh_', 'token": "0.AXkA', 'abc123def456ghi789jkl"'), j("pass", "word: S3cr3t", "Passw0rd!xyz"),
           j("Authorization: Bearer ey", "JhbGciOiJIUzI1NiJ9.ey", "JzdWIiOiIxMjM0NTY3ODkwIn0.abcdefghijk123"),
           j("-----BEGIN OPENSSH PRI", "VATE KEY-----"), j('"beeper_token": "bd', 'api_FAKEfakeFAKE', 'fakeFAKEfake0123456789"'),
           j("token = gh", "p_abcdefghijklmnop", "qrstuvwxyz0123456789")]
    good = ['password: "{{ password | default(\'\') }}"', "password: !secret router_password",
            '"password": CFG["password"]', "api_key: ENC[AES256_GCM,data:abc123def456ghi789]",
            "token = headers_get_token(req)", "secret: self.client_secret_value", "url = 'https://x.y/token=1'",
            "token: your-token-here-123456", "# the refresh token is kept in the keyring"]
    for s in bad:
        assert suspicious(s), f"missed: {s}"
    for s in good:
        assert not suspicious(s), f"false positive: {s}"
    print("self-test ok")


if __name__ == "__main__":
    self_test() if "--self-test" in sys.argv else main()
