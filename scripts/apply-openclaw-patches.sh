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
BUILTIN="$DIST/builtin-openclaw-q1hiFm14.mjs"
MINIMAX="$DIST/provider-registration-BoNJNMii.mjs"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*"; }

if [ ! -f "$BUILTIN" ] || [ ! -f "$MINIMAX" ]; then
    log "FAIL: runtime not found under $DIST"
    log "      set OPENCLAW_DIST to the installed dist directory and retry"
    exit 1
fi

changed=0

# ---------------------------------------------------------------------------
# Patch 1 (primary): exclude Anthropic-compatible providers that do not
# implement Anthropic's prompt-cache TTL semantics.
# ---------------------------------------------------------------------------
if grep -q "ANTHROPIC_COMPAT_WITHOUT_PROMPT_CACHE_TTL" "$BUILTIN"; then
    log "patch 1 already applied (cache-ttl provider exclusion)"
else
    python3 - "$BUILTIN" <<'PY'
import re
import sys

path = sys.argv[1]
src = open(path).read()

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
    "\tif (ANTHROPIC_COMPAT_WITHOUT_PROMPT_CACHE_TTL.has(normalizedProvider)) return false;\n"
    "\tconst normalizedBaseUrl = normalizeLowercaseStringOrEmpty(route?.baseUrl);\n"
    "\tif (modelApi === \"anthropic-messages\" && normalizedBaseUrl && !normalizedBaseUrl.includes(\"api.anthropic.com\")) {\n"
    "\t\tif (!isGooglePromptCacheEligible({\n"
    "\t\t\tmodelApi,\n"
    "\t\t\tmodelId: normalizedModelId\n"
    "\t\t}) && normalizedProvider !== \"kilocode\") return false;\n"
    "\t}\n"
    "\treturn isAnthropicFamilyCacheTtlEligible({"
)

if eligibility_anchor not in src:
    sys.exit("FAIL: could not find the isCacheTtlEligibleProvider anchor")

src = src.replace(eligibility_anchor, eligibility_block, 1)
open(path, "w").write(src)
print("patch 1 applied")
PY
    if [ $? -eq 0 ]; then
        changed=1
    else
        log "FAIL: patch 1 could not be applied"
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# Patch 2 (redundant safety net): declare MiniMax ineligible in the provider
# plugin itself, via the documented `isCacheTtlEligible` plugin hook.
# ---------------------------------------------------------------------------
if grep -q "isCacheTtlEligible" "$MINIMAX"; then
    log "patch 2 already applied (minimax provider hook)"
else
    python3 - "$MINIMAX" <<'PY'
import sys

path = sys.argv[1]
src = open(path).read()

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
open(path, "w").write(src)
print("patch 2 applied")
PY
    if [ $? -eq 0 ]; then
        changed=1
    else
        log "FAIL: patch 2 could not be applied"
        exit 1
    fi
fi

for f in "$BUILTIN" "$MINIMAX"; do
    node --check "$f" >/dev/null 2>&1 || { log "FAIL: syntax error in $f"; exit 1; }
done

if [ "$changed" = "1" ]; then
    log "patches applied - restart the gateway: launchctl kickstart -k gui/501/ai.openclaw.gateway"
else
    log "nothing to do"
fi
exit 0
