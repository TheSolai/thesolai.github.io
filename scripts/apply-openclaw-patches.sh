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

# --verify-only: run the syntax + BEHAVIOUR checks without touching any file.
# The Claw Doctor calls this so that the tripwire tests what the guard
# actually DOES, not merely that a marker string is present.
VERIFY_ONLY=0
[ "${1:-}" = "--verify-only" ] && VERIFY_ONLY=1

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
# The guard.
#
# It must match on the provider, the model id AND the base URL, because the
# call site does NOT pass a bare provider id. Measured on 2026-11-03 by
# extracting the patched function and calling it directly:
#
#     provider="minimax"                  -> false   (matched)
#     provider="minimax/MiniMax-M2.7"     -> TRUE    (MISSED - qualified ref)
#     provider=""                         -> TRUE    (MISSED - empty)
#     provider=undefined                  -> TRUE    (MISSED - undefined)
#
# The qualified form is what the attempt actually passes, so the earlier
# exact-match guard never fired and the markers kept coming for six days.
# Matching on the model id and base URL as well covers every shape.
#
# The guard is deliberately a substring test on "minimax", not a set
# membership test: "minimax", "minimax/MiniMax-M2.7", "minimax-fast-mode"
# and "MiniMax-M2.7" all have to be excluded, and none of them is a real
# Anthropic endpoint.
# ---------------------------------------------------------------------------
GUARD_MINIFIED='if(/minimax/i.test(String(Ot??"")+" "+String(Zt??"")+" "+String(Dn?.baseUrl??"")))return false;/*cache-ttl-no-minimax*/'
OLD_GUARD_MINIFIED='if(String(Ot??"").toLowerCase()==="minimax")return false;/*cache-ttl-no-minimax*/'

GUARD_READABLE='if (/minimax/i.test(`${normalizedProvider} ${normalizedModelId} ${normalizeLowercaseStringOrEmpty(route?.baseUrl)}`)) return false;/*cache-ttl-no-minimax*/'
OLD_GUARD_READABLE='if (ANTHROPIC_COMPAT_WITHOUT_PROMPT_CACHE_TTL.has(normalizedProvider)) return false;/*cache-ttl-no-minimax*/'

# ---------------------------------------------------------------------------
# Patch A: the pretty-printed copy in the main bundle.
# ---------------------------------------------------------------------------
patch_pretty() {
    python3 - "$1" <<PYEOF
import sys

path = sys.argv[1]
src = open(path, encoding="utf-8", errors="replace").read()

NEW_GUARD = '''$GUARD_READABLE'''
OLD_GUARD = '''$OLD_GUARD_READABLE'''

if NEW_GUARD in src:
    print("already patched")
    raise SystemExit(0)

if OLD_GUARD in src:
    # An earlier, too-narrow guard is in place. Widen it in place.
    src = src.replace(OLD_GUARD, NEW_GUARD, 1)
    open(path, "w", encoding="utf-8").write(src)
    print("guard widened (readable shape)")
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
    "\t//\n"
    "\t// Match on the provider, the model id AND the base URL. The call site\n"
    "\t// does not pass a bare provider id - it passes a qualified reference\n"
    "\t// such as \"minimax/MiniMax-M2.7\" - so an exact-match test never fired.\n"
    "\t$GUARD_READABLE\n"
    "\tif (ANTHROPIC_COMPAT_WITHOUT_PROMPT_CACHE_TTL.has(normalizedProvider)) return false;\n"
    "\tconst normalizedBaseUrl = normalizeLowercaseStringOrEmpty(route?.baseUrl);\n"
    "\tif (modelApi === \"anthropic-messages\" && normalizedBaseUrl && !normalizedBaseUrl.includes(\"api.anthropic.com\") && !ANTHROPIC_COMPAT_WITHOUT_PROMPT_CACHE_TTL.has(normalizedProvider)) {\n"
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
PYEOF
}

