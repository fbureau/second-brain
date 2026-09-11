#!/usr/bin/env bash
#
# One-command setup for the Second Brain on Hermes Agent (Desktop or CLI).
#
#   ./hermes/setup.sh                      # vault at ~/second-brain
#   ./hermes/setup.sh ~/notes/my-vault     # vault somewhere else
#
# Unlike install.sh, this asks nothing and assumes nothing: it creates the vault if it
# is missing, initialises git, links the plugin, and WRITES the configuration itself so
# there is nothing left to copy-paste. Safe to re-run.
set -euo pipefail

vault="${1:-$HOME/second-brain}"
hermes_home="${HERMES_HOME:-$HOME/.hermes}"
repo="$(cd "$(dirname "$0")/.." && pwd)"

step() { printf '\n\033[1m%s\033[0m\n' "$*"; }
ok()   { printf '  ✓ %s\n' "$*"; }
warn() { printf '  ! %s\n' "$*"; }

# ---------------------------------------------------------------- 1. the vault
step "1/5  Vault"
if [[ -f "$vault/_CLAUDE.md" ]]; then
  ok "already there: $vault"
else
  mkdir -p "$(dirname "$vault")"
  cp -R "$repo/vault-starter" "$vault"
  ok "created from the starter: $vault"
fi
vault="$(cd "$vault" && pwd)"          # absolute, now that it exists

if git -C "$vault" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  ok "git repository already initialised"
else
  git -C "$vault" init -q
  git -C "$vault" add -A
  git -C "$vault" -c user.email=you@example.com -c user.name="Second Brain" \
      commit -qm "Initial vault" --no-verify
  ok "git initialised, first commit made"
fi

"$repo/hooks/install.sh" "$vault" >/dev/null 2>&1 && ok "pre-commit hook installed (it enforces the note rules)" \
  || warn "pre-commit hook not installed — run hooks/install.sh \"$vault\" by hand"

# ---------------------------------------------------------------- 2. hermes home
step "2/5  Hermes home"
if [[ -d "$hermes_home" ]]; then
  ok "found: $hermes_home"
else
  mkdir -p "$hermes_home"
  ok "created: $hermes_home"
fi
mkdir -p "$hermes_home/plugins" "$hermes_home/skills" "$hermes_home/memories"

# ---------------------------------------------------------------- 3. the plugin
step "3/5  Plugin, skills and memory provider"
link() {
  if [[ -L "$2" || ! -e "$2" ]]; then ln -sfn "$1" "$2"; ok "$(basename "$2")"
  else warn "$2 exists and is not a link — left untouched"; fi
}
link "$repo/hermes/plugin/second_brain" "$hermes_home/plugins/second_brain"
link "$repo/hermes/memory/sb_vault"     "$hermes_home/plugins/sb_vault"
link "$repo/hermes/plugin/second_brain/skills"  "$hermes_home/skills/second-brain"

if [[ -f "$hermes_home/SOUL.md" ]]; then
  warn "SOUL.md already exists — merge hermes/SOUL.md into it if you want the second-brain identity"
else
  cp "$repo/hermes/SOUL.md" "$hermes_home/SOUL.md"; ok "SOUL.md"
fi

lang="$(grep -oE 'Working language\*\*: `?[a-z]{2}' "$vault/00-inbox/MY-PROFILE.md" 2>/dev/null | grep -oE '[a-z]{2}$' || echo en)"
if [[ ! -f "$hermes_home/memories/USER.md" ]]; then
  sed -e "s#__VAULT_PATH__#$vault#" -e "s#__LANG__#$lang#" \
      "$repo/hermes/memories/USER.md.example" > "$hermes_home/memories/USER.md"
  ok "memories/USER.md (language: $lang)"
fi

grep -qs '^SECOND_BRAIN_VAULT=' "$hermes_home/.env" 2>/dev/null \
  || { printf 'SECOND_BRAIN_VAULT=%s\n' "$vault" >> "$hermes_home/.env"; ok ".env"; }

# ---------------------------------------------------------------- 4. config.yaml
step "4/5  Configuration"
cfg="$hermes_home/config.yaml"
snippet="$hermes_home/second-brain-config-snippet.yaml"
cat > "$snippet" <<YAML
plugins:
  entries:
    second_brain:
      settings:
        vault_path: "$vault"
terminal:
  cwd: "$vault"
YAML

python3 - "$cfg" "$vault" "$hermes_home" <<'PY' || warn "could not edit config.yaml automatically — paste $snippet into it by hand"
import shutil, sys, os
cfg, vault, home = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    import yaml
except ImportError:
    sys.exit(1)
data = {}
if os.path.exists(cfg):
    shutil.copy(cfg, cfg + ".backup-second-brain")
    with open(cfg, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
data.setdefault("plugins", {}).setdefault("entries", {}).setdefault("second_brain", {}) \
    .setdefault("settings", {})["vault_path"] = vault
data.setdefault("terminal", {})["cwd"] = vault
with open(cfg, "w", encoding="utf-8") as f:
    yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
print("  ✓ config.yaml written" + (" (backup: config.yaml.backup-second-brain)" if os.path.exists(cfg + ".backup-second-brain") else ""))
PY

# ---------------------------------------------------------------- 5. self-check
step "5/5  Check"
python3 - "$vault" "$repo" <<'PY'
import sys, pathlib
vault, repo = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
sys.path.insert(0, str(repo / "hermes" / "plugin"))
import os
os.environ["SECOND_BRAIN_VAULT"] = str(vault)
try:
    from second_brain.vault import Vault
    from second_brain import schemas
    v = Vault.locate()
    print(f"  ✓ the plugin can read the vault ({len(schemas.ALL_VAULT)} tools, language: {v.working_language()})")
except Exception as e:
    print(f"  ! the plugin could NOT read the vault: {e}")
    sys.exit(1)
PY

cat <<EOF

Done. Everything is installed and configured.

What is left is the one thing a script cannot do for you:

  1. Open $vault/00-inbox/MY-PROFILE.md and fill in your name,
     your language and your main projects. Every skill reads it.

  2. In Hermes Desktop, pick a model that supports tool calling,
     then start a new conversation and type:

       /braindump the onboarding team is struggling with the new script

     You should see it call sb_brief, then sb_create_note, then sb_commit,
     and a new note appears in $vault/00-inbox/.

If the tools do not show up, quit Hermes Desktop completely and reopen it:
plugins are discovered at startup.
EOF
