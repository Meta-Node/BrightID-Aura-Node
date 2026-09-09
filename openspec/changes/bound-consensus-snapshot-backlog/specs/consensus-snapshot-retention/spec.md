## Purpose

Bound the number of completed, unconsumed consensus snapshot dumps kept on
disk, so a node catching up after downtime cannot accumulate an unbounded
backlog of them. This bounds dump *count*, not the size of any single dump —
an oversized individual `arangodump` is out of scope.

## ADDED Requirements

### Requirement: Bounded pending snapshots
`consensus_receiver` SHALL NOT create a new snapshot dump while the count of
completed snapshots — `dump_*_fnl` directories in `/snapshots` — is at or
above `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`. A `dump_*` directory without the
`_fnl` suffix (a dump in progress, or left unfinished by a crash) does not
count toward the cap.

#### Scenario: Catch-up after downtime
- **WHEN** the node reconnects after being offline long enough to cross
  multiple `SNAPSHOTS_PERIOD` boundaries in quick succession
- **THEN** `consensus_receiver` blocks before starting a new snapshot once
  the count of completed snapshots reaches the configured cap, and resumes
  once the scorer has consumed one

#### Scenario: Default behavior unchanged for normal operation
- **WHEN** the scorer keeps pace with the receiver, as in ordinary operation
- **THEN** the count of completed snapshots stays below the cap and blocks
  are processed without added delay

### Requirement: Startup cleanup of unfinished dumps
On startup, before entering its main loop, `consensus_receiver` SHALL remove
any `dump_*` directory in `/snapshots` that lacks the `_fnl` suffix.

#### Scenario: Crash mid-dump
- **WHEN** `consensus_receiver` crashes after `arangodump` starts but before
  the directory is renamed to `dump_<block>_fnl`
- **THEN** on the next startup, the orphaned `dump_<block>` directory is
  removed before the count of completed snapshots is evaluated, so it cannot
  permanently occupy a cap slot

### Requirement: Reject a non-positive cap
`consensus_receiver` SHALL reject a configured
`BN_CONSENSUS_MAX_PENDING_SNAPSHOTS` value of `0` or less at startup, with a
clear error, instead of starting with a cap that can never be satisfied.

#### Scenario: Misconfigured cap
- **WHEN** `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS` is set to `0` or a negative
  number
- **THEN** `consensus_receiver` exits at startup with an error naming the
  invalid value, rather than starting and blocking indefinitely
