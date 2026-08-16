# Development guide

This is an in-repo home for development workflow docs, starting with the
automated Foxx build/test path. The rest of the historical
[wiki](https://github.com/BrightID/BrightID-Node/wiki) — the manual
docker/ArangoDB-UI workflow, installation guide, HTTPS setup, etc. — still
applies for now and is linked below; the plan is to migrate those pages into
this directory over time so they're easier to keep in sync with the code.

## Building and testing the Foxx services

`web_services/foxx/brightid6.zip` and `apply6.zip` are the deployable
bundles for the `brightid` and `apply` Foxx services. Historically these were
built by hand: run the node locally in Docker (bind-mounting a local
directory to `/var/lib/arangodb3-apps` so you can edit the JS and see it
hot-reload), edit and test through the ArangoDB web UI, then download the
zip from the UI and unpack it over the committed one. See the wiki's
[Development Guide](https://github.com/BrightID/BrightID-Node/wiki/Development-Guide)
for that full manual process — it's still how you'd do exploratory,
interactive development against a live service.

For rebuilding the zips from source and confirming they pass the test suite
— e.g. after merging in upstream changes — there's now an automated path:

```
scripts/build-foxx.sh
```

This builds both zips from `web_services/foxx/brightid` and runs the
`brightid6` Mocha test suite (`foxx test`), entirely inside a container
matching production's ArangoDB version (currently 3.9.1) and Alpine/musl
runtime. That matters because the services depend on compiled native
modules (`keccak`, `secp256k1`); building inside the same OS/libc production
runs on means you don't have to reason about whether your host platform
produces compatible binaries.

Prerequisites: Docker. Nothing else — this repo has no Node, Python, or
other host-side runtime dependency; every service (Foxx, `consensus`,
`scorer`, `updater`, `web_services/profile`) builds and runs entirely inside
its own container.

**Output**: `web_services/foxx/brightid6.zip` and `apply6.zip` are written
to the working tree regardless of whether the test suite passes — a build
that produces valid, correctly-built zips shouldn't lose them just because a
test failed. The script's exit code reflects the test result (`0` = all
passed), so treat a non-zero exit as "review before committing/shipping,"
not as "the zips are broken."

**Known pre-existing test failures**: as of this writing, 2 of the 114
`brightid6` tests fail on current `upstream/dev` itself (confirmed by
running this same suite against a clean `upstream/dev` checkout) —
`every app should have different limit` and
`should accept new sponsor operation without appUserId`. These are upstream
issues, not something introduced by aura-specific changes; don't treat them
as blocking unless the failure count or set of failing tests changes.

Required Foxx configuration (`seed`, `operationsTimeWindow`,
`operationsLimit`, `appsOperationsLimit`) is passed automatically by the
script, matching the wiki's documented dev defaults.

### If it fails

- **`docker build` fails on the base image or a package install**: check
  your network/Docker Desktop status first; these are pinned, previously-working
  versions.
- **`arangod failed to start`**: the script prints the ArangoDB log on
  failure — check for a port conflict on 8529 from another running
  container.
- **A `foxx install` error mentioning a configuration option**: the
  `manifest.json`/`manifest_apply.json` configuration section may have
  changed upstream; compare against the `-c` flags in
  `scripts/foxx-build-inner.sh`.
- **Test failures beyond the two known ones above**: treat as a real
  regression — don't ship the rebuilt zips until it's understood.

### The tooling itself has its own (much faster) test

`scripts/build-foxx.sh`'s actual build/test logic lives in
`scripts/foxx-build-inner.sh`, which is also exercised directly (no Docker,
no `arangod`, sub-second) by `scripts/build-foxx.test.sh` against stubbed
tools. That test guards the *script's* control flow — e.g. that a failure
partway through can't silently cause a build to lose its own output — not
the real Foxx application behavior. See [`scripts/README.md`](../scripts/README.md)
for details and the convention for adding more tooling tests.
