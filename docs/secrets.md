# Secrets with sops + age

Passwords and tokens never go into git in plain text. They live in `secrets.enc.env`, encrypted with
[sops](https://github.com/getsops/sops) using an [age](https://github.com/FiloSottile/age) key. Only the
encrypted file is committed; `install.sh` decrypts it to `.secrets.env` (git-ignored) when it runs.

## One-time setup

```bash
# 1. Tools (Debian/Ubuntu; or download the release binaries)
sudo apt install age
# sops: download the binary for your architecture from https://github.com/getsops/sops/releases, then
sudo install -m 755 sops-v*.linux.* /usr/local/bin/sops

# 2. Your key. Keep a copy of this file in your password manager: without it the secrets are gone.
mkdir -p ~/.config/sops/age && age-keygen -o ~/.config/sops/age/keys.txt
grep 'public key' ~/.config/sops/age/keys.txt      # → age1…

# 3. Put that public key in .sops.yaml (replace the placeholder)
```

## Everyday use

```bash
cp secrets.example.env secrets.env      # fill in the real values
sops --encrypt --input-type dotenv --output-type dotenv secrets.env > secrets.enc.env
rm secrets.env                          # only the encrypted file stays
sops secrets.enc.env                    # later: edit in place (decrypts in your editor, re-encrypts on save)
```

Values in `secrets.enc.env` override the same names in `.env`.

## On a new server

Copy `~/.config/sops/age/keys.txt` from your password manager to the same path, clone the repo, run
`./install.sh`. Nothing else is needed to get every secret back.
