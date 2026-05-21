#!/bin/bash
# UI smoke test — start backend + frontend in prod mode, hit every route,
# verify key markup is rendered.
#
# Notes:
# - Most tab pages are "use client" → SSR returns the sidebar + loading state
#   only; full content renders after JS. So we probe the SSR for the shell
#   (sidebar + tab labels) and the OnboardingGate's "Loading workspace…".
# - For API rewrites we probe the actual JSON response.

set -e
CURL=/usr/bin/curl
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
LOG_BE=/tmp/sourcy_smoke_be.log
LOG_FE=/tmp/sourcy_smoke_fe.log

cleanup() {
  [ -n "$BEPID" ] && kill "$BEPID" 2>/dev/null
  [ -n "$FEPID" ] && kill "$FEPID" 2>/dev/null
}
trap cleanup EXIT

echo "━━━━ Starting backend on :8000 ━━━━"
DEV_MODE=1 .venv/bin/python main.py > "$LOG_BE" 2>&1 &
BEPID=$!
sleep 4

echo "━━━━ Starting frontend on :3000 (prod) ━━━━"
cd frontend
PORT=3000 npm start > "$LOG_FE" 2>&1 &
FEPID=$!
cd "$ROOT"
sleep 6

PASS=0
FAIL=0
check() {
  local label="$1" url="$2" expected="$3"
  local code body
  code=$($CURL -s -o /tmp/sourcy_body.txt -w "%{http_code}" -L "$url")
  body=$(cat /tmp/sourcy_body.txt)
  if [ "$code" = "200" ] && echo "$body" | /usr/bin/grep -q "$expected"; then
    echo "  ✓ $label ($code) — contains '$expected'"
    PASS=$((PASS+1))
  else
    echo "  ✗ $label ($code) — missing '$expected'"
    FAIL=$((FAIL+1))
  fi
}

echo
echo "━━━━ Frontend shell (SSR) ━━━━"
check "/home shell"     "http://localhost:3000/home"          "AI co-pilot"
check "/chat shell"     "http://localhost:3000/chat"          "AI co-pilot"
check "/library shell"  "http://localhost:3000/library"       "AI co-pilot"
check "/memory shell"   "http://localhost:3000/memory"        "AI co-pilot"
check "Sidebar tabs"    "http://localhost:3000/home"          "Brand voice"

echo
echo "━━━━ Routes return 200 ━━━━"
check "/ → /home"             "http://localhost:3000/"              "html"
check "/home/tickets"          "http://localhost:3000/home/tickets" "html"
check "/memory/setup wizard"   "http://localhost:3000/memory/setup" "html"

echo
echo "━━━━ API rewrites (Next → FastAPI) ━━━━"
check "memory/state"  "http://localhost:3000/api/v2/memory/state"   "setup_complete"
check "home/refresh"  "http://localhost:3000/api/v2/home/refresh"   "agents_to_dispatch"
check "library/blogs" "http://localhost:3000/api/v2/library/blogs"  "count"
check "library/ads"   "http://localhost:3000/api/v2/library/ads"    "count"
check "library/images""http://localhost:3000/api/v2/library/images" "count"

echo
echo "━━━━ Backend direct probes ━━━━"
check "GA4 / api status" "http://localhost:8000/api/v2/memory/state" "api_status"
check "Principles loaded""http://localhost:8000/api/v2/memory/state" "principles"
check "Winners loaded"   "http://localhost:8000/api/v2/memory/state" "winners"

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  UI SMOKE: $PASS passed · $FAIL failed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $FAIL
