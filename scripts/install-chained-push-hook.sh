#!/bin/bash
# Install the credential gate as a pre-push hook in repos that publish to
# GitHub AND hold a live credential in their working tree.
#
# Unlike install-publish-hook.sh, this CHAINENS rather than clobbers: if a
# repo already has a pre-push hook (e.g. the git-lfs one), the original is
# preserved as pre-push.original and the new hook runs both.
#
# Both hooks need the pre-push protocol on stdin (the list of refs being
# pushed), so stdin is captured once to a temp file and replayed to each.
# The credential gate runs FIRST: it is fail-closed, and we do not want a
# credential-bearing push to be attempted at all.
#
# Usage: install-chained-push-hook.sh <repo-dir> [repo-dir ...]

set -uo pipefail

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATE="$HOOK_DIR/publish-gate.sh"

if [ ! -f "$GATE" ]; then
    echo "publish gate not found at $GATE" >&2
    exit 2
fi

for REPO in "$@"; do
    HOOKS="$REPO/.git/hooks"
    if [ ! -d "$HOOKS" ]; then
        echo "  skip (no .git/hooks): $REPO"
        continue
    fi

    # Preserve any existing hook exactly once -- but NOT our own gate hook.
    # A repo that already has the credential gate would otherwise chain the
    # gate to a copy of itself and scan twice.
    if [ -f "$HOOKS/pre-push" ]; then
        if grep -q "publish-gate" "$HOOKS/pre-push" 2>/dev/null; then
            echo "  replacing existing credential gate hook: $HOOKS/pre-push"
            rm -f "$HOOKS/pre-push.original"
        elif [ ! -f "$HOOKS/pre-push.original" ]; then
            cp "$HOOKS/pre-push" "$HOOKS/pre-push.original"
            echo "  preserved existing hook -> pre-push.original"
        fi
    fi

    cat > "$HOOKS/pre-push" <<HOOK
#!/bin/bash
# Pre-push: credential gate + any pre-existing hook.
# Installed by install-chained-push-hook.sh. Delete to disable (not advised).
set -uo pipefail
GATE="$GATE"
TOP="\$(git rev-parse --show-toplevel)"
HOOKS="\$(git rev-parse --git-dir)/hooks"

# Both the credential gate and git-lfs read the ref list from stdin.
STDIN_COPY="\$(mktemp)"
trap 'rm -f "\$STDIN_COPY"' EXIT
cat > "\$STDIN_COPY"

# 1. Credential gate -- fail closed, and run before anything else.
if [ ! -f "\$GATE" ]; then
    echo "pre-push: credential gate missing at \$GATE -- refusing to publish" >&2
    exit 1
fi
if ! /bin/bash "\$GATE" "\$TOP" < "\$STDIN_COPY"; then
    echo "pre-push: BLOCKED -- credential detected; nothing was published." >&2
    exit 1
fi

# 2. Any pre-existing hook (e.g. git-lfs), replaying the same stdin.
if [ -x "\$HOOKS/pre-push.original" ]; then
    "\$HOOKS/pre-push.original" "\$@" < "\$STDIN_COPY"
    rc=\$?
    if [ \$rc -ne 0 ]; then
        exit \$rc
    fi
fi

exit 0
HOOK
    chmod +x "$HOOKS/pre-push"
    echo "  installed chained gate: $HOOKS/pre-push"
done
