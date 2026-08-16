# scripts/

Tooling for this repo, as opposed to the Foxx application code it builds and
deploys. This is a different kind of code from `web_services/foxx/v5/` and
`v6/` and has its own, lighter test convention — see below.

## build-foxx.sh

Builds all four Foxx deployment zips — `brightid5.zip`/`apply5.zip` from
`web_services/foxx/v5`, and `brightid6.zip`/`apply6.zip` from
`web_services/foxx/v6` — and runs each version's Mocha test suite
(`foxx test`). Everything runs inside a container matching production's
ArangoDB version and Alpine/musl runtime (see `foxx-builder.Dockerfile`), so
native modules (`keccak`, `secp256k1`) match the deployed environment rather
than whatever platform the developer is on.

```
scripts/build-foxx.sh
```

v6 installs into ArangoDB's default `_system` database. v5 gets its own
database for the test run only, purely to keep one version's Mocha suite
from polluting the other's fixtures via shared collections — production
runs both against the same database, since they share one social graph.
A build/install failure in one version never prevents the other from
being attempted.

Zips are written regardless of whether `foxx install`/`foxx test` succeed —
a build that produces valid zips but hits a pre-existing test failure
shouldn't lose the zips. The script's exit code reflects the combined test
result across both versions (0 = all passed), so CI can still gate on it
while a human decides whether to ship zips built alongside a known failure.

The actual build/install/test logic lives in `foxx-build-inner.sh`, which
`build-foxx.sh` mounts into the container and runs. It's a separate file
specifically so it can also run directly on the host, outside docker,
against stubbed tools — that's what `build-foxx.test.sh` does.

## build-foxx.test.sh

A control-flow regression test for `foxx-build-inner.sh` — no docker, no
`arangod`, runs in under a second. It stubs `arangod`/`arangosh`/`npm`/`foxx`
on `PATH` (see `test-stubs/`) and runs the real inner script against small
fake v5/v6 source trees, then asserts:

- the zips it builds always get written to the output directory regardless
  of what happens afterward — even if `foxx install` or `foxx test` fail;
- a build/install failure in one version never prevents the other version
  from being attempted.

```
scripts/build-foxx.test.sh
```

This exists because of two real bugs, both the same failure class one level
apart:

1. An earlier version of the script copied the built zips out *after*
   `foxx install`/`foxx test`, both running under `set -e`. A failure in
   either one aborted the script before the already-built zips were ever
   written to the host, silently losing valid build output.
2. Once v5 support was added, each version's build+install+test ran as one
   `set -e`-protected sequence — so a v6 install failure would abort the
   whole script before v5 was ever attempted, and vice versa.

Both are pinned here: zips are written before anything that could fail
downstream, and each version's build/install is independently wrapped so a
failure in one can't cascade and skip the other.

**What this test does not cover**: it stubs out `arangod`/`npm`/`foxx`
entirely, so it says nothing about whether the real docker image builds,
whether `arangod` actually starts, whether `npm ci` produces working native
modules, or whether either version's Foxx test suite itself passes. Only a
real run of `build-foxx.sh` proves that. Use this test to catch control-flow
regressions in the script cheaply and often; use a real `build-foxx.sh` run
before trusting a merge/release.

## test-stubs/

Fake `arangod`, `arangosh`, `npm`, and `foxx` executables used only by
`build-foxx.test.sh`, prepended onto `PATH` for that test's duration. `foxx`
supports env vars to simulate failure on demand:

- `FOXX_FAIL_INSTALL=1` — `foxx install ...` exits 1, for any mount
- `FOXX_FAIL_INSTALL_MOUNT=X` — `foxx install ...` exits 1 only when a
  mount argument contains `X` (e.g. `6`, to fail only v6's installs)
- `FOXX_FAIL_TEST=<n>` — `foxx test ...` exits `<n>`

## Adding more tooling tests

If more scripts get added here, the convention is: `<name>.sh` for the
tool, `<name>.test.sh` for a stub-based test of its control flow (not its
real external dependencies), following the same pattern as
`build-foxx.sh`/`build-foxx.test.sh`. Shared fake executables can move into
`test-stubs/` if more than one test needs the same stub.
