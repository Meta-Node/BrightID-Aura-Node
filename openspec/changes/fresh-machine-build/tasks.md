## 1. Dockerfile

- [ ] 1.1 In `db/Dockerfile`, set `FROM alpine:3.22`, replace the `--repository`-flagged install with `apk add --no-cache nodejs npm`, and update the comment above it; verify `docker compose build --no-cache db` succeeds on a clean host.
- [ ] 1.2 Verify the image: `docker run --rm --entrypoint sh brightid/db -c 'arangod --version; foxx --version'` reports 3.9.1 and 2.1.1.

## 2. Compose

- [ ] 2.1 Add `restart: unless-stopped` to every service in `docker-compose.yml` and remove the top-level `version:` key; verify `docker compose config` shows the policy on all seven services and prints no `version` warning.
- [ ] 2.2 Verify recovery: with the node running, reboot the host; all seven services return to `running` and `lastProcessedBlock` advances. Then `docker compose stop`, reboot, and verify the services stay stopped.

## 3. Install guide

- [ ] 3.1 In `docs/installation-guide.md`, label the tarball/Docker Hub section as the published-image path for `BrightID/BrightID-Node` and add "Building from this repository" (clone, `config.env`, `docker compose build`, `INIT_BRIGHTID_DB=1 docker compose up -d`, restart behaviour); verify by following the new section verbatim on a clean host through to `/brightid/v6/state` answering.

## 4. Tests

- [ ] 4.1 Run `scripts/build-foxx.sh`; verify both Mocha suites pass with no change from `dev`.