# ---------------------------------------------------------------------------
# Patch B: the minified copies in the worker bundles.
# ---------------------------------------------------------------------------
patch_minified() {
    python3 - "$1" <<PYEOF
import re
import sys

path = sys.argv[1]
src = open(path, encoding="utf-8", errors="replace").read()

NEW_GUARD = '''$GUARD_MINIFIED'''
OLD_GUARD = '''$OLD_GUARD_MINIFIED'''

if NEW_GUARD in src:
    print("already patched")
    raise SystemExit(0)

if OLD_GUARD in src:
    src = src.replace(OLD_GUARD, NEW_GUARD, 1)
    open(path, "w", encoding="utf-8").write(src)
    print("guard widened (minified shape)")
    raise SystemExit(0)

# Insert the guard as the FIRST statement of the function, using the provider
# parameter directly. The guard must not depend on any local variable: in the
# minified bundle the parameter is the first argument, and the body opens with
# a `let` declaration list that an insertion would break.
pat = re.compile(r"(function isCacheTtlEligibleProvider\(\s*(\w+)\s*,[^)]*\)\{)")
m = pat.search(src)
if not m:
    sys.exit("FAIL: could not find the minified isCacheTtlEligibleProvider")

guard = NEW_GUARD
src = src[:m.end()] + guard + src[m.end():]
open(path, "w", encoding="utf-8").write(src)
print("patched (minified shape)")
PYEOF
}

for t in "${TARGETS[@]}"; do
    if [ "$VERIFY_ONLY" = "1" ]; then
        log "  (verify-only, not patching): ${t#$DIST/}"
        continue
    fi
    # Always run the patcher: it is idempotent, and it also WIDENS an
    # existing too-narrow guard in place. A file that merely contains the
    # marker string is not proof that the guard is correct — the first
    # version of this patch matched only the bare provider id and therefore
    # never fired against the qualified reference the call site actually
    # passes.
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
    [ "$out" != "already patched" ] && changed=1
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
# Patch D: gate the SECOND marker writer.
#
# The provider guard in `isCacheTtlEligibleProvider` only covers the first
# writer, `appendAttemptCacheTtlIfNeeded`. There is a second one:
#
#     persistToolResultProjections(toolResultPromptProjectionState,
#       (customType, data) => sessionManager.appendCustomEntry(customType, data))
#
# It runs on EVERY prompt submission and is gated only by
# `toolResultPromptProjectionState.frozen.size > 0` — it never consults the
# provider eligibility. Measured on 2026-11-03 at 17:18, AFTER the
# provider guard was loaded by the 17:09:50 restart, the Telegram session
# still wrote a 5,698-byte marker, and a subagent wrote 28 more. Patching
# the first writer alone does not stop the bloat.
#
# The same eligibility test is applied to this writer, so a provider that
# does not implement Anthropic's prompt-cache TTL semantics writes no
# cache-TTL markers at all.
#
# The attempt identifier is DISCOVERED, never hardcoded: the minified
# bundles name it differently in different bundles and the file may be
# re-minified by an OpenClaw upgrade.
# ---------------------------------------------------------------------------
patch_projection_gate() {
    python3 - "$1" <<'PYEOF'
import re
import sys

path = sys.argv[1]
src = open(path, encoding="utf-8", errors="replace").read()

CALL = re.compile(
    r"persistToolResultProjections\(\s*(\w+)\s*,\s*\((\w+)\s*,\s*(\w+)\)\s*=>\s*"
    r"(\w+)\.appendCustomEntry\(\s*\2\s*,\s*\3\s*\)\s*\)")

matches = list(CALL.finditer(src))
if not matches:
    sys.exit("FAIL: no projection-writer call site found")

patched = 0
for m in reversed(matches):          # reversed: earlier offsets stay valid
    state, a, b, mgr = m.group(1), m.group(2), m.group(3), m.group(4)
    before = src[max(0, m.start() - 4000):m.start()]

    # The attempt identifier, DISCOVERED and never hardcoded:
    #   `attempt:_n,`      the minified bundles
    #   `attempt,`         the pretty-printed bundle (shorthand property)
    #   `{ activeSession, attempt } = input`   the destructured binding
    attempt = None
    ids = re.findall(r"attempt:(\w+)\s*,", before)
    if ids:
        attempt = ids[-1]
    elif re.search(r"\battempt\s*,", before):
        attempt = "attempt"
    elif re.search(r"\{[^}]*\battempt\b[^}]*\}\s*=\s*\w+", before):
        attempt = "attempt"
    if not attempt:
        sys.exit("FAIL: could not determine the attempt identifier")

    # The match consumed BOTH closing parens (appendCustomEntry's and
    # persistToolResultProjections'), so the replacement has to close both
    # as well. Leaving the original ')' in place produced a double close
    # and a syntax error in all three bundles.
    guarded = (
        f"persistToolResultProjections({state},({a},{b})=>{{"
        f"isCacheTtlEligibleProvider({attempt}.provider,{attempt}.modelId,"
        f"{attempt}.model?.api,{{baseUrl:{attempt}.model?.baseUrl,"
        f"supportsPromptCacheKey:{attempt}.model?.compat?.supportsPromptCacheKey}})"
        f"&&{mgr}.appendCustomEntry({a},{b})}})")

    src = src[:m.start()] + guarded + src[m.end():]
    patched += 1

open(path, "w", encoding="utf-8").write(src)
print(f"projection gate applied to {patched} call site(s)")
PYEOF
}

