#!/bin/bash
# apply-openclaw-patches.sh
#
# Re-applies the local patches to the installed OpenClaw runtime.
#
# WHY THIS EXISTS
#   OpenClaw treats any provider that speaks the Anthropic Messages API as
#   "cache-TTL eligible" and then appends an `openclaw.cache-ttl` transcript
#   marker on every attempt. Each marker re-lists every frozen tool result, so
#   the session window grows O(attempts x toolResults). Measured on
#   2026-10-28 with MiniMax M2.7: 30 markers = 961 KB of a 1.34 MB session
#   window (72% of the transcript was pure bookkeeping), and the session
#   overflowed its 184,800-token context budget because of it.
#
#   `agents.defaults.contextPruning.mode = "off"` does NOT stop it: the agent
#   runtime resolves its own config scope and the Anthropic-compat default
#   re-applies `mode: "cache-ttl"` there. Verified empirically on 2026-10-28
#   by removing the key entirely and restarting — the markers kept coming.
#
#   The only reliable gate is provider eligibility, so that is what is patched.
#
# PATCH EVERY COPY — THIS IS THE PART THAT MATTERS
#   `isCacheTtlEligibleProvider` is not defined once. It is inlined into THREE
#   separately-bundled files:
#       dist/builtin-openclaw-<hash>.mjs       (the main bundle)
#       dist/worker/worker.mjs                 (the worker bundle)
#       dist/worker/sqlite-store.worker.mjs    (the sqlite worker bundle)
#   The agent turns actually run in the WORKER, so patching only the main
#   bundle leaves the decision to an unpatched copy. That is exactly what
#   happened: the 2026-10-28 patch covered the main bundle, and the markers
#   came back — 22 markers = 607 KB of a 910 KB cron window (67%) by
#   2026-11-03, six days later, with the Doctor's tripwire screaming.
#
#   So this script DISCOVERS every file that defines the function and patches
#   each one. It does not hardcode a bundle hash, because the hash changes on
#   every OpenClaw release.
#
#   An OpenClaw upgrade replaces the runtime bundle and silently undoes these
#   patches. Run this script after every upgrade, then restart the gateway:
#       bash scripts/apply-openclaw-patches.sh
#       launchctl kickstart -k gui/501/ai.openclaw.gateway
#
# VERIFY after applying:
#       /opt/homebrew/bin/python3 scripts/health/cache-ttl-audit.py --minutes 10
#
# The Claw Doctor also runs that audit, so a regression is reported even if
# this script is forgotten.

set -u

DIST="${OPENCLAW_DIST:-$HOME/.openclaw/tools/node-v24.21.0/lib/node_modules/openclaw/dist}"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*"; }

if [ ! -d "$DIST" ]; then
    log "FAIL: runtime not found under $DIST"
    log "      set OPENCLAW_DIST to the installed dist directory and retry"
    exit 1
fi

changed=0

