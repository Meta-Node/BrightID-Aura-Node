#!/bin/sh
# Runs inside the foxx-builder container (see build-foxx.sh), or directly on
# the host under scripts/build-foxx.test.sh with FOXX_BASE_DIR pointed at a
# fake source tree and arangod/arangosh/npm/foxx stubbed on PATH.
set -e

FOXX_BASE_DIR="${FOXX_BASE_DIR:-/build/foxx}"

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

echo "-- seeding variables collection (belt-and-suspenders: initdb.js now creates this itself on a fresh install, but pre-seeding here costs nothing and protects against older service versions still carrying the old bug) --"
arangosh --server.authentication false --server.endpoint tcp://127.0.0.1:8529 \
  --javascript.execute-string "if (!db._collection(\"variables\")) { db._create(\"variables\"); }"

echo "-- npm ci (installs native modules for this container's OS/libc) --"
cd "$FOXX_BASE_DIR/brightid"
npm ci

echo "-- building brightid6.zip --"
rm -rf /tmp/out/brightid && mkdir -p /tmp/out/brightid/APP
cp -r "$FOXX_BASE_DIR/brightid/." /tmp/out/brightid/APP/
find /tmp/out/brightid/APP -name ".DS_Store" -delete
( cd /tmp/out/brightid && zip -rq /tmp/brightid6.zip APP )

echo "-- building apply6.zip --"
rm -rf /tmp/out/apply && mkdir -p /tmp/out/apply/APP
cp -r "$FOXX_BASE_DIR/brightid/." /tmp/out/apply/APP/
find /tmp/out/apply/APP -name ".DS_Store" -delete
rm -rf /tmp/out/apply/APP/tests
cp /tmp/out/apply/APP/manifest_apply.json /tmp/out/apply/APP/manifest.json
( cd /tmp/out/apply && zip -rq /tmp/apply6.zip APP )

echo "-- writing zips to mounted output (independent of install/test outcome below) --"
cp /tmp/brightid6.zip "$FOXX_BASE_DIR/brightid6.zip"
cp /tmp/apply6.zip "$FOXX_BASE_DIR/apply6.zip"

echo "-- installing services into running arangod --"
# Config values per the wiki Development Guide (Default Values section):
# https://github.com/BrightID/BrightID-Node/wiki/Development-Guide
foxx install --server http://127.0.0.1:8529 \
  -c seed="\"ci-test-seed-do-not-use-in-production\"" \
  -c operationsTimeWindow=900 -c operationsLimit=60 -c appsOperationsLimit=500 \
  /brightid6 /tmp/brightid6.zip
foxx install --server http://127.0.0.1:8529 \
  -c seed="\"ci-test-seed-do-not-use-in-production\"" \
  -c operationsTimeWindow=900 -c operationsLimit=60 -c appsOperationsLimit=500 \
  /apply6 /tmp/apply6.zip

echo "-- running brightid6 test suite --"
set +e
foxx test --server http://127.0.0.1:8529 /brightid6
TEST_EXIT=$?
set -e

if [ "$TEST_EXIT" -ne 0 ]; then
  echo "==> zips written, but $TEST_EXIT test(s) failed - review before shipping" >&2
else
  echo "==> done, all tests passed"
fi
exit $TEST_EXIT
