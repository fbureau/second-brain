#!/usr/bin/env bash
#
# Install the Second Brain plugin + skills into a Hermes Agent home.
#
# Usage:
#   ./hermes/install.sh /path/to/your/vault [~/.hermes]
#
# Idempotent. Never overwrites an existing SOUL.md, USER.md or config.yaml — it prints
# what to merge instead.
set -euo pipefail

vault="${1:?usage: install.sh /path/to/vault [hermes-home]}"
hermes_home="${2:-${HERMES_HOME:-$HOME/.hermes}}"
repo="$(cd "$(dirname "$0")/.." && pwd)"
vault="$(cd "$vault" && pwd)"

[[ -f "$vault/_CLAUDE.md" ]] || { echo "✗ $vault has no _CLAUDE.md — copy vault-starter/ there first"; exit 1; }
[[ -d "$hermes_home" ]] || { echo "✗ $hermes_home not found — install Hermes Agent first (hermes-agent.nousresearch.com)"; exit 1; }

link() {  # link <src> <dst>
  if [[ -L "$2" || ! -e "$2" ]]; then ln -sfn "$1" "$2"; echo "✓ $2 → $1"; else echo "• $2 exists (not a symlink) — left as is"; fi
}

mkdir -p "$hermes_home/plugins" "$hermes_home/skills" "$hermes_home/memories"
link "$repo/hermes/plugin/second_brain" "$hermes_home/plugins/second_brain"
link "$repo/hermes/plugin/second_brain/skills"  "$hermes_home/skills/second-brain"
link "$repo/hermes/memory/sb_vault"     "$hermes_home/plugins/sb_vault"

if [[ -f "$hermes_home/SOUL.md" ]]; then
  echo "• $hermes_home/SOUL.md exists — merge hermes/SOUL.md into it by hand (identity slot #1 of the system prompt)"
else
  cp "$repo/hermes/SOUL.md" "$hermes_home/SOUL.md"; echo "✓ SOUL.md installed"
fi

lang="$(grep -oE 'Working language\*\*: `?[a-z]{2}' "$vault/00-inbox/MY-PROFILE.md" 2>/dev/null | grep -oE '[a-z]{2}$' || echo en)"
if [[ -f "$hermes_home/memories/USER.md" ]]; then
  echo "• memories/USER.md exists — add the pointers from hermes/memories/USER.md.example if missing"
else
  sed -e "s#__VAULT_PATH__#$vault#" -e "s#__LANG__#$lang#" "$repo/hermes/memories/USER.md.example" > "$hermes_home/memories/USER.md"
  echo "✓ memories/USER.md seeded (vault pointer, language=$lang)"
fi

if ! grep -qs '^SECOND_BRAIN_VAULT=' "$hermes_home/.env" 2>/dev/null; then
  printf 'SECOND_BRAIN_VAULT=%s\n' "$vault" >> "$hermes_home/.env"; echo "✓ SECOND_BRAIN_VAULT written to $hermes_home/.env"
else
  echo "• SECOND_BRAIN_VAULT already set in $hermes_home/.env"
fi

# The vault's own safety net: the pre-commit hook (needs the vault to be a git repo).
if git -C "$vault" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  "$repo/hooks/install.sh" "$vault" | sed 's/^/  /'
else
  echo "• $vault is not a git repository — run: (cd \"$vault\" && git init && git add -A && git commit -m 'Initial vault') then $repo/hooks/install.sh \"$vault\""
fi

cat <<EOF

Next steps
  1. Merge hermes/config.example.yaml into $hermes_home/config.yaml — at minimum:
       hermes config set plugins.entries.second_brain.settings.vault_path "$vault"
       hermes config set terminal.cwd "$vault"
     and pick a tool-calling-capable model with \`hermes model\` (context ≥ 32k).
  2. Optional — passive recall from the vault on every turn:
       hermes config set memory.provider sb_vault
     (read-only; only one external memory provider can be active at a time.)
  3. Validate:   hermes plugins doctor second_brain   ·   hermes plugins list
  4. Try it:     hermes  →  /braindump the onboarding team is struggling with the new script
EOF
