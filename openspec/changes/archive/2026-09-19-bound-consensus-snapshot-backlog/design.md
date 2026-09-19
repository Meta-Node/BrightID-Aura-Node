## Decisions

**D1. Bound the backlog by deleting the oldest pending snapshot, never by
blocking the receiver.** Before `save_snapshot()`, if the count of completed
`dump_*_fnl` directories in `/snapshots` is at or above
`BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`, the receiver deletes the oldest one(s)
until it's below the cap, then proceeds — block processing and operation
application never pause. Every verifier recomputes its output fully from
whichever snapshot it reads (`scorer/verifications/*.py` take no prior
snapshot's results as input), so a snapshot superseded by a newer one carries
nothing the newer one doesn't already have; deleting it loses no information a
correct node needs. *Rejected:* blocking the receiver (the prior D1) — chain-
operation ingestion must never stall on the scorer's pace, or a wedged or
merely slow scorer stalls consensus itself, not just scoring.

**D2. The scorer processes the newest completed snapshot, not the oldest,
deleting superseded ones as it goes.** `scorer/runner.py`'s `next_snapshot()`
currently sorts ascending and returns the first (oldest) `_fnl` directory, so
a backlog is worked through in order even though only the newest snapshot's
results matter once a newer one exists. Change it to select the newest,
deleting every other completed snapshot found at that point. This is what
actually keeps verifications caught up during a backlog; D1's cap only bounds
worst-case disk use for a scorer that has stopped running entirely, not one
that's merely behind. *Rejected:* leave `next_snapshot()` oldest-first and
rely on D1 alone — the scorer would still burn through every stale snapshot in
a backlog before reaching current data, even with the count bounded.

**D3. New env var `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`, default `3`.** A
backstop against a scorer that has stopped running altogether, not the
mechanism for ordinary catch-up (that's D2). Three is a small round default;
not derived from measured dump sizes, which vary by deployment — operators
size it against their own volume. *Rejected:* a hard-coded constant —
widening the buffer would need a code change.

**D4. On startup, remove `dump_*` directories that lack the `_fnl` suffix.** A
crash between `arangodump` starting and the rename leaves an unfinished
directory that neither `next_snapshot()` (D2) nor the cap count (D1) ever
selects: disk waste, not a cap occupant. `consensus_receiver` is the only
process that creates `dump_*` directories, and the scorer removes only `_fnl`
directories it has consumed, so the cleanup cannot race it. *Rejected:* leave
orphans to the operator — they accumulate silently.

**D5. Reject a configured cap of `0` or less at startup.** At `0`, D1 would
delete every completed snapshot as fast as the receiver creates them,
including ones the scorer hasn't had a chance to read yet; negatives are
meaningless. It exits with an error naming the value. *Rejected:* clamp
silently to `1` — hides the mistake.

## Risks / Trade-offs

- A stuck or merely slow scorer no longer stalls the receiver. Older
  unconsumed snapshots get deleted instead — by D2 during ordinary catch-up,
  by D1's cap if the scorer has stopped entirely — so their verifications are
  simply never computed. Only the newest verifications matter, so this is a
  data-freshness trade, not a correctness one: a fully-stopped scorer still
  means verifications stop advancing, same as before.
- D2 changes normal-operation behavior slightly, not just catch-up: if two
  completed snapshots ever exist at once for any reason, the scorer now
  always prefers the newer, where before it processed both in order.
- Startup cleanup relies on no other process or manual step ever creating a
  `dump_*` directory under `/snapshots`.
