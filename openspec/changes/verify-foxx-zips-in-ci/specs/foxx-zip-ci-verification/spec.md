## Purpose

Give CI proof that the Foxx deployment zips committed to the repo match the
source they claim to be built from, on top of packaging that is made
deterministic first so that proof is meaningful.

## ADDED Requirements

### Requirement: Zip packaging is deterministic
Building `brightid5.zip`, `apply5.zip`, `brightid6.zip`, and `apply6.zip`
twice, independently, from the same unchanged source tree, inside the
pinned builder image, SHALL produce byte-for-byte identical zips — same
bytes, same dereferenced symlinks, same permission bits as the archives
committed today.

#### Scenario: Two independent builds, same source
- **WHEN** `scripts/build-foxx.sh` is run twice from independent clean
  checkouts of the same commit, using the pinned builder image
- **THEN** each of the four zips produced by the first run is byte-for-byte
  identical to the corresponding zip produced by the second run

### Requirement: CI verifies committed zips match source
A CI workflow SHALL rebuild `brightid5.zip`, `apply5.zip`, `brightid6.zip`,
and `apply6.zip` from `web_services/foxx/v5` and `web_services/foxx/v6` on
every push and pull request that touches `web_services/foxx/**`,
`scripts/build-foxx.sh`, `scripts/foxx-build-inner.sh`,
`scripts/foxx-builder.Dockerfile`, or the workflow file itself, and SHALL
fail the check if any rebuilt zip differs byte-for-byte from the committed
one.

#### Scenario: Source changed, zip not rebuilt
- **WHEN** a pull request edits a file under `web_services/foxx/v6` without
  updating `web_services/foxx/brightid6.zip`
- **THEN** the CI check fails, naming the mismatched zip

#### Scenario: Zip rebuilt and committed correctly
- **WHEN** a pull request edits Foxx source and its author re-runs
  `scripts/build-foxx.sh` and commits the resulting zips
- **THEN** the CI check passes

#### Scenario: Build-script change not covered by source-path filters alone
- **WHEN** a pull request edits `scripts/foxx-build-inner.sh` or
  `scripts/foxx-builder.Dockerfile` without touching `web_services/foxx/**`
- **THEN** the CI check still runs, because the workflow's path filters
  include those files

### Requirement: Build artifacts on tag
On a tag push, the CI workflow SHALL upload the freshly built zips as
workflow artifacts (GitHub Actions build artifacts attached to the run), in
addition to running the verification check.

#### Scenario: Release tag
- **WHEN** a tag is pushed
- **THEN** the four zips are attached to that workflow run as downloadable
  workflow artifacts
