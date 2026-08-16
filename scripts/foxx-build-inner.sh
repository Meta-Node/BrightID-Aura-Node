#!/bin/sh
# Runs inside the foxx-builder container (see build-foxx.sh), or directly on
# the host under scripts/build-foxx.test.sh with FOXX_BASE_DIR pointed at a
# fake source tree and arangod/arangosh/npm/foxx stubbed on PATH.
#
# Builds and tests both v5 (soulbound verification) and v6 (blind-signature
# verification) from web_services/foxx/v5 and v6. Production installs both
# into the same ArangoDB database (_system) since they share the same
# social graph - but for *testing*, each version gets its own database
# here, so one version's Mocha suite (truncating collections in
# before/after hooks) can't pollute the other's fixtures. That's a
# deliberate difference from production, not an oversight.
set -e

FOXX_BASE_DIR="${FOXX_BASE_DIR:-/build/foxx}"
SERVER="http://127.0.0.1:8529"

echo "-- starting arangod --"
mkdir -p /tmp/arangodb-data /tmp/arangodb-apps
arangod --database.directory /tmp/arangodb-data \
        --javascript.app-path /tmp/arangodb-apps \
        --server.authentication false \
        --server.endpoint tcp://127.0.0.1:8529 \
        --log.foreground-tty false \
        --log.file /tmp/arangod.log &
ARANGOD_PID=$!
trap 'kill $ARANGOD_PID 2>/dev/null || true' EXIT

echo "-- waiting for arangod --"
up=0
for i in $(seq 1 60); do
  if arangosh --server.authentication false --server.endpoint tcp://127.0.0.1:8529 --javascript.execute-string "db._version()" >/dev/null 2>&1; then
    up=1
    break
  fi
  sleep 1
done
if [ "$up" != "1" ]; then
  echo "arangod failed to start" >&2
  cat /tmp/arangod.log >&2
  exit 1
fi
echo "arangod is up"

# v6 uses the default _system database (matches how build-foxx.sh worked
# before v5 was added). v5 gets its own database, created here, purely for
# test isolation - see header comment.
V5_DB=v5test

echo "-- creating $V5_DB database for v5 test isolation --"
arangosh --server.authentication false --server.endpoint "$SERVER" \
  --javascript.execute-string "if (!db._databases().includes(\"$V5_DB\")) { db._createDatabase(\"$V5_DB\"); }"

seed_variables_collection() {
  db_flag="$1"
  echo "-- seeding variables collection $db_flag (works around a fresh-install-only bug in initdb.js, present upstream on both v5 and v6: variablesColl is captured before createCollections() runs) --"
  arangosh --server.authentication false --server.endpoint "$SERVER" $db_flag \
    --javascript.execute-string "if (!db._collection(\"variables\")) { db._create(\"variables\"); }"
}

seed_variables_collection ""
seed_variables_collection "--server.database $V5_DB"

