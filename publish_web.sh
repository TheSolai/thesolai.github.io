#!/usr/bin/env bash
# Publish the SIDHE & STONE web build into the drossapps.github.io Jekyll site.
#
# One command from "the web build works" to "the new build is live".
#
#   ./publish_web.sh --build          # build, sync, commit, push, wait for Pages
#   ./publish_web.sh --build --no-push  # build, sync, commit locally only
#
# The traps this exists to prevent, both of which cost real time on v0.1.0:
#
#   1. Godot writes `.import` sidecar files next to every sprite. `npm run build`
#      does not remove them, and copying `dist/` wholesale into the Jekyll site
#      carries them into the deploy as noise. They are stripped here.
#   2. `atlas.json` is NOT a sprite. It must survive the strip, because the web
#      build reads the sprite atlas from it at runtime.
#
# The published tree is checked AFTER the copy, not before: a sync that
# "succeeded" but left a stale file is exactly the failure that ships silently.

set -uo pipefail

SRC="/Users/amre/Projects/GameStewKit/web"
DST="/Users/amre/Projects/drossapps.github.io"
REL="apps/sidhe-and-stone/game"

BUILD=0
PUSH=1
for arg in "$@"; do
	case "$arg" in
		--build) BUILD=1 ;;
		--no-push) PUSH=0 ;;
	esac
done

step() { printf "\n\033[1m=== %s ===\033[0m\n" "$1"; }
fail() { printf "\033[31m  FAILED: %s\033[0m\n" "$1"; exit 1; }

[ -d "$SRC" ] || fail "missing $SRC"
[ -d "$DST" ] || fail "missing $DST"

if [ "$BUILD" = "1" ]; then
	step "Build the web bundle"
	cd "$SRC" || fail "cd $SRC"
	npm run build 2>&1 | tail -20 || fail "npm run build"
	[ -f "$SRC/dist/index.html" ] || fail "no dist/index.html"
fi

[ -d "$SRC/dist" ] || fail "no $SRC/dist — run with --build"

step "Sync dist into the site"
mkdir -p "$DST/$REL" || fail "mkdir $DST/$REL"
# Replace the tree wholesale so deleted sprites do not linger.
rm -rf "$DST/$REL" || fail "clean $DST/$REL"
mkdir -p "$DST/$REL" || fail "mkdir $DST/$REL"
cp -R "$SRC/dist/." "$DST/$REL/" || fail "copy dist"

step "Strip Godot .import sidecars"
stripped=$(find "$DST/$REL" -name "*.import" -type f | wc -l | tr -d ' ')
find "$DST/$REL" -name "*.import" -type f -delete
printf "  stripped %s sidecar(s)\n" "$stripped"

step "Verify the published tree"
[ -f "$DST/$REL/index.html" ] || fail "published index.html missing"
[ -f "$DST/$REL/sprites/atlas.json" ] || fail "atlas.json was stripped — it is not a sprite"
png_count=$(find "$DST/$REL/sprites" -name "*.png" | wc -l | tr -d ' ')
sidecars_left=$(find "$DST/$REL" -name "*.import" | wc -l | tr -d ' ')
printf "  sprites: %s png, %s sidecar(s) remaining\n" "$png_count" "$sidecars_left"
[ "$sidecars_left" = "0" ] || fail "sidecars survived the strip"
[ "$png_count" -gt 0 ] || fail "no sprites published"

# The bundle filename is content-hashed, so index.html must reference a file
# that actually exists next to it.
js_ref=$(grep -oE 'assets/index-[A-Za-z0-9_-]+\.js' "$DST/$REL/index.html" | head -1)
[ -n "$js_ref" ] || fail "index.html references no bundle"
[ -f "$DST/$REL/$js_ref" ] || fail "index.html references $js_ref but it is absent"
printf "  bundle: %s present\n" "$js_ref"

step "Commit"
cd "$DST" || fail "cd $DST"
git add -A "$REL" || fail "git add"
if git diff --cached --quiet; then
	printf "  nothing to commit (site already current)\n"
else
	git commit -q -m "Update the Sidhe & Stone web build" || fail "git commit"
	printf "  %s\n" "$(git log --oneline -1)"
fi

if [ "$PUSH" = "1" ]; then
	step "Push"
	git push origin main 2>&1 | tail -3 || fail "git push"
	COMMIT=$(git rev-parse HEAD)
	printf "  pushed %s\n" "${COMMIT:0:7}"

	step "Wait for GitHub Pages"
	for i in $(seq 1 30); do
		sleep 10
		url="https://thesolai.github.io/drossapps.github.io/apps/sidhe-and-stone/game/index.html"
		code=$(/usr/bin/curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
		if [ "$code" = "200" ]; then
			printf "  live: %s\n" "$url"
			break
		fi
		printf "  ... waiting (%s)\n" "$code"
		if [ "$i" = "30" ]; then
			printf "\033[33m  Pages did not serve 200 within 5 minutes; check the build.\033[0m\n"
			exit 1
		fi
	done
else
	printf "\n  Not pushed (--no-push).\n"
fi

printf "\n\033[1mPublished.\033[0m\n"
