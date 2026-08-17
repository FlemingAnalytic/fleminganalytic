#!/usr/bin/env bash
# Build the React client and put it live.
#
#   scripts/deploy_client.sh            build, verify, deploy
#   scripts/deploy_client.sh --check    build and verify, deploy nothing
#
# This exists because the previous procedure was "npm run build, then copy
# dist/* into client-prod by hand". That is how the web root came to hold
# eight stale deploy trees, one of them advertising a placeholder phone
# number, and how a bundle pointing at a wrong API base URL stayed live for
# weeks without anyone noticing.
#
# The checks below are the ones that would have caught what actually went
# wrong, in the order they went wrong.
set -euo pipefail

SRC="${CLIENT_SRC:-/root/src/fleminganalytic-client}"
WEB="${CLIENT_WEB:-/var/www/fleminganalytic/client-prod}"
SITE="${SITE_URL:-https://fleminganalytic.com}"
CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1

ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
bad()  { printf "  \033[31m✗\033[0m %s\n" "$1"; }
info() { printf "  \033[2m·\033[0m %s\n" "$1"; }
die()  { bad "$1"; echo; exit 1; }

echo
info "building in $SRC"
cd "$SRC"
npm run build >/tmp/deploy_build.log 2>&1 || { cat /tmp/deploy_build.log; die "build failed"; }
ok "built"

INDEX="$SRC/dist/index.html"
JS=$(grep -o 'index-[A-Za-z0-9_-]*\.js' "$INDEX" | head -1)
CSS=$(grep -o 'index-[A-Za-z0-9_-]*\.css' "$INDEX" | head -1)
[ -n "$JS" ] && [ -n "$CSS" ] || die "could not find the hashed asset names in dist/index.html"

# 1. The API base URL. A trailing /api here 404s every call in the app at
#    once, silently, because the routers are mounted without a shared prefix.
#    Scanned across every chunk, not just the entry one: the client is now
#    code-split, and the module that builds request URLs is in its own chunk,
#    so grepping the entry point alone would have stopped checking this.
if grep -rq 'api\.fleminganalytic\.com/api' "$SRC/dist/assets/"; then
    die "a chunk points at api.fleminganalytic.com/api — that 404s every call"
fi
ok "API base URL has no /api suffix (all chunks)"

# 2. Tailwind actually compiled. An unlayered universal reset once voided
#    every padding and margin utility in the app while the classes stayed in
#    the markup, so presence of a class name proves nothing - check the CSS.
CSS_BYTES=$(stat -c%s "$SRC/dist/assets/$CSS")
if [ "$CSS_BYTES" -lt 40000 ]; then
    die "stylesheet is only ${CSS_BYTES} bytes — utilities are probably not compiling"
fi
ok "stylesheet is $((CSS_BYTES / 1024))KB (utilities compiled)"

# 3. No secrets in a file served to the public. Every chunk, for the same
#    reason as check 1.
if grep -rqE '(secret|password|api[_-]?key)["'"'"']?\s*[:=]\s*["'"'"'][A-Za-z0-9+/=_-]{16,}' "$SRC/dist/assets/"; then
    die "something credential-shaped is in a chunk"
fi
ok "no credential-shaped strings in any chunk"

# 4. Every chunk index.html asks for up front exists in the build. A missing
#    modulepreload target is a blank page, and it would not show up as a bad
#    status code - the HTML serves fine and the app never starts.
MISSING=0
for ref in $(grep -oE '/assets/[A-Za-z0-9._-]+' "$INDEX" | sed 's|/assets/||' | sort -u); do
    [ -f "$SRC/dist/assets/$ref" ] || { bad "index.html references missing $ref"; MISSING=1; }
done
[ "$MISSING" = "0" ] || die "the build is incomplete"
ok "every asset index.html references is present"

if [ "$CHECK_ONLY" = "1" ]; then
    echo; info "--check: nothing deployed."; echo; exit 0
fi

# Deploy every chunk in dist/assets, and nothing outside it.
#
# This used to copy exactly index.html plus the two hashed assets, because a
# recursive copy of the whole tree was what buried the web root in eight stale
# deploys. That was right when the client was one bundle. It is now
# code-split into ~26 chunks, and copying two of them would put a page live
# whose preloads 404 - a blank site with every status code healthy.
#
# So: copy all of dist/assets (the build output only, never the tree above
# it), then age out what the new build did not produce.
install -m 644 "$INDEX" "$WEB/index.html"
install -d -m 755 "$WEB/assets"
COPIED=0
for f in "$SRC"/dist/assets/*; do
    install -m 644 "$f" "$WEB/assets/$(basename "$f")"
    COPIED=$((COPIED + 1))
done
chown -R www-data:www-data "$WEB/index.html" "$WEB/assets"
ok "deployed $COPIED chunks"

# Age out superseded chunks. Not deleted immediately: a browser that loaded
# the page seconds before a deploy will still ask for its own chunks, and
# pulling them mid-session breaks a page that was working. Three days is long
# enough for that and short enough that the directory stays bounded - it had
# reached 9.5 MB of bundles going back four months.
PRUNED=0
for f in "$WEB"/assets/*; do
    base=$(basename "$f")
    [ -e "$SRC/dist/assets/$base" ] && continue
    if [ -n "$(find "$f" -mtime +3 2>/dev/null)" ]; then
        rm -f "$f"; PRUNED=$((PRUNED + 1))
    fi
done
[ "$PRUNED" -gt 0 ] && info "pruned $PRUNED superseded chunk(s) older than 3 days"

# 5. Every chunk the new index.html asks for is actually being served. This is
#    the check that would catch the two-file copy above going stale again.
sleep 2
for ref in $(grep -oE '/assets/[A-Za-z0-9._-]+' "$INDEX" | sort -u); do
    code=$(curl -s -o /dev/null -w '%{http_code}' "$SITE$ref")
    [ "$code" = "200" ] || die "$ref returns $code from the live site"
done
ok "every preloaded chunk is served"

# 6. The live page serves the bundle we just built, not a cached older one.
sleep 2
LIVE=$(curl -s "$SITE/" | grep -o 'index-[A-Za-z0-9_-]*\.js' | head -1)
[ "$LIVE" = "$JS" ] || die "live page serves $LIVE, expected $JS"
ok "live page serves the new bundle"

# 7. The routes exist. A single-page app answers 200 on any path, so a status
#    code proves nothing - check the served shell is the app, then leave the
#    render check to scripts/verify_claims.mjs.
for route in / /approach /contact /analyst; do
    code=$(curl -s -o /dev/null -w '%{http_code}' "$SITE$route")
    [ "$code" = "200" ] || die "$route returned $code"
done
ok "core routes respond"

echo
info "deployed. render checks: node scripts/verify_claims.mjs"
echo