# $1 = version (5 or 6), $2 = extra foxx-cli db flag (empty for v6/_system)
build_test_install() {
  version="$1"
  db_flag="$2"
  src="$FOXX_BASE_DIR/v$version"

  echo "-- npm ci for v$version (installs native modules for this container's OS/libc) --"
  ( cd "$src" && npm ci )

  echo "-- building brightid$version.zip --"
  rm -rf "/tmp/out/brightid$version" && mkdir -p "/tmp/out/brightid$version/APP"
  cp -r "$src/." "/tmp/out/brightid$version/APP/"
  find "/tmp/out/brightid$version/APP" -name ".DS_Store" -delete
  ( cd "/tmp/out/brightid$version" && zip -rq "/tmp/brightid$version.zip" APP )

  echo "-- building apply$version.zip --"
  rm -rf "/tmp/out/apply$version" && mkdir -p "/tmp/out/apply$version/APP"
  cp -r "$src/." "/tmp/out/apply$version/APP/"
  find "/tmp/out/apply$version/APP" -name ".DS_Store" -delete
  rm -rf "/tmp/out/apply$version/APP/tests"
  cp "/tmp/out/apply$version/APP/manifest_apply.json" "/tmp/out/apply$version/APP/manifest.json"
  ( cd "/tmp/out/apply$version" && zip -rq "/tmp/apply$version.zip" APP )

  echo "-- writing v$version zips to mounted output (independent of install/test outcome below) --"
  cp "/tmp/brightid$version.zip" "$FOXX_BASE_DIR/brightid$version.zip"
  cp "/tmp/apply$version.zip" "$FOXX_BASE_DIR/apply$version.zip"

  echo "-- installing v$version services --"
  # Config values per docs/development-guide.md's dev defaults.
  foxx install --server "$SERVER" $db_flag \
    -c seed="\"ci-test-seed-do-not-use-in-production\"" \
    -c operationsTimeWindow=900 -c operationsLimit=60 -c appsOperationsLimit=500 \
    "/brightid$version" "/tmp/brightid$version.zip"
  foxx install --server "$SERVER" $db_flag \
    -c seed="\"ci-test-seed-do-not-use-in-production\"" \
    -c operationsTimeWindow=900 -c operationsLimit=60 -c appsOperationsLimit=500 \
    "/apply$version" "/tmp/apply$version.zip"
}

# A build/install failure for one version must never prevent the other
# from being attempted - each is wrapped so `set -e` can't cascade across
# versions (the same bug class as the original zip-copy-ordering fix, one
# level up: build_test_install itself runs `foxx install` under `set -e`,
# which would otherwise abort the whole script on the first version's
# failure and skip the second version entirely).
set +e
build_test_install 6 ""
BUILD6_EXIT=$?
set -e
if [ "$BUILD6_EXIT" -ne 0 ]; then
  echo "==> v6 build/install failed (exit $BUILD6_EXIT) - attempting v5 anyway" >&2
fi

set +e
build_test_install 5 "--database $V5_DB"
BUILD5_EXIT=$?
set -e
if [ "$BUILD5_EXIT" -ne 0 ]; then
  echo "==> v5 build/install failed (exit $BUILD5_EXIT)" >&2
fi

TEST6_EXIT=0
if [ "$BUILD6_EXIT" -eq 0 ]; then
  echo "=================================================="
  echo "-- running brightid6 test suite --"
  set +e
  foxx test --server "$SERVER" /brightid6
  TEST6_EXIT=$?
  set -e
else
  echo "==> skipping v6 tests - v6 was not successfully installed" >&2
fi

TEST5_EXIT=0
if [ "$BUILD5_EXIT" -eq 0 ]; then
  echo "=================================================="
  echo "-- running brightid5 test suite --"
  set +e
  foxx test --server "$SERVER" --database "$V5_DB" /brightid5
  TEST5_EXIT=$?
  set -e
else
  echo "==> skipping v5 tests - v5 was not successfully installed" >&2
fi
echo "=================================================="

TOTAL_EXIT=0
if [ "$BUILD6_EXIT" -ne 0 ]; then
  TOTAL_EXIT=$((TOTAL_EXIT + BUILD6_EXIT))
elif [ "$TEST6_EXIT" -ne 0 ]; then
  echo "==> v6: $TEST6_EXIT test(s) failed - review before shipping" >&2
  TOTAL_EXIT=$((TOTAL_EXIT + TEST6_EXIT))
fi
if [ "$BUILD5_EXIT" -ne 0 ]; then
  TOTAL_EXIT=$((TOTAL_EXIT + BUILD5_EXIT))
elif [ "$TEST5_EXIT" -ne 0 ]; then
  echo "==> v5: $TEST5_EXIT test(s) failed - review before shipping" >&2
  TOTAL_EXIT=$((TOTAL_EXIT + TEST5_EXIT))
fi
if [ "$TOTAL_EXIT" -eq 0 ]; then
  echo "==> done, all tests passed (v5 and v6)"
fi
exit $TOTAL_EXIT