# ---------------------------------------------------------------------------
# Discover EVERY file that defines isCacheTtlEligibleProvider.
# ---------------------------------------------------------------------------
# NOTE: no `mapfile` — macOS ships bash 3.2, which does not have it.
TARGETS=()
while IFS= read -r _line; do
    [ -n "$_line" ] && TARGETS[${#TARGETS[@]}]="$_line"
done < <(grep -rl "function isCacheTtlEligibleProvider" "$DIST" --include="*.mjs" 2>/dev/null | sort)

if [ "${#TARGETS[@]}" -eq 0 ]; then
    log "FAIL: no file under $DIST defines isCacheTtlEligibleProvider"
    log "      the runtime layout has probably changed — re-derive the gate"
    exit 1
fi

log "found ${#TARGETS[@]} copy/copies of isCacheTtlEligibleProvider:"
for t in "${TARGETS[@]}"; do log "  - ${t#$DIST/}"; done

# ---------------------------------------------------------------------------
# Patch A: the pretty-printed copy in the main bundle.
#
#   Adds the provider exclusion set and the early return before the final
#   eligibility check. The Anthropic-compat branch below is left intact for
#   providers that genuinely implement Anthropic's prompt-cache TTL.
# ---------------------------------------------------------------------------
patch_pretty() {
    python3 - "$1" <<'PY'
import sys

path = sys.argv[1]
src = open(path, encoding="utf-8", errors="replace").read()

if "cache-ttl-no-minimax" in src or "ANTHROPIC_COMPAT_WITHOUT_PROMPT_CACHE_TTL" in src:
    print("already patched")
    raise SystemExit(0)

const_anchor = 'const CACHE_TTL_CUSTOM_TYPE = "openclaw.cache-ttl";'
const_block = const_anchor + '''
/**
* Providers that expose the Anthropic Messages API but do NOT implement
* Anthropic's prompt-cache TTL semantics. OpenClaw must not append the
* `openclaw.cache-ttl` transcript marker for them: the marker re-lists every
* frozen tool result on every attempt, so the session window grows
* O(attempts x toolResults) and the session overflows its context budget.
*/
const ANTHROPIC_COMPAT_WITHOUT_PROMPT_CACHE_TTL = new Set(["minimax"]);'''

if const_anchor not in src:
    sys.exit("FAIL: could not find the CACHE_TTL_CUSTOM_TYPE anchor")

src = src.replace(const_anchor, const_block, 1)

eligibility_anchor = "\tif (pluginEligibility !== void 0) return pluginEligibility;\n\treturn isAnthropicFamilyCacheTtlEligible({"
eligibility_block = (
    "\tif (pluginEligibility !== void 0) return pluginEligibility;\n"
    "\t// A third-party endpoint that merely SPEAKS the Anthropic Messages API\n"
    "\t// does not implement Anthropic's prompt-cache TTL semantics. Treating it\n"
    "\t// as eligible makes OpenClaw append an `openclaw.cache-ttl` transcript\n"
    "\t// marker on every attempt, and each marker re-lists every frozen tool\n"
    "\t// result, so the session window grows O(attempts x toolResults).\n"
    "\t// `agents.defaults.contextPruning.mode = \"off\"` cannot prevent this: the\n"
    "\t// agent runtime resolves its own config scope and the Anthropic-compat\n"
    "\t// default re-applies `mode: \"cache-ttl\"` there. The only reliable gate\n"
    "\t// is provider eligibility.\n"
    "\tif (ANTHROPIC_COMPAT_WITHOUT_PROMPT_CACHE_TTL.has(normalizedProvider)) return false;/*cache-ttl-no-minimax*/\n"
    "\tconst normalizedBaseUrl = normalizeLowercaseStringOrEmpty(route?.baseUrl);\n"
    "\tif (modelApi === \"anthropic-messages\" && normalizedBaseUrl && !normalizedBaseUrl.includes(\"api.anthropic.com\")) {\n"
    "\t\tif (!isGooglePromptCacheEligible({\n"
    "\t\t\tmodelId: normalizedModelId\n"
    "\t\t}) && normalizedProvider !== \"kilocode\") return false;\n"
    "\t}\n"
    "\treturn isAnthropicFamilyCacheTtlEligible({"
)

if eligibility_anchor not in src:
    sys.exit("FAIL: could not find the isCacheTtlEligibleProvider anchor")

src = src.replace(eligibility_anchor, eligibility_block, 1)
open(path, "w", encoding="utf-8").write(src)
print("patched (readable shape)")
PY
}

# ---------------------------------------------------------------------------
# Patch B: the minified copies in the worker bundles.
#
#   The worker bundles are single-line minified builds with their own inlined
#   copy of the provider runtime, so the main-bundle patch does not reach
#   them. Insert a self-contained guard as the first statement of the
#   function: if the provider is minimax, it is not cache-TTL eligible.
# ---------------------------------------------------------------------------
patch_minified() {
    python3 - "$1" <<'PY'
import re
import sys

path = sys.argv[1]
src = open(path, encoding="utf-8", errors="replace").read()

if "cache-ttl-no-minimax" in src:
    print("already patched")
    raise SystemExit(0)

# Insert the guard as the FIRST statement of the function, using the provider
# parameter directly. The guard must not depend on any local variable: in the
# minified bundle the parameter is the first argument, and the body opens with
# a `let` declaration list that an insertion would break.
pat = re.compile(r"(function isCacheTtlEligibleProvider\(\s*(\w+)\s*,[^)]*\)\{)")
m = pat.search(src)
if not m:
    sys.exit("FAIL: could not find the minified isCacheTtlEligibleProvider")

param = m.group(2)
guard = f'if(String({param}??"").toLowerCase()==="minimax")return false;/*cache-ttl-no-minimax*/'
src = src[:m.end()] + guard + src[m.end():]
open(path, "w", encoding="utf-8").write(src)
print("patched (minified shape)")
PY
}

for t in "${TARGETS[@]}"; do
    if grep -q "cache-ttl-no-minimax" "$t"; then
        log "  already patched: ${t#$DIST/}"
        continue
    fi
    out=$(patch_pretty "$t" 2>&1) && rc=0 || rc=$?
    if [ $rc -ne 0 ]; then
        out=$(patch_minified "$t" 2>&1) && rc=0 || rc=$?
    fi
    if [ $rc -ne 0 ]; then
        log "  FAIL: ${t#$DIST/}"
        log "    $(echo "$out" | tail -2)"
        exit 1
    fi
    log "  $out: ${t#$DIST/}"
    changed=1
done

# ---------------------------------------------------------------------------
# Patch C (redundant safety net): declare MiniMax ineligible in the provider
# plugin itself, via the documented `isCacheTtlEligible` plugin hook.
# ---------------------------------------------------------------------------
MINIMAX=$(grep -rl "MINIMAX_PROVIDER_HOOKS" "$DIST" --include="*.mjs" 2>/dev/null | head -1)
if [ -z "$MINIMAX" ]; then
    log "WARN: no MINIMAX_PROVIDER_HOOKS found — skipping patch C"
elif grep -q "isCacheTtlEligible" "$MINIMAX"; then
    log "patch C already applied (minimax provider hook)"
else
    python3 - "$MINIMAX" <<'PY'
import sys

path = sys.argv[1]
src = open(path, encoding="utf-8", errors="replace").read()

anchor = '\t...buildProviderStreamFamilyHooks("minimax-fast-mode"),\n'
block = anchor + (
    "\t// MiniMax speaks the Anthropic Messages API but does NOT implement\n"
    "\t// Anthropic's prompt-cache TTL semantics. Without this, OpenClaw treats\n"
    "\t// MiniMax as cache-TTL eligible and appends an `openclaw.cache-ttl`\n"
    "\t// marker on every attempt; each marker re-lists every frozen tool\n"
    "\t// result, so the window grows O(attempts x toolResults).\n"
    "\tisCacheTtlEligible: () => false,\n"
)

if anchor not in src:
    sys.exit("FAIL: could not find the MINIMAX_PROVIDER_HOOKS anchor")

src = src.replace(anchor, block, 1)
open(path, "w", encoding="utf-8").write(src)
print("patch C applied")
PY
    if [ $? -eq 0 ]; then
        changed=1
    else
        log "FAIL: patch C could not be applied"
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# Syntax-check EVERY patched file and VERIFY the guard is actually present.
# A patch that does not compile, or that landed in a copy that never runs,
# is worse than no patch at all.
# ---------------------------------------------------------------------------
for f in "${TARGETS[@]}"; do
    node --check "$f" >/dev/null 2>&1 || { log "FAIL: syntax error in $f"; exit 1; }
    if ! grep -q "cache-ttl-no-minimax" "$f"; then
        log "FAIL: $f has no cache-ttl guard after patching"
        exit 1
    fi
done

log "verified: ${#TARGETS[@]}/${#TARGETS[@]} copies patched and syntax-clean"

if [ "$changed" = "1" ]; then
    log "patches applied - restart the gateway to load them:"
    log "  launchctl kickstart -k gui/501/ai.openclaw.gateway"
else
    log "nothing to do"
fi
exit 0
