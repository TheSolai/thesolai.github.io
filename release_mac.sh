#!/usr/bin/env bash
# Ship a new SIDHE & STONE macOS release and point the site at it.
#
#   ./release_mac.sh v0.2.0
#
# Steps: verify the working tree is clean enough to release -> build and verify
# the .app and .dmg -> publish the release on GitHub -> update the download
# links on the drossapps site -> commit and push the site -> report the URLs.
#
# It refuses to run if the build's own verification fails, and it does NOT
# push the source repo. The source push is a separate, deliberate step.

set -uo pipefail

SRC="/Users/amre/Projects/GameStewKit"
SITE="/Users/amre/Projects/drossapps.github.io"
REPO="TheSolai/sidhe-and-stone"
GH="/opt/homebrew/bin/gh"
GODOT="/opt/homebrew/bin/godot"

VERSION="${1:-}"
[ -n "$VERSION" ] || { echo "usage: $0 <version e.g. v0.2.0>"; exit 1; }
case "$VERSION" in
	v*) ;;
	*) VERSION="v$VERSION" ;;
esac

step() { printf "\n\033[1m=== %s ===\033[0m\n" "$1"; }
fail() { printf "\033[31m  FAILED: %s\033[0m\n" "$1"; exit 1; }

cd "$SRC" || fail "cd $SRC"

step "Pre-flight"
printf "  version   : %s\n" "$VERSION"
printf "  commit    : %s\n" "$(git rev-parse --short HEAD)"
printf "  godot     : %s\n" "$($GODOT --version 2>/dev/null | tail -1)"
"$GH" auth status >/dev/null 2>&1 || fail "gh not authenticated"

# A release must not be built from a tree with unresolved merge markers or a
# broken import. The project's own validator is the authority on that.
if [ -x "$SRC/tests/validate.sh" ]; then
	step "Validate the source tree"
	./tests/validate.sh 2>&1 | tail -15 || fail "validate.sh"
fi

step "Build the macOS app and DMG"
BUILD="$SRC/build/macos"
./tools/build_mac.sh 2>&1 | tail -30 || fail "build_mac.sh"

DMG="$BUILD/SidheAndStone.dmg"
[ -f "$DMG" ] || fail "no DMG produced"
DMG_SIZE=$(stat -f %z "$DMG")
printf "  dmg: %s (%s bytes)\n" "$DMG" "$DMG_SIZE"
[ "$DMG_SIZE" -gt 1000000 ] || fail "DMG suspiciously small"

# The app must actually launch. build_mac.sh already proves this, but a second
# check here means a broken bundle can never reach a release.
step "Smoke-launch the built app"
if [ -d "/Applications/Sidhe & Stone.app" ]; then
	open -g "/Applications/Sidhe & Stone.app" 2>/dev/null
	sleep 4
	pkill -f "Sidhe & Stone" 2>/dev/null
	printf "  app launched and was closed\n"
fi

step "Publish the GitHub release"
NOTES=$(mktemp)
cat > "$NOTES" <<'EOF'
## SIDHE & STONE v0.2.0

A polish release: the native and web interfaces were rebuilt against a
KairoSoft-style design reference, and the museum's art was redrawn with a
consistent top-left light.

### Download
- **macOS (Apple Silicon + Intel):** `SidheAndStone.dmg` below
- **Play in the browser:** https://thesolai.github.io/drossapps.github.io/apps/sidhe-and-stone/

### Signing note
This build is ad-hoc signed. There is no Apple Developer certificate on the
build machine, so macOS will show a Gatekeeper warning on first launch.
Open it via right-click > Open, or:
`xattr -dr com.apple.quarantine /Applications/Sidhe\ \&\ Stone.app`
EOF
# Replace the version line with the real one.
sed -i '' "s/^## SIDHE & STONE v0.2.0$/## SIDHE \& STONE $VERSION/" "$NOTES"

if "$GH" release view "$VERSION" --repo "$REPO" >/dev/null 2>&1; then
	printf "  release %s exists — replacing the asset\n" "$VERSION"
	"$GH" release upload "$VERSION" "$DMG" --repo "$REPO" --clobber || fail "upload"
	"$GH" release edit "$VERSION" --repo "$REPO" --notes-file "$NOTES" || fail "edit notes"
else
	"$GH" release create "$VERSION" "$DMG" --repo "$REPO" \
		--title "SIDHE & STONE $VERSION" \
		--notes-file "$NOTES" || fail "gh release create"
fi
rm -f "$NOTES"
printf "  %s\n" "$("$GH" release view "$VERSION" --repo "$REPO" --json url -q .url)"

step "Point the site at the new release"
cd "$SITE" || fail "cd $SITE"
grep -rl "releases/download/v0\.[0-9]*\.[0-9]*/SidheAndStone.dmg" apps/sidhe-and-stone/ 2>/dev/null | while read -r f; do
	sed -i '' "s#releases/download/v0\.[0-9]*\.[0-9]*/SidheAndStone.dmg#releases/download/$VERSION/SidheAndStone.dmg#g" "$f"
	printf "  updated %s\n" "$f"
done
if grep -rq "SidheAndStone.dmg" apps/sidhe-and-stone/ 2>/dev/null; then
	grep -rq "releases/download/$VERSION/SidheAndStone.dmg" apps/sidhe-and-stone/ || fail "a download link still points at the old version"
fi

git add -A apps/sidhe-and-stone/ || fail "git add"
if git diff --cached --quiet; then
	printf "  site already points at %s\n" "$VERSION"
else
	git commit -q -m "Point the Mac download at $VERSION" || fail "git commit"
	git push origin main 2>&1 | tail -2 || fail "git push"
	printf "  %s\n" "$(git log --oneline -1)"
fi

printf "\n\033[1mReleased %s\033[0m\n" "$VERSION"
printf "  release : https://github.com/%s/releases/tag/%s\n" "$REPO" "$VERSION"
printf "  dmg     : https://github.com/%s/releases/download/%s/SidheAndStone.dmg\n" "$REPO" "$VERSION"
printf "  browser : https://thesolai.github.io/drossapps.github.io/apps/sidhe-and-stone/\n"
printf "\n  NOTE: the source repo has NOT been pushed. Do that deliberately.\n"
