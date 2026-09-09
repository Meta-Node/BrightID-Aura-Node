## Why

`consensus/receiver.py` calls `save_snapshot()` every `SNAPSHOTS_PERIOD` blocks; each call runs `arangodump` into `/snapshots/dump_<block>`, renamed to `dump_<block>_fnl` once the dump succeeds. `scorer/runner.py` consumes and deletes one `_fnl` snapshot at a time. When a node catches up after downtime the blocks inside one poll iteration are processed back-to-back, so the receiver crosses `SNAPSHOTS_PERIOD` boundaries far faster than the scorer clears snapshots and the `snapshots` volume fills; operators recover by deleting dump directories by hand, undocumented (upstream [BrightID-Node#366](https://github.com/BrightID/BrightID-Node/issues/366)). This change caps how many completed snapshots may be waiting — `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`, default `3` — and blocks the receiver at the cap instead of letting the disk fill.

## What Changes

- `consensus/receiver.py`: before creating a new snapshot, the receiver blocks while the count of completed snapshots — `dump_*_fnl` directories in `/snapshots` — is at or above `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`, and resumes when the count drops below the cap.
- `consensus/receiver.py`: on startup, before the main loop, it removes any `dump_*` directory in `/snapshots` that lacks the `_fnl` suffix — an unfinished dump left by a crash.
- New env var `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`, default `3`, in `config.env`; a value of `0` or less is rejected at startup with a clear error.
- `docs/installation-guide.md` gets a line noting the cap and the variable.

## Impact

- At the cap the receiver stops applying chain operations — block processing and snapshot creation — until the scorer consumes a snapshot. Node state goes stale instead of the disk filling; a wedged scorer now stalls the receiver.
- The cap bounds dump *count*, not size. One oversized `arangodump` can still fill the volume and still needs manual cleanup.
- An unfinished `dump_*` directory never counts toward the cap; startup cleanup reclaims its disk, it does not free a cap slot.
- Upgrade: the cap check and startup cleanup are receiver code, so they need a `consensus` image rebuild; changing the value afterwards only needs `docker compose up -d consensus_receiver`.
- The variable is optional, so existing `config.env` files keep working. No schema, database, or backup change.
