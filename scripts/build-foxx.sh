#!/usr/bin/env bash
# Builds brightid6.zip and apply6.zip from web_services/foxx/brightid source,
# and runs the brightid6 test suite, all inside the same OS image used in
# production (db/Dockerfile) so native modules (keccak, secp256k1) match the
# deployed runtime rather than whatever platform the developer is on.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FOXX_DIR="$REPO_ROOT/web_services/foxx"
IMAGE_TAG="brightid-foxx-builder"

echo "==> Building foxx builder image (matches production ArangoDB version + Alpine/musl runtime)"
docker build -q -t "$IMAGE_TAG" -f "$REPO_ROOT/scripts/foxx-builder.Dockerfile" "$REPO_ROOT/scripts"

echo "==> Running build+test container"
docker run --rm \
  -v "$FOXX_DIR:/build/foxx" \
  --entrypoint /bin/sh \
  "$IMAGE_TAG" \
  -c '
set -e

echo "-- starting arangod --"
mkdir -p /tmp/arangodb-data /tmp/arangodb-apps
arangod --database.directory /tmp/arangodb-data \
        --javascript.app-path /tmp/arangodb-apps \
        --server.authentication false \
        --server.endpoint tcp://127.0.0.1:8529 \
        --log.foreground-tty false \
        --log.file /tmp/arangod.log &
ARANGOD_PID=$!
trap "kill $ARANGOD_PID 2>/dev/null || true" EXIT

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

echo "-- seeding variables collection (works around a fresh-install-only bug in initdb.js, present in upstream too: variablesColl is captured before createCollections() runs) --"
arangosh --server.authentication false --server.endpoint tcp://127.0.0.1:8529 \
  --javascript.execute-string "if (!db._collection(\"variables\")) { db._create(\"variables\"); }"

echo "-- npm ci (installs native modules for this container'"'"'s OS/libc) --"
cd /build/foxx/brightid
npm ci

echo "-- building brightid6.zip --"
rm -rf /tmp/out/brightid && mkdir -p /tmp/out/brightid/APP
cp -r /build/foxx/brightid/. /tmp/out/brightid/APP/
find /tmp/out/brightid/APP -name ".DS_Store" -delete
( cd /tmp/out/brightid && zip -rq /tmp/brightid6.zip APP )

echo "-- building apply6.zip --"
rm -rf /tmp/out/apply && mkdir -p /tmp/out/apply/APP
cp -r /build/foxx/brightid/. /tmp/out/apply/APP/
find /tmp/out/apply/APP -name ".DS_Store" -delete
rm -rf /tmp/out/apply/APP/tests
cp /tmp/out/apply/APP/manifest_apply.json /tmp/out/apply/APP/manifest.json
( cd /tmp/out/apply && zip -rq /tmp/apply6.zip APP )

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

echo "-- writing zips to mounted output (independent of test outcome) --"
cp /tmp/brightid6.zip /build/foxx/brightid6.zip
cp /tmp/apply6.zip /build/foxx/apply6.zip

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
'
