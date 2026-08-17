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
if grep -oq 'api\.fleminganalytic\.com/api' "$SRC/dist/assets/$JS"; then
    die "the bundle points at api.fleminganalytic.com/api — that 404s every call"
fi
ok "API base URL has no /api suffix"

# 2. Tailwind actually compiled. An unlayered universal reset once voided
#    every padding and margin utility in the app while the classes stayed in
#    the markup, so presence of a class name proves nothing - check the CSS.
CSS_BYTES=$(stat -c%s "$SRC/dist/assets/$CSS")
if [ "$CSS_BYTES" -lt 40000 ]; then
    die "stylesheet is only ${CSS_BYTES} bytes — utilities are probably not compiling"
fi
ok "stylesheet is $((CSS_BYTES / 1024))KB (utilities compiled)"

# 3. No secrets in a file served to the public.
if grep -qEo '(secret|password|api[_-]?key)["'"'"']?\s*[:=]\s*["'"'"'][A-Za-z0-9+/=_-]{16,}' "$SRC/dist/assets/$JS"; then
    die "something credential-shaped is in the bundle"
fi
ok "no credential-shaped strings in the bundle"

if [ "$CHECK_ONLY" = "1" ]; then
    echo; info "--check: nothing deployed."; echo; exit 0
fi

# Deploy. Only index.html and the two hashed assets - never a recursive copy,
# which is what buried the web root in old build output.
install -m 644 "$INDEX" "$WEB/index.html"
install -m 644 "$SRC/dist/assets/$JS"  "$WEB/assets/$JS"
install -m 644 "$SRC/dist/assets/$CSS" "$WEB/assets/$CSS"
chown -R www-data:www-data "$WEB/index.html" "$WEB/assets"
ok "deployed $JS + $CSS"

# 4. The live page serves the bundle we just built, not a cached older one.
sleep 2
LIVE=$(curl -s "$SITE/" | grep -o 'index-[A-Za-z0-9_-]*\.js' | head -1)
[ "$LIVE" = "$JS" ] || die "live page serves $LIVE, expected $JS"
ok "live page serves the new bundle"

# 5. The routes exist. A single-page app answers 200 on any path, so a status
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
