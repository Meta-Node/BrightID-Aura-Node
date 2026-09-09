## Decisions

**D1. Block the receiver on a pending-snapshot count cap rather than skipping
snapshots.** Before `save_snapshot()` the receiver counts `dump_*_fnl`
directories in `/snapshots` — the completed dumps `next_snapshot()` selects in
`scorer/runner.py` — and blocks, sleeping and rechecking, while the count is at
or above `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`; it resumes when the count drops
below the cap. Blocking preserves every snapshot. *Rejected:* skip the
snapshot, or delete the oldest pending dump — both discard a snapshot the
scorer has not verified.

**D2. New env var `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`, default `3`.** Three is
a small round default — one snapshot mid-restore plus one queued. It is not
derived from measured dump sizes, which vary by deployment; operators size it
against their own volume. *Rejected:* a hard-coded constant — widening the
buffer would need a code change.

**D3. On startup, remove `dump_*` directories that lack the `_fnl` suffix.** A
crash between `arangodump` starting and the rename leaves an unfinished
directory that `next_snapshot()` never selects and D1's count never includes:
disk waste, not a cap occupant. `consensus_receiver` is the only process that
creates `dump_*` directories, and the scorer removes only `_fnl` directories it
has consumed, so the cleanup cannot race it. *Rejected:* leave orphans to the
operator — they accumulate silently.

**D4. Reject a configured cap of `0` or less at startup.** At `0` the count is
always at or above the cap, so the receiver would block forever; negatives are
meaningless. It exits with an error naming the value. *Rejected:* clamp
silently to `1` — hides the mistake.

## Risks / Trade-offs

- A stuck scorer stalls the receiver indefinitely instead of filling the disk.
  That is the intended trade.
- Startup cleanup relies on no other process or manual step ever creating a
  `dump_*` directory under `/snapshots`.
