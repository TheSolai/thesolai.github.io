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
CHAINER="$HOOK_DIR/install-chained-push-hook.sh"

PUBLISH_REPOS=(
    "$HOME/.openclaw/workspace"
    "$HOME/Projects/quill"
    "$HOME/Projects/SmolQuill"
    "$HOME/Projects/SolChat"
    "$HOME/Projects/sol-assistant"
    "$HOME/Projects/openclaw-backup"
    "$HOME/Projects/openclaw-backup-check"
    "$HOME/Projects/TerminalDeck"
    "$HOME/Projects/stash-memory"
)

if [ $# -gt 0 ]; then
    TARGETS=("$@")
else
    TARGETS=("${PUBLISH_REPOS[@]}")
fi

if [ ! -f "$GATE" ]; then
    echo "publish gate not found at $GATE" >&2
    exit 2
fi

# Delegate to the chained installer. Writing the hook directly here used to
# CLOBBER any pre-existing pre-push hook (e.g. the git-lfs one in
# stash-memory), silently breaking LFS pushes. The chained installer keeps
# the original as pre-push.original and runs both.
if [ ! -f "$CHAINER" ]; then
    echo "chained hook installer not found at $CHAINER" >&2
    exit 2
fi

echo "Installing pre-push credential gate..."
/bin/bash "$CHAINER" "${TARGETS[@]}"
echo "Done."
