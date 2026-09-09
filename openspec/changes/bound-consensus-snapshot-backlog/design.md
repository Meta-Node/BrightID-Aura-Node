## Context

`consensus/receiver.py` `main()`'s outer loop sleeps 1 second every
iteration (rate-limiting the Ethereum RPC call), plus a further 3 seconds
whenever there are new confirmed blocks to process (a workaround for a
`getBlock` timing bug, per the code comment). Neither delay applies between
the individual blocks processed within one iteration's
`range(last_block + 1, confirmed_block + 1)` loop, so during a long catch-up
many blocks — and the `save_snapshot()` calls at `SNAPSHOTS_PERIOD`
boundaries among them — go by back-to-back with no delay. `save_snapshot()`
dumps to `dump_<block>` and renames to `dump_<block>_fnl` only once
`arangodump` succeeds; there is no check on how many prior dumps are still
unprocessed. `scorer/runner.py` `process()` handles one `_fnl` snapshot at a
time — `arangorestore`, verify, `shutil.rmtree` — and only then looks for the
next one. During normal operation the two stay roughly in step. During a long
catch-up after downtime, the receiver can pass many `SNAPSHOTS_PERIOD`
boundaries before the scorer finishes even one snapshot, and every dump
written in between stays on disk until consumed.

## Goals / Non-Goals

**Goals:** cap the number of unconsumed snapshots a backlog can accumulate on
disk; keep normal (caught-up) operation unaffected; no change to what gets
verified; recover cleanly from a dump left unfinished by a crash.

**Non-Goals:** changing the scorer's processing rate; changing
`SNAPSHOTS_PERIOD` itself; bounding the size of any single dump (a count cap
bounds how many completed dumps can pile up, not how large one is — an
oversized single dump is out of scope here).

## Decisions

**D1. Block the receiver on a pending-snapshot count cap, rather than
skipping snapshots.** Before `save_snapshot()`, count `dump_*_fnl` directories
under `/snapshots` — the same completed-dump entries `scorer/runner.py`'s
`next_snapshot()` selects; an in-progress `dump_<block>` directory without the
suffix is never counted. The receiver blocks while the count of completed
snapshots is at or above `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`, sleeping and
rechecking, and resumes once it drops below the cap. Skipping a periodic
snapshot would leave a gap in `VERIFICATIONS_HASHES`/`PREV_SNAPSHOT_TIME` that
other verifiers rely on; blocking preserves every snapshot and only changes
how fast the receiver gets ahead of the scorer, which is exactly the failure
mode in the issue. *Alternative rejected:* delete the oldest pending dump
instead of blocking — that would silently drop a snapshot the scorer hasn't
verified yet.

**D2. New env var `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`, default `3`.** Three
gives headroom for normal jitter (a snapshot mid-restore plus one queued)
without the volume filling past ~3 dumps' worth of a stalled scorer.
Configurable per-deployment because dump size and volume size vary.
*Alternative rejected:* a hard-coded constant — an operator with more disk or
a slower scorer has no way to widen the buffer without a code change.

**D3. On startup, remove non-`_fnl` `dump_*` directories before counting;
reject a configured cap ≤ 0.** A crash inside `save_snapshot()` (between
`arangodump` starting and the rename to `_fnl`) leaves an unfinished
`dump_<block>` directory that `next_snapshot()` never selects and D1's count
never includes — so it sits on disk forever without affecting the cap, which
is correct for the cap but still wastes space and, at cap `1`, was previously
indistinguishable from a stuck scorer. On process start, before entering the
main loop, the receiver lists `/snapshots` and removes any `dump_*` directory
that lacks the `_fnl` suffix; `consensus_receiver` is the only writer to
`/snapshots`, so this is safe — nothing else creates or expects to find an
in-progress dump directory across a restart. Separately, a cap of `0` or
negative would either block forever (the count-of-completed-dumps precondition
can never be satisfied while the cap counts against it, since even zero
completed dumps would still be "at or above" a cap of `0`) or is simply
meaningless; the receiver validates `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS > 0` at
startup and exits with a clear error otherwise. *Alternative rejected:* leave
orphan cleanup to the operator — orphans don't count toward the cap and so
can't recreate the backlog deadlock, but left alone they accumulate
indefinitely, wasting disk and confusing operators trying to read
`/snapshots` state during an incident.

## Risks / Trade-offs

- A stuck scorer (not just a slow one) now stalls the receiver indefinitely
  instead of filling the disk. That is the intended trade: an operator
  diagnosing a wedged scorer is better than one recovering a full disk.
- The count check (`os.listdir`) runs once per block-processing iteration
  during catch-up; negligible cost next to `arangodump`/`arangorestore`.
- Startup orphan cleanup deletes a `dump_*` directory unconditionally once
  it lacks `_fnl`; this is correct given the receiver is the sole writer, but
  relies on that invariant holding (no other process or manual step should
  ever create a `dump_*` directory under `/snapshots`).

## Migration Plan

No data migration. `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS` defaults if unset, so
existing `config.env` files need no edit to keep working; operators who want
a different cap add the variable and recreate the `consensus_receiver`
container (see Impact in `proposal.md` — the cap-check code itself needs a
rebuild once, adjusting the value afterward does not). On first start after
upgrade, the receiver's startup cleanup also removes any orphaned non-`_fnl`
`dump_*` directories left behind by earlier crashes, if present.
