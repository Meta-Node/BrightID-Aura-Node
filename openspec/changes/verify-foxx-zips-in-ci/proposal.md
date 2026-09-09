## Why

`web_services/foxx/{brightid,apply}{5,6}.zip` are built locally with `scripts/build-foxx.sh` and committed by hand, and nothing checks that a committed zip still matches its source — a PR can change `web_services/foxx/v5`/`v6` and merge with a stale zip (upstream [BrightID-Node#361](https://github.com/BrightID/BrightID-Node/issues/361)). The repo has no `.github/workflows` today. A rebuild-and-compare check only works if two builds of the same source produce the same bytes, and today they don't: `scripts/foxx-build-inner.sh` packages with plain `zip -rq`, which records each file's modification time and walks the directory in filesystem order. So this change makes packaging deterministic first, recommits the four archives once under the new packaging — their bytes change even though their file contents don't — and then adds a workflow that rebuilds and compares.

## What Changes

- `scripts/foxx-builder.Dockerfile`: pin the `node:20-alpine` base by digest and pin the `apk add` package versions.
- `scripts/foxx-build-inner.sh`: package deterministically — normalize modification times on the staged tree, feed `zip` a sorted file list instead of letting `zip -r` walk the directory, and pass `-X`.
- `web_services/foxx/*.zip`: rebuild and recommit all four once, as part of this change.
- New `.github/workflows/foxx-zips.yml`: on push/PR touching `web_services/foxx/**`, `scripts/build-foxx.sh`, `scripts/foxx-build-inner.sh`, `scripts/foxx-builder.Dockerfile`, or the workflow file, runs `scripts/build-foxx.sh` and fails, naming the mismatched zip, if any rebuilt zip differs byte-for-byte from the committed one.
- `scripts/README.md`: a short section on the check, the fix when it fails (rerun `scripts/build-foxx.sh`, commit the result), and the rule that any future packaging change must preserve determinism.

## Impact

- Contributors: a PR that edits Foxx source without rebuilding the zips fails the check instead of merging stale. The fix is the existing `scripts/build-foxx.sh` — no new local tooling.
- The four committed archives change once: same file contents and same dereferenced symlinks, different entry order and metadata. Anything that pinned or hashed those zip bytes externally sees a one-time change.
- Deployment is untouched — `docker-entrypoint.sh` and the `ws` image read the zips by content, not by timestamp or entry order.
- The workflow runs both Mocha suites, because `scripts/build-foxx.sh` does; that is one CI job per relevant push/PR, the same cost as running the script locally.
- The check surfaces mismatches but does not block merging. Making it required is a repository branch-protection setting, listed as an optional task.
