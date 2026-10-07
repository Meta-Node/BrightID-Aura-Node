## ADDED Requirements

### Requirement: Zip packaging is deterministic
Building `brightid5.zip`, `apply5.zip`, `brightid6.zip`, and `apply6.zip`
twice, independently, from the same unchanged source tree inside the pinned
builder image, SHALL produce byte-for-byte identical zips — `cmp` reports no
difference between the two runs' output.

#### Scenario: Two independent builds, same source
- **WHEN** `scripts/build-foxx.sh` is run twice from independent clean
  checkouts of the same commit, using the pinned builder image
- **THEN** each of the four zips from the first run is byte-for-byte identical
  to the corresponding zip from the second run

### Requirement: CI verifies committed zips match source
A CI workflow SHALL rebuild `brightid5.zip`, `apply5.zip`, `brightid6.zip`, and
`apply6.zip` on every push and pull request touching `web_services/foxx/**`,
`scripts/build-foxx.sh`, `scripts/foxx-build-inner.sh`,
`scripts/foxx-builder.Dockerfile`, or the workflow file itself, and SHALL fail
the check, naming the mismatched zip, if any rebuilt zip differs byte-for-byte
from the committed one.

#### Scenario: Source changed, zip not rebuilt
- **WHEN** a pull request edits a file under `web_services/foxx/v6` without
  updating `web_services/foxx/brightid6.zip`
- **THEN** the CI check fails, naming the mismatched zip

#### Scenario: Zip rebuilt and committed
- **WHEN** a pull request edits Foxx source, re-runs `scripts/build-foxx.sh`,
  and commits the resulting zips
- **THEN** the CI check passes

#### Scenario: Packaging change with no source change
- **WHEN** a pull request edits `scripts/foxx-build-inner.sh` or
  `scripts/foxx-builder.Dockerfile` without touching `web_services/foxx/**`
- **THEN** the CI check still runs, because the workflow's path filters include
  those files
