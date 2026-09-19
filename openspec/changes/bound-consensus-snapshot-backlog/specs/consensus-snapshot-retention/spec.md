## Purpose

Keep consensus verifications current during a snapshot backlog without ever
pausing chain-operation ingestion, and bound disk use if the scorer stops
running entirely.

## ADDED Requirements

### Requirement: Scorer prefers the newest snapshot
`scorer/runner.py` SHALL select the newest completed snapshot — the
`dump_*_fnl` directory with the highest block number — to process next, and
SHALL delete every other completed snapshot found at that point without
processing it.

#### Scenario: Backlog of completed snapshots
- **WHEN** more than one `dump_*_fnl` directory exists in `/snapshots`
- **THEN** the scorer processes only the one with the highest block number,
  and deletes the rest without restoring or verifying them

#### Scenario: Normal operation
- **WHEN** exactly one completed snapshot exists
- **THEN** it is processed as before, with no behavior change

### Requirement: Processing a snapshot never deletes its own verifications
`scorer/runner.py` SHALL NOT prune verifications at a block higher than the
snapshot it has just processed.

#### Scenario: VERIFICATION_BLOCK left ahead of the snapshot
- **WHEN** `VERIFICATION_BLOCK` holds a block number higher than the snapshot
  being processed — as a snapshot left in `/snapshots` across a database
  re-initialization leaves it, since its block belongs to a timeline the
  database no longer occupies
- **THEN** the verifications written for the snapshot just processed survive,
  and only verifications below that snapshot's block are removed

This requirement covers the rows in the collection, not which block the API
answers from. The served block is the highest key in `VERIFICATIONS_HASHES`,
which a stale snapshot also sets and this requirement does not address.

### Requirement: Receiver never blocks on snapshot backlog
`consensus_receiver` SHALL continue applying chain operations and creating
snapshots at every `SNAPSHOTS_PERIOD` boundary regardless of how many
completed snapshots are pending.

#### Scenario: Scorer stopped or far behind
- **WHEN** the count of completed snapshots — `dump_*_fnl` directories in
  `/snapshots` — is at or above `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`
- **THEN** `consensus_receiver` deletes the oldest completed snapshot(s) until
  the count is below the cap, then creates the new snapshot and continues the
  main loop without pausing block processing

### Requirement: Startup cleanup of unfinished dumps
`consensus_receiver` SHALL remove any `dump_*` directory in `/snapshots` that
lacks the `_fnl` suffix, on startup, before entering its main loop.

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
  invalid value, rather than starting and deleting every snapshot as fast as
  it's created
