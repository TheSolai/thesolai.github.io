#!/usr/bin/env bash
# Run the FULL verification suite for SIDHE & STONE: native, web, and art.
#
#   ./verify_all.sh
#
# Every check here is a check that already exists in the repo. Nothing here is
# weakened, skipped, or edited around — the point of this script is to make it
# impossible to ship without having run all of them, and to run them in the
# order that fails fastest.
#
# The art suite runs FIRST on purpose. A sprite problem is the cheapest defect
# to fix and the most expensive to discover after the native and web suites have
# already told you everything is fine.

set -uo pipefail

SRC="/Users/amre/Projects/GameStewKit"
GODOT="/opt/homebrew/bin/godot"
NODE="/Users/amre/.openclaw/tools/node-v24.21.0/bin/node"
PXL="$NODE tools/pxl/bin/pxl.js"

# The web steps run `npm` and `node`, and the npm shim is a shebang script
# (`#!/usr/bin/env node`), so it picks up whatever `node` is first on PATH.
# The Homebrew node on PATH is broken (it cannot load libllhttp), so the
# working toolchain has to be first on PATH or every web step dies with a
# dyld error that looks like a test failure but is not one.
export PATH="/Users/amre/.openclaw/tools/node-v24.21.0/bin:$PATH"

FAILED=()
PASSED=()

step() { printf "\n\033[1m=== %s ===\033[0m\n" "$1"; }
ok()   { PASSED+=("$1"); printf "\033[32m  PASS\033[0m %s\n" "$1"; }
bad()  { FAILED+=("$1"); printf "\033[31m  FAIL\033[0m %s\n" "$1"; }

cd "$SRC" || { echo "no $SRC"; exit 1; }

# ---------------------------------------------------------------- art
step "Art: rebuild sprite assets from pxl source"
if python3 ai/regen_sprites.py --build 2>&1 | tail -8; then
	ok "regen_sprites.py --build"
else
	bad "regen_sprites.py --build"
fi

step "Art: verify sprites"
if python3 ai/verify_sprites.py 2>&1 | tail -5; then
	ok "verify_sprites.py"
else
	bad "verify_sprites.py"
fi

step "Art: grid check"
if python3 tools/grid_check.py 2>&1 | tail -3; then
	ok "grid_check.py"
else
	bad "grid_check.py"
fi

step "Art: pxl lint every sprite"
LINT_FAIL=0
LINT_N=0
for f in art/*/*.px.js; do
	[ -e "$f" ] || continue
	case "$(basename "$f")" in palette.px.js) continue ;; esac
	LINT_N=$((LINT_N + 1))
	out=$($PXL lint "$f" 2>&1) || { LINT_FAIL=1; printf "  %s\n" "$out" | tail -3; }
	echo "$out" | grep -qE "clean" || { LINT_FAIL=1; echo "  lint findings: $f"; }
done
if [ "$LINT_FAIL" = "0" ]; then ok "pxl lint ($LINT_N sprites)"; else bad "pxl lint"; fi

step "Art: lighting check every sprite"
LIGHT_FAIL=0
LIGHT_N=0
for f in art/*/*.px.js; do
	[ -e "$f" ] || continue
	case "$(basename "$f")" in palette.px.js) continue ;; esac
	name=$(basename "$f" .px.js)
	LIGHT_N=$((LIGHT_N + 1))
	out=$(python3 tools/light_check.py "$name" 2>&1) || { LIGHT_FAIL=1; printf "  %s\n" "$out" | tail -2; }
done
if [ "$LIGHT_FAIL" = "0" ]; then ok "light_check ($LIGHT_N sprites)"; else bad "light_check"; fi

# ------------------------------------------------------------- native
step "Native: UI smoke test"
if "$GODOT" --headless --path . --script res://tests/ui_smoke.gd 2>&1 | tail -12; then
	ok "ui_smoke.gd"
else
	bad "ui_smoke.gd"
fi

step "Native: validate.sh"
if ./tests/validate.sh 2>&1 | tail -12; then
	ok "validate.sh"
else
	bad "validate.sh"
fi

step "Native: UI capture"
if "$GODOT" --headless --path . --script res://tests/ui_capture.gd 2>&1 | tail -12; then
	ok "ui_capture.gd"
else
	bad "ui_capture.gd"
fi

# ---------------------------------------------------------------- web
step "Web: build"
if (cd web && npm run build 2>&1 | tail -12); then
	ok "npm run build"
else
	bad "npm run build"
fi

step "Web: test suite"
if (cd web && npm test 2>&1 | tail -20); then
	ok "npm test"
else
	bad "npm test"
fi

step "Web: screenshot capture"
if (cd web && node tests/capture_shots.mjs 2>&1 | tail -12); then
	ok "capture_shots.mjs"
else
	bad "capture_shots.mjs"
fi

# ------------------------------------------------------------ palette
step "Palette: all six mirrors in sync"
python3 - <<'PY'
import re, sys
files = {
    "art/palette.px.js": None,
    "web/src/ui/palette.ts": None,
    "ai/verify_sprites.py": None,
    "tools/grid_check.py": None,
    "src/main.gd": None,
    "web/index.html": None,
}
sets = {}
for f in files:
    try:
        txt = open(f).read()
    except OSError:
        print("  MISSING", f); sys.exit(1)
    # Godot spells colours "1e1a16" without the hash.
    cols = set(re.findall(r'#([0-9A-Fa-f]{6})', txt))
    cols |= set(re.findall(r'"([0-9A-Fa-f]{6})"', txt))
    cols |= set(re.findall(r'\b([0-9A-Fa-f]{6})\b', txt))
    sets[f] = {c.lower() for c in cols if not c.lower() in ("ffffff",)}
base = sets["art/palette.px.js"]

# The three canonical mirrors must spell the whole palette.
CANONICAL = ("art/palette.px.js", "web/src/ui/palette.ts", "ai/verify_sprites.py")
# The rest are consumers: they may use a SUBSET of the palette, but they may
# never introduce a colour that is not in it. A consumer holding 4 of the 20
# is correct; a consumer holding a 21st colour is a private palette, and
# that is the drift this check exists to catch.
CONSUMERS = ("tools/grid_check.py", "src/main.gd", "web/index.html")

bad = False
for f in CANONICAL:
    s = sets[f]
    if s != base:
        print(f"  MISMATCH {f} (canonical mirror must spell the whole palette)")
        print("    only in palette.px.js:", sorted(base - s))
        print("    only in mirror      :", sorted(s - base))
        bad = True
for f in CONSUMERS:
    s = sets[f]
    foreign = s - base
    if foreign:
        print(f"  FOREIGN COLOUR {f}:", sorted(foreign))
        print("    a consumer may use a subset of the palette, never a new colour")
        bad = True
    else:
        print(f"  ok {f} ({len(s)}/{len(base)} colours, all canonical)")
print("  palette colours:", len(base))
sys.exit(1 if bad else 0)
PY
if [ $? -eq 0 ]; then ok "palette mirrors"; else bad "palette mirrors"; fi

# -------------------------------------------------------------- done
printf "\n\033[1m=== Summary ===\033[0m\n"
printf "  passed: %s\n" "${#PASSED[@]}"
for p in "${PASSED[@]}"; do printf "    \033[32m+%s\033[0m\n" "$p"; done
if [ "${#FAILED[@]}" -gt 0 ]; then
	printf "  failed: %s\n" "${#FAILED[@]}"
	for f in "${FAILED[@]}"; do printf "    \033[31m-%s\033[0m\n" "$f"; done
	exit 1
fi
printf "\n\033[1mALL GREEN\033[0m\n"
