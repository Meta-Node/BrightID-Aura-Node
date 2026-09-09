## Purpose

Bound how many completed, unconsumed consensus snapshot dumps sit on disk.
This bounds dump *count*, not the size of any single dump.

## ADDED Requirements

### Requirement: Bounded pending snapshots
`consensus_receiver` SHALL NOT create a new snapshot dump while the count of
completed snapshots — `dump_*_fnl` directories in `/snapshots` — is at or
above `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`. A `dump_*` directory without the
`_fnl` suffix does not count toward the cap.

#### Scenario: Catch-up after downtime
- **WHEN** the node crosses multiple `SNAPSHOTS_PERIOD` boundaries faster than
  the scorer consumes snapshots
- **THEN** `consensus_receiver` blocks before creating a new snapshot once the
  count is at or above the cap, and resumes when the count drops below the cap

### Requirement: Startup cleanup of unfinished dumps
On startup, before entering its main loop, `consensus_receiver` SHALL remove
any `dump_*` directory in `/snapshots` that lacks the `_fnl` suffix.

#### Scenario: Crash mid-dump
- **WHEN** `consensus_receiver` crashes after `arangodump` starts but before
  the directory is renamed to `dump_<block>_fnl`
- **THEN** on the next startup the unfinished `dump_<block>` directory is
  removed, reclaiming its disk

### Requirement: Reject a non-positive cap
`consensus_receiver` SHALL reject a configured
`BN_CONSENSUS_MAX_PENDING_SNAPSHOTS` of `0` or less at startup, exiting with
an error naming the invalid value.

#### Scenario: Misconfigured cap
- **WHEN** `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS` is set to `0` or a negative
  number
- **THEN** `consensus_receiver` exits at startup with an error naming the
  invalid value, rather than starting and blocking indefinitely
