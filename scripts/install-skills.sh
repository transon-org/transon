#!/usr/bin/env bash
# Installs the agent skills listed in skills-manifest.txt into this project
# using the skills.sh CLI (https://github.com/vercel-labs/skills).
#
# Requires Node.js (npx). Safe to re-run; re-installs/updates listed skills.
set -euo pipefail

cd "$(dirname "$0")/.."
MANIFEST="scripts/skills-manifest.txt"

while IFS= read -r spec; do
    case "$spec" in
        ''|'#'*) continue ;;
    esac
    echo "==> Installing $spec"
    # </dev/null: keep the CLI from consuming the manifest on stdin
    npx -y skills add "$spec" -a cursor -y --copy </dev/null
done < "$MANIFEST"

echo "Done. Installed skills:"
npx -y skills list -p
