#!/bin/bash
# Install the publish gate as a `pre-push` hook in a repository.
#
# The hook makes it impossible to push a credential by accident, from any
# tool, in any terminal, at any hour — not just from the scripts we
# remembered to update.
#
# Usage:
#   install-publish-hook.sh [repo-dir ...]
#
# With no arguments it installs into every repo listed in
# PUBLISH_REPOS below.

set -uo pipefail

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATE="$HOOK_DIR/publish-gate.sh"

PUBLISH_REPOS=(
    "$HOME/.openclaw/workspace"
    "$HOME/Projects/quill"
    "$HOME/Projects/SmolQuill"
    "$HOME/Projects/SolChat"
    "$HOME/Projects/sol-assistant"
    "$HOME/Projects/openclaw-backup"
)

install_into() {
    repo="$1"
    hooks="$repo/.git/hooks"
    if [ ! -d "$hooks" ]; then
        echo "  skip (no .git/hooks): $repo"
        return 0
    fi
    cat > "$hooks/pre-push" <<HOOK
#!/bin/bash
# Pre-push credential gate — installed by install-publish-hook.sh
# Refuses to push anything carrying a credential. Delete this file to
# disable the gate (not recommended).
GATE="$GATE"
if [ ! -f "\$GATE" ]; then
    echo "pre-push: gate missing at \$GATE — refusing to publish" >&2
    exit 1
fi
exec /bin/bash "\$GATE" "\$(git rev-parse --show-toplevel)"
HOOK
    chmod +x "$hooks/pre-push"
    echo "  installed: $hooks/pre-push"
}

if [ $# -gt 0 ]; then
    TARGETS=("$@")
else
    TARGETS=("${PUBLISH_REPOS[@]}")
fi

if [ ! -f "$GATE" ]; then
    echo "publish gate not found at $GATE" >&2
    exit 2
fi

echo "Installing pre-push credential gate..."
for repo in "${TARGETS[@]}"; do
    if [ -d "$repo/.git" ]; then
        install_into "$repo"
    else
        echo "  skip (not a git repo): $repo"
    fi
done
echo "Done."
