## Why

`web_services/foxx/{brightid,apply}{5,6}.zip` are built locally with `scripts/build-foxx.sh` and committed by hand (e.g. `git log` shows plain `chore: update zip files` commits). Nothing checks that a committed zip still matches its source tree, so a PR can change `web_services/foxx/v5`/`v6` without the zips being rebuilt, and nothing today surfaces that mismatch to reviewers automatically (upstream [BrightID-Node#361](https://github.com/BrightID/BrightID-Node/issues/361)). The repo has no CI today — no `.github/workflows`.

A byte-for-byte check only works if two independent builds of the same source actually produce identical bytes. Today they don't: `scripts/foxx-build-inner.sh` builds each zip with plain `zip -rq` (`scripts/foxx-build-inner.sh:74`), which records each file's modification time and enumerates files in filesystem order — so a rebuild from an identical checkout produces a different zip purely from timestamps and directory-listing order, even with no source change. Packaging has to be made deterministic before a comparison check is meaningful.

## What Changes

- `scripts/foxx-builder.Dockerfile`: pin the base image by digest and the toolchain versions it installs, so the environment two independent builds run in is itself fixed.
- `scripts/foxx-build-inner.sh`: make zip packaging deterministic — build the file list in a fixed (sorted) order, strip variable metadata (modification times, extra fields), and keep dereferencing symlinks the way the current build already does — so two independent builds of the same source tree, in that pinned image, produce byte-for-byte identical zips.
- New `.github/workflows/foxx-zips.yml`: on push/PR touching `web_services/foxx/**`, `scripts/build-foxx.sh`, `scripts/foxx-build-inner.sh`, `scripts/foxx-builder.Dockerfile`, or the workflow file itself, runs `scripts/build-foxx.sh` and fails the check if any rebuilt zip differs byte-for-byte from the committed one. It also runs on tags, uploading the built zips as workflow artifacts.
- `scripts/README.md` gets a short section describing the CI check and what to do when it fails (rerun `scripts/build-foxx.sh` and commit the result), and the determinism requirement for anything that changes the packaging step.

## Capabilities

### New Capabilities
- `foxx-zip-ci-verification`: an automated check that committed Foxx zips match their source.

### Modified Capabilities
(none)

## Impact

Contributors: a PR that edits Foxx source without rebuilding the zips now makes the CI check fail instead of merging silently stale; the fix is running the existing `scripts/build-foxx.sh` locally and committing the diff — no new local tooling. This change does not itself make the check required for merge — that needs a separate, optional repository setting (branch protection), listed as an optional task below. No change to how zips are built for deployment, installed, or deployed; `docker-entrypoint.sh` and the images are untouched, and the packaging determinism fix produces identical archives to before — same dereferenced symlinks, same permission bits — just fixed metadata and file order. Adds one CI job (Docker build + Mocha suites, same cost as running `build-foxx.sh` today) to every relevant push/PR.
