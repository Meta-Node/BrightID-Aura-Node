# scripts/

Tooling for this repo, as opposed to the Foxx application code it builds and
deploys. This is a different kind of code from `web_services/foxx/brightid/`
and has its own, lighter test convention — see below.

## build-foxx.sh

Builds `web_services/foxx/brightid6.zip` and `apply6.zip` from
`web_services/foxx/brightid` source, and runs the `brightid6` Mocha test
suite (`foxx test`). Everything runs inside a container matching production's
ArangoDB version and Alpine/musl runtime (see `foxx-builder.Dockerfile`), so
native modules (`keccak`, `secp256k1`) match the deployed environment rather
than whatever platform the developer is on.

```
scripts/build-foxx.sh
```

Zips are written regardless of whether `foxx install`/`foxx test` succeed —
a build that produces valid zips but hits a pre-existing test failure
shouldn't lose the zips. The script's exit code reflects the test result
(0 = all passed), so CI can still gate on it while a human decides whether to
ship zips built alongside a known failure.

The actual build/install/test logic lives in `foxx-build-inner.sh`, which
`build-foxx.sh` mounts into the container and runs. It's a separate file
specifically so it can also run directly on the host, outside docker,
against stubbed tools — that's what `build-foxx.test.sh` does.

## build-foxx.test.sh

A control-flow regression test for `foxx-build-inner.sh` — no docker, no
`arangod`, runs in under a second. It stubs `arangod`/`arangosh`/`npm`/`foxx`
on `PATH` (see `test-stubs/`) and runs the real inner script against a small
fake Foxx source tree, then asserts the zips it builds always get written to
the output directory regardless of what happens afterward — even if
`foxx install` or `foxx test` fail.

```
scripts/build-foxx.test.sh
```

This exists because of a real bug: an earlier version of the script copied
the built zips out *after* `foxx install`/`foxx test`, both running under
`set -e`. A failure in either one aborted the script before the already-built
zips were ever written to the host, silently losing valid build output. This
test pins the fix (zips are written before anything that could fail
downstream) so that ordering can't quietly regress.

**What this test does not cover**: it stubs out `arangod`/`npm`/`foxx`
entirely, so it says nothing about whether the real docker image builds,
whether `arangod` actually starts, whether `npm ci` produces working native
modules, or whether the Foxx test suite itself passes. Only a real run of
`build-foxx.sh` proves that. Use this test to catch control-flow regressions
in the script cheaply and often; use a real `build-foxx.sh` run before
trusting a merge/release.

## test-stubs/

Fake `arangod`, `arangosh`, `npm`, and `foxx` executables used only by
`build-foxx.test.sh`, prepended onto `PATH` for that test's duration. `foxx`
supports two env vars to simulate failure on demand:

- `FOXX_FAIL_INSTALL=1` — `foxx install ...` exits 1
- `FOXX_FAIL_TEST=<n>` — `foxx test ...` exits `<n>`

## Adding more tooling tests

If more scripts get added here, the convention is: `<name>.sh` for the
tool, `<name>.test.sh` for a stub-based test of its control flow (not its
real external dependencies), following the same pattern as
`build-foxx.sh`/`build-foxx.test.sh`. Shared fake executables can move into
`test-stubs/` if more than one test needs the same stub.
