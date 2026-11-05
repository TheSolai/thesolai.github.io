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
#   publish-gate.sh [--range <git-rev-range>[,<range>...]]
#                   [--baseline <rev>] [repo-dir]
#
#   --range   revision range(s) to scan. Comma-separated. Each entry is
#             either a range ("main..HEAD") or a single rev ("HEAD",
#             meaning every ancestor of that rev).
#
#   --baseline  a revision that is ALREADY PUBLISHED. Literal credential
#             values that already occur in that revision's tree are
#             reported as pre-existing and do not block. Without this the
#             gate re-blocks forever on content it published long ago — a
#             credential already on the remote cannot be un-published by
#             refusing a later push. Every finding that is NOT already
#             published still blocks, so a newly introduced credential is
#             still fatal. Pattern findings are never suppressed.
#
#   --remote  the git remote being pushed to (default: origin). Used to
#             work out whether the TARGET repo is private.
#
# PRIVATE REPOS
#   When the target repo is private, an IDENTIFIER harvested from a
#   secrets file (an email address, a URL, a hostname) is reported but
#   does not block. Publishing a reply address to a private backup repo
#   is not a credential leak; blocking it did exactly that for the
#   Private Workspace Backup, which failed every run from 2026-10-31 to
#   2026-11-03 because a 16-character address in
#   secrets/reply-addresses.txt appeared in ten files. A credential-SHAPED
#   literal still blocks, and a pattern finding still blocks — nothing
#   else is relaxed.
#
#   The privacy is read from GitHub itself (`gh api repos/<owner>/<repo>`),
#   not from a local flag, and the check FAILS CLOSED: if GitHub cannot be
#   asked, the strict public-repo rules apply.
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
BASELINE=""
REMOTE="origin"
PRIVATE_REPO=0

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
        --baseline)
            BASELINE="$2"
            shift 2
            ;;
        --baseline=*)
            BASELINE="${1#--baseline=}"
            shift
            ;;
        --remote)
            REMOTE="$2"
            shift 2
            ;;
        --remote=*)
            REMOTE="${1#--remote=}"
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

# gate_target_is_private — 0 if the repo being pushed to is PRIVATE.
#
# The answer comes from GitHub, not from a local flag, so it cannot be
# faked by the thing being gated. It FAILS CLOSED: any error — no gh, no
# auth, an unknown host, a private repo that does not exist — leaves the
# strict public-repo rules in force.
gate_target_is_private() {
    local url path owner repo out
    command -v gh >/dev/null 2>&1 || return 1
    url=$(git remote get-url "$REMOTE" 2>/dev/null) || return 1
    [ -n "$url" ] || return 1

    case "$url" in
        *github.com[:/]*) path="${url#*github.com/}" ;;
        *github.com[:/]*) path="${url#*github.com:}" ;;
        *) return 1 ;;
    esac
    path="${path%.git}"
    path="${path#/}"
    owner="${path%%/*}"
    repo="${path#*/}"
    [ "$owner" != "$path" ] || return 1
    [ -n "$owner" ] && [ -n "$repo" ] || return 1

    out=$(gh api "repos/$owner/$repo" --jq '.private' 2>/dev/null) || return 1
    [ "$out" = "true" ]
}

if gate_target_is_private; then
    PRIVATE_REPO=1
    echo "publish-gate: target remote '$REMOTE' is a PRIVATE repo — identifier literals are reported, not blocking."
fi

# run_scan <scan args...>
# Runs the scanner, passing --baseline only when one was supplied. Kept as
# a function rather than an array so the script stays portable to the
# bash 3.2 that ships with macOS.
run_scan() {
    if [ -n "$BASELINE" ]; then
        if [ "$PRIVATE_REPO" = "1" ]; then
            "$PY" "$SCAN" "$REPO" "$@" --baseline "$BASELINE" --private-repo
        else
            "$PY" "$SCAN" "$REPO" "$@" --baseline "$BASELINE"
        fi
    else
        if [ "$PRIVATE_REPO" = "1" ]; then
            "$PY" "$SCAN" "$REPO" "$@" --private-repo
        else
            "$PY" "$SCAN" "$REPO" "$@"
        fi
    fi
}

# ------------------------------------------------------------- worktree
echo "publish-gate: checking working tree..."
if ! run_scan --worktree; then
    echo "publish-gate: BLOCKED — credential found in the working tree." >&2
    exit 1
fi

# ---------------------------------------------------------------- index
echo "publish-gate: checking index..."
if ! run_scan --staged --quiet; then
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
run_scan --history "$RANGE"
SCAN_RC=$?
if [ "$SCAN_RC" -ne 0 ]; then
    if [ "$SCAN_RC" -eq 3 ]; then
        # Could not INSPECT, not "inspected and found something". This
        # happens when the remote-tracking ref is stale and the range
        # names a commit this clone does not have. The push is still
        # blocked - an unscanned push is not a safe push - but telling
        # someone to rotate a credential that is not there sends them
        # chasing a phantom.
        echo "publish-gate: BLOCKED - the push range could not be inspected." >&2
        echo "publish-gate: this is a stale local ref, NOT a credential finding." >&2
        echo "publish-gate: run 'git fetch origin' and push again." >&2
    else
        echo "publish-gate: BLOCKED - credential found in the commits being pushed." >&2
        echo "publish-gate: scrub the history (git filter-repo) or rotate the credential." >&2
    fi
    exit 1
fi

echo "publish-gate: OK — nothing to publish carries a credential."
exit 0
