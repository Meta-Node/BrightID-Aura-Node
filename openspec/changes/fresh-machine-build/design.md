## Context

`db/Dockerfile` derives from ArangoDB's official Alpine image for 3.9.1 on `alpine:3.14`. The Foxx CLI it installs needs a newer Node than 3.14 ships, so the file already pulls `nodejs`/`npm` from the 3.18 repositories with `--repository` flags. On a clean build the `apk` step completes and `npm install -g foxx-cli@2.1.1` segfaults — reproduced twice with `--no-cache` on Ubuntu 24.04 / Docker 29. `docker-compose.yml` sets no restart policy. `docs/installation-guide.md` describes the published-image path only.

## Goals / Non-Goals

**Goals:** a deterministic clean-host build with the smallest diff; a node that survives reboots while a deliberate stop is respected; an install guide that names this repository's path.

**Non-Goals:** upgrading ArangoDB, Node, or foxx-cli; changing how Foxx services are built or installed; DAppNode packaging; publishing images.

## Decisions

**D1. Base `db` on `alpine:3.22` and install Node from its own repositories.** One release for base and packages removes the cross-release mismatch and the ordering workaround. 3.22 is a currently supported release (3.18 reached end of life 2025-05-09). Verified: the image builds from `--no-cache`; inside it `arangod` 3.9.1, `foxx` 2.1.1 and Node 22 run; a node initialised from snapshot and processed blocks on it. Alternatives: pinning an older Node on 3.14 — no Node new enough for foxx-cli exists there; a Debian or `node:` base — changes paths and tooling the entrypoint assumes, for no gain.

**D2. `restart: unless-stopped`.** Containers return when the daemon starts, and containers the operator stopped stay stopped. `always` would override a deliberate stop; `on-failure` does not cover a reboot.

**D3. Scope the existing instructions and add this repository's.** The tarball/Docker Hub section is labelled as the published-image path for `BrightID/BrightID-Node`; a new section covers cloning, `config.env`, `docker compose build`, and first start.

## Risks / Trade-offs

- [Newer userland under ArangoDB] → ArangoDB 3.9.1 is statically linked; the entrypoint's tools (`gpg`, `ar`, `tar`, `numactl`, `pwgen`) are available in 3.22. Verified on one host as above, not across hosts.
- [Removing `version:`] → Compose v2 ignores it and warns; Compose v1 is end of life.

## Migration Plan

Tag the current `db` image before rebuilding (`docker tag brightid/db brightid/db:pre-3.22`). Pull, `docker compose build`, `docker compose up -d`. Data volumes are untouched; no re-initialisation. Rollback: `docker tag brightid/db:pre-3.22 brightid/db && docker compose up -d --no-deps db`. Running containers can take the restart policy without recreation: `docker update --restart unless-stopped $(docker compose ps -q)`.
