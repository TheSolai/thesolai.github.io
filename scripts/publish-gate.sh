#!/bin/bash
# Publish gate — refuses to push a commit that carries a credential.
#
# Installed as a `pre-push` hook in every repo that publishes to GitHub,
# and called directly by scripts/workspace-backup.sh before it pushes.
#
# Three independent checks:
#   1. WORKTREE — no credential in any tracked or untracked file.
#   2. INDEX    — no credential staged for commit.
#   3. HISTORY  — no credential in the commits about to be pushed.
#
# The history check is the one that actually matters. A credential that
# was committed months ago and is still sitting in the branch history
# will be published by the push even though the working tree is clean.
#
# Failure is fatal by design. A blocked push is recoverable. A published
# credential is not.
#
# Usage:
#   publish-gate.sh [--range <git-rev-range>[,<range>...]] [repo-dir]
#
#   --range   revision range(s) to scan. Comma-separated. Each entry is
#             either a range ("main..HEAD") or a single rev ("HEAD",
#             meaning every ancestor of that rev).
#
#   With no --range, the gate reads git's pre-push protocol from stdin
#   (one "<local ref> <local sha> <remote ref> <remote sha>" line per
#   ref being pushed) and scans exactly those ranges. If stdin is empty
#   it falls back to "@{u}..HEAD", and failing that, to every ancestor
#   of HEAD — the conservative choice, because an unpushed branch is
#   exactly the case where a stale leak is most likely to be published.
#
# Exit codes: 0 = safe to publish, 1 = blocked, 2 = usage error.

set -uo pipefail

GATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCAN="$GATE_DIR/secret-scan.py"
RANGE=""
REPO=""
STDIN_RANGES=""

while [ $# -gt 0 ]; do
    case "$1" in
        --range)
            RANGE="$2"
            shift 2
            ;;
        --range=*)
            RANGE="${1#--range=}"
            shift
            ;;
        -h|--help)
            sed -n '2,33p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            REPO="$1"
            shift
            ;;
    esac
done

if [ -z "$REPO" ]; then
    REPO="$(git rev-parse --show-toplevel 2>/dev/null)"
fi
if [ -z "$REPO" ] || [ ! -d "$REPO/.git" ]; then
    echo "publish-gate: not inside a git repository" >&2
    exit 2
fi

cd "$REPO" || exit 2

if [ ! -f "$SCAN" ]; then
    echo "publish-gate: secret-scan.py not found at $SCAN — refusing to publish unchecked" >&2
    exit 1
fi

PY=/usr/bin/python3
if [ ! -x "$PY" ]; then
    PY="$(command -v python3)"
fi
if [ -z "$PY" ]; then
    echo "publish-gate: python3 not available — refusing to publish unchecked" >&2
    exit 1
fi

# ------------------------------------------------------------- worktree
echo "publish-gate: checking working tree..."
if ! "$PY" "$SCAN" "$REPO" --worktree; then
    echo "publish-gate: BLOCKED — credential found in the working tree." >&2
    exit 1
fi

# ---------------------------------------------------------------- index
echo "publish-gate: checking index..."
if ! "$PY" "$SCAN" "$REPO" --staged --quiet; then
    echo "publish-gate: BLOCKED — credential staged for commit." >&2
    exit 1
fi

# -------------------------------------------------------------- history
if [ -z "$RANGE" ]; then
    # git's pre-push protocol: "<local ref> <local sha> <remote ref> <remote sha>"
    while read -r local_ref local_sha remote_ref remote_sha; do
        [ -z "${local_sha:-}" ] && continue
        if [ "${remote_sha:-}" = "0000000000000000000000000000000000000000" ]; then
            # New branch: everything reachable from the local sha is new.
            STDIN_RANGES="${STDIN_RANGES}${STDIN_RANGES:+,}${local_sha}"
        else
            STDIN_RANGES="${STDIN_RANGES}${STDIN_RANGES:+,}${remote_sha}..${local_sha}"
        fi
    done

    if [ -n "$STDIN_RANGES" ]; then
        RANGE="$STDIN_RANGES"
    else
        UPSTREAM="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)"
        if [ -n "$UPSTREAM" ]; then
            RANGE="@{u}..HEAD"
        else
            # No upstream: scan every ancestor of HEAD. Conservative on
            # purpose — this is the case where an old leak survives to
            # the push unnoticed.
            RANGE="HEAD"
        fi
    fi
fi

echo "publish-gate: checking push range $RANGE..."
if ! "$PY" "$SCAN" "$REPO" --history "$RANGE"; then
    echo "publish-gate: BLOCKED — credential found in the commits being pushed." >&2
    echo "publish-gate: scrub the history (git filter-repo) or rotate the credential." >&2
    exit 1
fi

echo "publish-gate: OK — nothing to publish carries a credential."
exit 0
