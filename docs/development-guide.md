# Development guide

This is the in-repo home for development workflow docs, migrated from the
[wiki](https://github.com/BrightID/BrightID-Node/wiki) so they're easier to
keep in sync with the code. If you find something here that's gone stale,
fix it in the same PR as whatever change made it stale, or flag it.

## v5 and v6

BrightID node serves two API versions side by side, from the same
underlying social graph: **v5** (soulbound — verifications are tied
directly to a user's BrightID) and **v6** (blind signatures — verifications
are unlinkable from the BrightID they came from; see
[the v6 changelog](v6-changelog.md) for why that changed). Both are real,
currently-served APIs, not a legacy/current split — production installs
both `brightid5`/`apply5` and `brightid6`/`apply6` at once, sharing one
ArangoDB database.

The source lives at `web_services/foxx/v5/` and `web_services/foxx/v6/` —
two independent copies of the same kind of service (they diverged from a
shared ancestor years ago and evolved mostly independently since; see
`web_services/foxx/core/README.md` for the plan to reconcile what's
actually identical between them over time). If a fix or feature is meant
to apply to both APIs, it needs making twice, once per directory, until
that reconciliation happens.

## Interactive development against a live service

For editing Foxx code and seeing it hot-reload against a real ArangoDB
instance:

### Docker install/setup

Pull the official ArangoDB image:

```sh
docker pull arangodb
```

Pick a local directory to bind-mount as the Foxx application directory —
this must exist on your filesystem, e.g. `FOXX_APPS=/home/you/brightid/arangodb-apps`.
On macOS you may need to add that directory under Docker Desktop's "File
Sharing" settings.

Run the container. This creates a persistent `arangodb` volume for the DB
files (so they survive container removal/updates) and bind-mounts the Foxx
directory so you can edit the JS from outside Docker:

```sh
docker run -d -e ARANGO_NO_AUTH=1 -e ARANGO_STORAGE_ENGINE=rocksdb -p 8529:8529 \
  -v arangodb:/var/lib/arangodb3 -v $FOXX_APPS:/var/lib/arangodb3-apps \
  --name arango arangodb
```

To upgrade ArangoDB later while preserving data, append
`--database.auto-upgrade true` to the command above, wait for the container
to exit, `docker rm arango`, then re-run without that flag.

### ArangoDB web interface

Open `http://localhost:8529`.

**Foxx initial deployment**: under "Services" → "Add Service" → "Upload",
upload `brightid6.zip` (or `brightid5.zip`, for the v5 API) from
`web_services/foxx/`, install it, and use `/brightid6` (or `/brightid5`)
as the mount point. Repeat for `apply6.zip`/`apply5.zip` → `/apply6`/`/apply5`.

**`brightid` vs `apply`**: within each version, `brightid` provides the
public API used by BrightID mobile clients; `apply` provides a single
internal endpoint used by the consensus service to apply operations to the
database once the network reaches consensus on them. Both share the same
JS modules within that version's directory (`web_services/foxx/v6/`, say)
— the only differences are that `apply` has no `tests/` directory
(`brightid`'s `tests/operations.js` covers both) and uses
`manifest_apply.json` (with `apply.js` as its main script) instead of
`manifest.json`. `scripts/build-foxx.sh` (see below) builds all four zips
(`brightid5`/`apply5`/`brightid6`/`apply6`) from these two directories
automatically.

**Settings**: under "Settings" for each service, enable development mode
("Set Development"). Configure `BN_SEED`, `operationsTimeWindow`,
`operationsLimit`, and `appsOperationsLimit` — either in `config.env` or
directly under "Settings" in the ArangoDB interface. Suggested dev defaults:

- `BN_SEED`: any secure random string — e.g. a random NaCl keypair's base64
  public key ([generator](https://tweetnacl.js.org/#/sign)).
- `operationsTimeWindow`: `900`
- `operationsLimit`: `60`
- `appsOperationsLimit`: `500`

**Editing**: in your `$FOXX_APPS` directory, edit files under
`_db/_system/brightid5/APP/` or `_db/_system/brightid6/APP/` depending on
which version you're changing. Changes hot-reload immediately. Keep the
matching `_db/_system/apply5/APP/`/`_db/_system/apply6/APP/` in sync with
any JS file you change (except test files), since `brightid`/`apply` share
code but aren't the same mount.

**Testing**: in a `brightid` service's "Settings" tab, click the beaker
icon to run tests; use "API" to exercise endpoints manually. It helps to
keep two browser tabs open — one on the service's API/Settings tab, one on
[the logs](http://localhost:8529/_db/_system/_admin/aardvark/index.html#logs)
— so you can check for errors if a test doesn't show results.

## Building and testing the Foxx services from source (automated)

`web_services/foxx/{brightid,apply}{5,6}.zip` are the deployable bundles
installed above. Historically, updating them meant doing the interactive
workflow above, then downloading the zip from the ArangoDB UI ("Settings"
→ "download") and unpacking it over the committed one — useful for
exploratory work, but manual and easy to get subtly wrong (stale zips,
macOS zip cruft, native modules built for the wrong OS).

For rebuilding the zips from source and confirming they pass their test
suites — e.g. after merging in upstream changes, or once you're done with
interactive edits above and want a clean rebuild — there's an automated
path:

```sh
scripts/build-foxx.sh
```

This builds all four zips from `web_services/foxx/v5` and `v6`, and runs
each version's Mocha test suite (`foxx test`), entirely inside a container
matching production's ArangoDB version (currently 3.9.1) and Alpine/musl
runtime. That matters because the services depend on compiled native
modules (`keccak`, `secp256k1`); building inside the same OS/libc production
runs on means you don't have to reason about whether your host platform
produces compatible binaries.

v6 installs into ArangoDB's default `_system` database, matching
production. v5 gets its own database (`v5test`) for the test run only —
production runs v5 and v6 against the same database since they share the
same social graph, but one version's Mocha suite truncating shared
collections in its `before`/`after` hooks would otherwise pollute the
other's fixtures during a single test run. A failure building/installing
one version never prevents the other from being attempted.

Prerequisites: Docker. Nothing else — this repo has no Node, Python, or
other host-side runtime dependency; every service (Foxx, `consensus`,
`scorer`, `updater`, `web_services/profile`) builds and runs entirely inside
its own container.

**Output**: all four zips are written to the working tree regardless of
whether either test suite passes — a build that produces valid,
correctly-built zips shouldn't lose them just because a test failed. The
script's exit code reflects the combined test result across both versions
(`0` = all passed), so treat a non-zero exit as "review before
committing/shipping," not as "the zips are broken."

**Known pre-existing test failures**:

- **v6**: none, as of this writing — 114/114 passing.
- **v5**: 3 of 92 tests fail, as of this writing (first time v5's suite has
  been run via this automation — v5 was frozen and untested for years
  before this). One is the identical `every app should have different
  limit` bug already diagnosed and fixed in v6 (dual `app`+`id`
  rate-limiting semantics breaking a test fixture that predates that
  change) — the same fix would apply, just not yet ported to v5's copy.
  The other two (`should not be able to add an operation twice`, and a
  `before all` hook failure under `document not found` in
  `userVerifications`) are newly-surfaced and not yet investigated. None
  of the three are introduced by bringing v5 into this repo — they're
  pre-existing in the v5 code itself. Don't treat new failures beyond
  these three as expected; investigate those.

Required Foxx configuration (`seed`, `operationsTimeWindow`,
`operationsLimit`, `appsOperationsLimit`) is passed automatically by the
script, matching the dev defaults above.

### If it fails

- **`docker build` fails on the base image or a package install**: check
  your network/Docker Desktop status first; these are pinned, previously-working
  versions.
- **`arangod failed to start`**: the script prints the ArangoDB log on
  failure — check for a port conflict on 8529 from another running
  container.
- **A `foxx install` error mentioning a configuration option**: a
  `manifest.json`/`manifest_apply.json` configuration section may have
  changed upstream; compare against the `-c` flags in
  `scripts/foxx-build-inner.sh`.
- **Test failures beyond the known ones above**: treat as a real
  regression — don't ship the rebuilt zips until it's understood.

### The tooling itself has its own (much faster) test

`scripts/build-foxx.sh`'s actual build/test logic lives in
`scripts/foxx-build-inner.sh`, which is also exercised directly (no Docker,
no `arangod`, sub-second) by `scripts/build-foxx.test.sh` against stubbed
tools. That test guards the *script's* control flow — e.g. that a failure
partway through can't silently cause a build to lose its own output, or
that a failure in one version can't silently prevent the other from being
attempted — not the real Foxx application behavior. See
[`scripts/README.md`](../scripts/README.md) for details and the convention
for adding more tooling tests.

## Running a full test server

Get the latest code:

```sh
git clone https://github.com/BrightID/BrightID-Node
cd BrightID-Node
# or, if you already have it:
git pull
```

Build and run the full stack (all services — `db`, `ws`, `scorer`,
`consensus_receiver`, `consensus_sender`, `updater`, `web`):

```sh
docker-compose build
docker-compose up -d
```
