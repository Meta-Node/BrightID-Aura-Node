## Why

`consensus/receiver.py` calls `save_snapshot()` every `SNAPSHOTS_PERIOD` blocks; each call runs `arangodump` into `/snapshots/dump_<block>`, renamed to `dump_<block>_fnl` once the dump succeeds. `scorer/runner.py` consumes one `_fnl` snapshot at a time, oldest first, deleting each once processed. When a node catches up after downtime the blocks inside one poll iteration are processed back-to-back, so the receiver crosses `SNAPSHOTS_PERIOD` boundaries far faster than the scorer clears snapshots and the `snapshots` volume fills; operators recover today by deleting dump directories by hand and letting the scorer skip straight to current data, undocumented (upstream [BrightID-Node#366](https://github.com/BrightID/BrightID-Node/issues/366)). This change automates that: the scorer always processes the newest snapshot, deleting stale ones as it goes, and a bounded cap (`BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`, default `3`) deletes the oldest pending dump if the scorer stops running entirely — the receiver itself never pauses.

## What Changes

- `scorer/runner.py`: `next_snapshot()` selects the newest completed (`dump_*_fnl`) snapshot instead of the oldest, deleting every other completed snapshot it finds at that point.
- `consensus/receiver.py`: before creating a new snapshot, if the count of completed snapshots — `dump_*_fnl` directories in `/snapshots` — is at or above `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`, the receiver deletes the oldest one(s) down to below the cap. Block processing and operation application never pause.
- `consensus/receiver.py`: on startup, before the main loop, it removes any `dump_*` directory in `/snapshots` that lacks the `_fnl` suffix — an unfinished dump left by a crash.
- New env var `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`, default `3`, in `config.env`; a value of `0` or less is rejected at startup with a clear error.
- `docs/installation-guide.md` gets a line noting the cap and the variable.

## Impact

- The receiver never stalls: it keeps applying chain operations and creating snapshots regardless of scorer backlog. During a backlog, verifications for intermediate blocks are simply never computed — the scorer jumps straight to whatever's newest, matching what recomputation from a snapshot already guarantees (nothing depends on having processed the ones in between).
- The cap bounds dump *count* as a backstop for a fully-stopped scorer, not size. One oversized `arangodump` can still fill the volume and still needs manual cleanup.
- An unfinished `dump_*` directory never counts toward the cap; startup cleanup reclaims its disk, it does not free a cap slot.
- Upgrade: this touches both `consensus` and `scorer` images, so both need a rebuild; changing the cap value afterwards only needs `docker compose up -d consensus_receiver`.
- The variable is optional, so existing `config.env` files keep working. No schema, database, or backup change.
