## 1. Dockerfile

- [x] 1.1 In `db/Dockerfile`, set `FROM alpine:3.22`, replace the `--repository`-flagged install with `apk add --no-cache nodejs npm`, and update the comment above it; verify `docker compose build --no-cache db` succeeds on a clean host.
- [x] 1.2 Verify the image: `docker run --rm --entrypoint sh brightid/db -c 'arangod --version; foxx --version'` reports 3.9.1 and 2.1.1.

## 2. Compose

- [x] 2.1 Add `restart: unless-stopped` to every service in `docker-compose.yml` and remove the top-level `version:` key; verify `docker compose config` shows the policy on all seven services and prints no `version` warning.
- [x] 2.2 Verify recovery: with the node running, reboot the host; all seven services return to `running` and `lastProcessedBlock` advances. Then `docker compose stop`, reboot, and verify the services stay stopped.

## 3. Install guide

- [ ] 3.1 In `docs/installation-guide.md`, label the tarball/Docker Hub section as the published-image path for `BrightID/BrightID-Node` and add "Building from this repository" (clone, `config.env`, `docker compose build`, `docker compose up -d`, restart behaviour); verify by following the new section verbatim on a clean host through to `/brightid/v6/state` answering.

## 4. Re-initialisation is served once

- [x] 4.1 `db/docker-entrypoint.sh`: gate the backup download and restore on
      `INIT_BRIGHTID_DB=1` *and* the absence of a marker outside the data
      volume, and write the marker after a successful restore. Verify: with the
      marker present the download is skipped; with it absent, or with an empty
      data volume, it runs.
- [x] 4.2 `scorer/config.py`: gate the `/snapshots` clear the same way, and
      test the variable's value rather than its presence so `0` means off.
- [ ] 4.3 Verify on a host: re-initialise, confirm the node comes back, then
      `docker compose stop && docker compose up -d` and confirm the database
      and `/snapshots` are untouched. Re-initialise again with
      `--force-recreate` and confirm it does re-initialise.

## 5. Tests

- [x] 5.1 Run `scripts/build-foxx.sh`; verify both Mocha suites pass with no change from `dev`.
