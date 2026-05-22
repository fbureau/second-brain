#!/usr/bin/env bash
#
# Install the Second Brain Git hooks into a target repository.
#
# Usage:
#   ./hooks/install.sh [path-to-vault-repo]
#
# With no argument, installs into THIS repo. Point it at your vault repo if the
# vault is versioned separately.
#
set -euo pipefail

src_dir="$(cd "$(dirname "$0")" && pwd)"
target_repo="${1:-$(git rev-parse --show-toplevel)}"

if [[ ! -d "$target_repo/.git" ]]; then
  echo "✗ $target_repo is not a Git repository (no .git/)."
  echo "  Run 'git init' there first."
  exit 1
fi

dest="$target_repo/.git/hooks/pre-commit"
ln -sf "$src_dir/pre-commit" "$dest" 2>/dev/null || cp "$src_dir/pre-commit" "$dest"
chmod +x "$dest"

echo "✓ Installed pre-commit hook into $target_repo/.git/hooks/"
echo "  (alternatively: git config core.hooksPath \"$src_dir\")"