for t in "${TARGETS[@]}"; do
    [ "$VERIFY_ONLY" = "1" ] && continue
    out=$(patch_projection_gate "$t" 2>&1) && rc=0 || rc=$?
    if [ $rc -ne 0 ]; then
        log "  FAIL: ${t#$DIST/}"
        log "    $(echo "$out" | tail -2)"
        exit 1
    fi
    log "  $out: ${t#$DIST/}"
    changed=1
done

# ---------------------------------------------------------------------------
# Syntax-check EVERY patched file and VERIFY the guard BEHAVIOUR.
#
# A string check is not enough. The first version of this patch was present
# in all three copies, passed every string check, and still never fired —
# because it matched only the bare provider id while the call site passes a
# qualified reference. The verification therefore extracts the function and
# CALLS it, with the worst-case stubs (the Anthropic-family check says yes),
# and asserts it returns false for every shape of minimax reference.
# ---------------------------------------------------------------------------
for f in "${TARGETS[@]}"; do
    node --check "$f" >/dev/null 2>&1 || { log "FAIL: syntax error in $f"; exit 1; }
    if ! grep -q "cache-ttl-no-minimax" "$f"; then
        log "FAIL: $f has no cache-ttl guard after patching"
        exit 1
    fi
done

# ---------------------------------------------------------------------------
# Verify the SECOND writer is gated too.
#
# The first guard covers `appendAttemptCacheTtlIfNeeded`. The projection
# writer is a separate call site, and it is the one that kept producing
# markers after the provider guard was loaded by the 17:09:50 restart on
# 2026-11-03. Every projection call site must therefore carry the same
# eligibility test, or the window keeps growing.
# ---------------------------------------------------------------------------
log "checking that every projection-writer call site is gated"
for f in "${TARGETS[@]}"; do
    /opt/homebrew/bin/python3 - "$f" <<'PYEOF'
import re
import sys

path = sys.argv[1]
src = open(path, encoding="utf-8", errors="replace").read()

CALL = re.compile(
    r"persistToolResultProjections\(\s*\w+\s*,\s*\(\w+\s*,\s*\w+\)\s*=>\s*"
    r"(?:\{)?[^;]{0,500}?\.appendCustomEntry\(")

sites = list(CALL.finditer(src))
if not sites:
    sys.exit(f"FAIL: no projection-writer call site found in {path}")

