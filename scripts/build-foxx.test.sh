#!/usr/bin/env bash
# Control-flow regression test for foxx-build-inner.sh - no docker, no
# arangod. Stubs arangod/arangosh/npm/foxx on PATH (scripts/test-stubs/) and
# runs the real inner script against small fake v5/v6 source trees, to
# check that the zips it builds always get written to FOXX_BASE_DIR
# regardless of what happens afterward (install/test failures), and that a
# failure in one version never prevents the other from being attempted.
#
# This does NOT verify the real docker/arangod/npm behavior - that only
# gets exercised by an actual run of build-foxx.sh (see its header
# comment). This guards two things: (1) a step between "zips are built"
# and "zips are copied out" must never be able to swallow already-built
# zips via `set -e`, and (2) a build/install failure for v5 or v6 must
# never cascade and skip the other version. See git history for
# scripts/foxx-build-inner.sh for the incidents this test regresses.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INNER_SCRIPT="$SCRIPT_DIR/foxx-build-inner.sh"
STUBS_DIR="$SCRIPT_DIR/test-stubs"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

FAKE_BASE="$WORKDIR/foxx-base"

make_fake_source() {
  version="$1"
  dir="$FAKE_BASE/v$version/tests"
  mkdir -p "$dir"
  cat > "$FAKE_BASE/v$version/manifest.json" <<EOF
{"main": "index.js", "name": "brightid-fake-v$version", "version": "0.0.0", "tests": ["tests/*.js"]}
EOF
  cat > "$FAKE_BASE/v$version/manifest_apply.json" <<EOF
{"main": "apply.js", "name": "apply-fake-v$version", "version": "0.0.0"}
EOF
  echo "module.exports = {}" > "$FAKE_BASE/v$version/index.js"
  echo "module.exports = {}" > "$FAKE_BASE/v$version/apply.js"
  echo "// fake test" > "$FAKE_BASE/v$version/tests/fake.js"
}

make_fake_source 6
make_fake_source 5

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

check_zips_written() {
  check "brightid6.zip was written" "[ -f '$FAKE_BASE/brightid6.zip' ]"
  check "apply6.zip was written" "[ -f '$FAKE_BASE/apply6.zip' ]"
  check "brightid5.zip was written" "[ -f '$FAKE_BASE/brightid5.zip' ]"
  check "apply5.zip was written" "[ -f '$FAKE_BASE/apply5.zip' ]"
}

clear_zips() {
  rm -f "$FAKE_BASE"/brightid6.zip "$FAKE_BASE"/apply6.zip "$FAKE_BASE"/brightid5.zip "$FAKE_BASE"/apply5.zip
}

echo "== case 1: foxx install fails (both versions) -> zips must still be written =="
clear_zips
set +e
FOXX_BASE_DIR="$FAKE_BASE" FOXX_FAIL_INSTALL=1 bash "$INNER_SCRIPT" >"$WORKDIR/case1.log" 2>&1
exit_code=$?
set -e
check "script exits non-zero" "[ $exit_code -ne 0 ]"
check_zips_written

echo "== case 2: everything succeeds -> zips written, exit 0 =="
clear_zips
set +e
FOXX_BASE_DIR="$FAKE_BASE" bash "$INNER_SCRIPT" >"$WORKDIR/case2.log" 2>&1
exit_code=$?
set -e
check "script exits zero" "[ $exit_code -eq 0 ]"
check_zips_written

echo "== case 3: foxx test fails on both versions -> zips still written, exit reflects combined failure count =="
clear_zips
set +e
FOXX_BASE_DIR="$FAKE_BASE" FOXX_FAIL_TEST=3 bash "$INNER_SCRIPT" >"$WORKDIR/case3.log" 2>&1
exit_code=$?
set -e
# FOXX_FAIL_TEST applies to every `foxx test` call the stub sees (v6 and
# v5 both), and foxx-build-inner.sh sums the two versions' exit codes -
# 3 failures reported for each version, so 6 total.
check "script exits with the combined test failure count" "[ $exit_code -eq 6 ]"
check_zips_written

echo "== case 4: only v6 install fails -> v5 must still build, install, and test successfully =="
clear_zips
set +e
FOXX_BASE_DIR="$FAKE_BASE" FOXX_FAIL_INSTALL_MOUNT=6 bash "$INNER_SCRIPT" >"$WORKDIR/case4.log" 2>&1
exit_code=$?
set -e
check "script exits non-zero (v6 failed)" "[ $exit_code -ne 0 ]"
check_zips_written
check "v5 tests actually ran (not skipped)" "grep -q 'running brightid5 test suite' '$WORKDIR/case4.log'"
check "v6 tests were skipped (v6 never installed)" "grep -q 'skipping v6 tests' '$WORKDIR/case4.log'"

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
