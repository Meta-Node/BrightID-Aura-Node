## Why

A clean `docker compose build` of this repository fails while installing the Foxx CLI in `db/Dockerfile`; a running node does not come back after the Docker daemon restarts; and the installation guide documents only `BrightID/BrightID-Node`'s published-image path. All three were met standing up a second Aura node on 2026-09-08.

## What Changes

- `db/Dockerfile`: base image `alpine:3.14` becomes `alpine:3.22`; `nodejs` and `npm` install from that release's own repositories.
- `docker-compose.yml`: every service gets `restart: unless-stopped`; the obsolete top-level `version:` key is removed.
- `docs/installation-guide.md`: a "Building from this repository" section is added and the existing tarball/Docker Hub instructions are scoped to `BrightID/BrightID-Node`'s published images.

## Capabilities

### New Capabilities
- `node-operation`: clean source builds and recovery after a host restart.

### Modified Capabilities
(none)

## Impact

Rebuilding changes the `db` image's base; ArangoDB remains 3.9.1 and the Foxx services, scorer, and APIs are untouched. Published `brightid/*` images and DAppNode packaging are unchanged.