unguarded = []
for m in sites:
    window = src[max(0, m.start() - 500):m.end() + 200]
    if "isCacheTtlEligibleProvider(" not in window:
        unguarded.append(m.start())

if unguarded:
    sys.exit(f"FAIL: {len(unguarded)} projection-writer call site(s) are "
             f"ungated in {path}")

print(f"  ok  {len(sites)} projection call site(s), all gated")
PYEOF
    rc=$?
    [ $rc -eq 0 ] || { log "FAIL: $f has an ungated projection writer"; exit 1; }
done

log "behaviour check: extracting the guard from each copy and calling it"
for f in "${TARGETS[@]}"; do
    node - "$f" <<'NODEEOF' || exit 1
const fs = require("fs");
const path = process.argv[2];
const src = fs.readFileSync(path, "utf8");
const i = src.indexOf("function isCacheTtlEligibleProvider(");
if (i < 0) { console.error("  FAIL: function not found in " + path); process.exit(1); }
let depth = 0, j = src.indexOf("{", i), k = j;
for (; k < src.length; k++) {
  if (src[k] === "{") depth++;
  else if (src[k] === "}") { depth--; if (depth === 0) { k++; break; } }
}
const fn = src.slice(i, k);
const normalizeLowercaseStringOrEmpty = (v) => String(v ?? "").trim().toLowerCase();
const resolveProviderCacheTtlEligibility = () => undefined;
const isAnthropicFamilyCacheTtlEligible = () => true;   // worst case
const isGooglePromptCacheEligible = () => false;
const make = new Function(
  "normalizeLowercaseStringOrEmpty", "resolveProviderCacheTtlEligibility",
  "isAnthropicFamilyCacheTtlEligible", "isGooglePromptCacheEligible",
  fn + "; return isCacheTtlEligibleProvider;"
);
const f = make(normalizeLowercaseStringOrEmpty, resolveProviderCacheTtlEligibility,
  isAnthropicFamilyCacheTtlEligible, isGooglePromptCacheEligible);
const cases = [
  ["minimax", "MiniMax-M2.7", "anthropic-messages", { baseUrl: "https://api.minimax.io/anthropic" }],
  ["minimax/MiniMax-M2.7", "MiniMax-M2.7", "anthropic-messages", { baseUrl: "https://api.minimax.io/anthropic" }],
  ["MiniMax", "MiniMax-M2.7", "anthropic-messages", { baseUrl: "https://api.minimax.io/anthropic" }],
  ["", "MiniMax-M2.7", "anthropic-messages", { baseUrl: "https://api.minimax.io/anthropic" }],
  [undefined, "MiniMax-M2.7", "anthropic-messages", { baseUrl: "https://api.minimax.io/anthropic" }],
  ["minimax", "MiniMax-M2.7", "anthropic-messages", { baseUrl: "" }],
  ["somethingelse", "gpt-5", "openai-responses", { baseUrl: "https://api.openai.com" }],
];
let bad = 0;
for (const c of cases) {
  const r = f(c[0], c[1], c[2], c[3]);
  const shouldBeFalse = c[0] === "somethingelse" ? false : true;
  const ok = (r === false) === shouldBeFalse;
  if (!ok) bad++;
  console.log(`  ${ok ? "ok  " : "FAIL"} provider=${JSON.stringify(c[0])} model=${c[1]} -> ${r}`);
}
if (bad) { console.error(`  ${bad} case(s) wrong in ${path}`); process.exit(1); }
NODEEOF
    log "  behaviour verified: ${f#$DIST/}"
done

log "verified: ${#TARGETS[@]}/${#TARGETS[@]} copies patched and syntax-clean"

if [ "$VERIFY_ONLY" = "1" ]; then
    log "verify-only: all checks passed, nothing was modified"
    exit 0
fi

if [ "$changed" = "1" ]; then
    log "patches applied - restart the gateway to load them:"
    log "  launchctl kickstart -k gui/501/ai.openclaw.gateway"
else
    log "nothing to do"
fi
exit 0
