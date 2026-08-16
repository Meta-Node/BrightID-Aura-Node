#!/usr/bin/env bash
# Control-flow regression test for foxx-build-inner.sh - no docker, no
# arangod. Stubs arangod/arangosh/npm/foxx on PATH (scripts/test-stubs/) and
# runs the real inner script against a small fake source tree, to check that
# the zips it builds always get written to FOXX_BASE_DIR regardless of what
# happens afterward (install/test failures).
#
# This does NOT verify the real docker/arangod/npm behavior - that only
# get exercised by an actual run of build-foxx.sh (see its header comment).
# This guards one thing: a step between "zips are built" and "zips are
# copied out" must never be able to swallow already-built zips via `set -e`.
# That's the exact bug this test was written to catch - see git history for
# scripts/foxx-build-inner.sh around the "writing zips to mounted output"
# step for the incident this test regresses.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INNER_SCRIPT="$SCRIPT_DIR/foxx-build-inner.sh"
STUBS_DIR="$SCRIPT_DIR/test-stubs"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

FAKE_BASE="$WORKDIR/foxx-base"
mkdir -p "$FAKE_BASE/brightid/tests"
cat > "$FAKE_BASE/brightid/manifest.json" <<'EOF'
{"main": "index.js", "name": "brightid-fake", "version": "0.0.0", "tests": ["tests/*.js"]}
EOF
cat > "$FAKE_BASE/brightid/manifest_apply.json" <<'EOF'
{"main": "apply.js", "name": "apply-fake", "version": "0.0.0"}
EOF
echo "module.exports = {}" > "$FAKE_BASE/brightid/index.js"
echo "module.exports = {}" > "$FAKE_BASE/brightid/apply.js"
echo "// fake test" > "$FAKE_BASE/brightid/tests/fake.js"

export PATH="$STUBS_DIR:$PATH"
export HOME="$WORKDIR" # arangosh/npm stubs don't need it, but keeps things sandboxed

pass=0
fail=0

check() {
  local desc="$1"
  local condition="$2"
  if eval "$condition"; then
    echo "  ok - $desc"
    pass=$((pass + 1))
  else
    echo "  FAIL - $desc"
    fail=$((fail + 1))
  fi
}

echo "== case 1: foxx install fails -> zips must still be written =="
rm -f "$FAKE_BASE/brightid6.zip" "$FAKE_BASE/apply6.zip"
set +e
FOXX_BASE_DIR="$FAKE_BASE" FOXX_FAIL_INSTALL=1 bash "$INNER_SCRIPT" >"$WORKDIR/case1.log" 2>&1
exit_code=$?
set -e
check "script exits non-zero" "[ $exit_code -ne 0 ]"
check "brightid6.zip was written" "[ -f '$FAKE_BASE/brightid6.zip' ]"
check "apply6.zip was written" "[ -f '$FAKE_BASE/apply6.zip' ]"

echo "== case 2: everything succeeds -> zips written, exit 0 =="
rm -f "$FAKE_BASE/brightid6.zip" "$FAKE_BASE/apply6.zip"
set +e
FOXX_BASE_DIR="$FAKE_BASE" bash "$INNER_SCRIPT" >"$WORKDIR/case2.log" 2>&1
exit_code=$?
set -e
check "script exits zero" "[ $exit_code -eq 0 ]"
check "brightid6.zip was written" "[ -f '$FAKE_BASE/brightid6.zip' ]"
check "apply6.zip was written" "[ -f '$FAKE_BASE/apply6.zip' ]"

echo "== case 3: foxx test fails -> zips still written, exit reflects failure count =="
rm -f "$FAKE_BASE/brightid6.zip" "$FAKE_BASE/apply6.zip"
set +e
FOXX_BASE_DIR="$FAKE_BASE" FOXX_FAIL_TEST=3 bash "$INNER_SCRIPT" >"$WORKDIR/case3.log" 2>&1
exit_code=$?
set -e
check "script exits with the test failure count" "[ $exit_code -eq 3 ]"
check "brightid6.zip was written" "[ -f '$FAKE_BASE/brightid6.zip' ]"
check "apply6.zip was written" "[ -f '$FAKE_BASE/apply6.zip' ]"

echo
echo "$pass passed, $fail failed"
if [ "$fail" -ne 0 ]; then
  echo "-- logs from the run(s) above --"
  for log in "$WORKDIR"/case*.log; do
    echo "--- $(basename "$log") ---"
    cat "$log"
  done
  exit 1
fi
