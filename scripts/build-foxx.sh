#!/usr/bin/env bash
# Builds brightid6.zip and apply6.zip from web_services/foxx/brightid source,
# and runs the brightid6 test suite, all inside the same OS image used in
# production (db/Dockerfile) so native modules (keccak, secp256k1) match the
# deployed runtime rather than whatever platform the developer is on.
#
# The actual build/test logic lives in foxx-build-inner.sh, which also runs
# directly on the host (no docker) under build-foxx.test.sh, with
# arangod/arangosh/npm/foxx stubbed on PATH.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FOXX_DIR="$REPO_ROOT/web_services/foxx"
IMAGE_TAG="brightid-foxx-builder"

echo "==> Building foxx builder image (matches production ArangoDB version + Alpine/musl runtime)"
docker build -q -t "$IMAGE_TAG" -f "$REPO_ROOT/scripts/foxx-builder.Dockerfile" "$REPO_ROOT/scripts"

echo "==> Running build+test container"
docker run --rm \
  -v "$FOXX_DIR:/build/foxx" \
  -v "$REPO_ROOT/scripts/foxx-build-inner.sh:/foxx-build-inner.sh:ro" \
  --entrypoint /bin/sh \
  "$IMAGE_TAG" \
  /foxx-build-inner.sh
