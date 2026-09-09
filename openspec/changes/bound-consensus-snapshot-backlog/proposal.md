## Why

When a node reconnects after being offline, `consensus_receiver` catches up through many blocks with no delay between them (`consensus/receiver.py` `main()`), calling `save_snapshot()` every `SNAPSHOTS_PERIOD` blocks. Each call runs `arangodump` into a new `/snapshots/dump_<block>` directory, then renames it to `dump_<block>_fnl` once the dump succeeds. `scorer/runner.py` consumes and deletes one completed (`_fnl`) snapshot at a time (`process()`, `next_snapshot()`), so during a long catch-up the receiver can produce dumps faster than the scorer removes them, filling the `snapshots` volume — a count cap bounds how many completed dumps can pile up, though it does not bound the size of any single dump. Operators recover by manually deleting dump directories, undocumented (upstream [BrightID-Node#366](https://github.com/BrightID/BrightID-Node/issues/366)).

## What Changes

- `consensus/receiver.py`: before creating a new snapshot, `save_snapshot()`'s caller blocks while the count of completed snapshots (`dump_*_fnl` directories in `/snapshots`) is at or above a cap, so the receiver never gets more than a bounded number of unconsumed snapshots ahead of the scorer.
- On startup, the receiver removes any `dump_*` directory left without the `_fnl` suffix (an unfinished dump orphaned by a crash mid-dump) before it starts counting — it is the only writer to `/snapshots`, so this is safe. Only `_fnl` directories count toward the cap.
- The cap is a new env var, `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`, with a documented default; the receiver rejects a configured value ≤ 0 at startup with a clear error. Added to `config.env`.
- `docs/installation-guide.md` gets a line noting the bound and the variable.

## Capabilities

### New Capabilities
- `consensus-snapshot-retention`: bounding disk use of consensus snapshot dumps during catch-up.

### Modified Capabilities
(none)

## Impact

Operators: once pending completed snapshots reach the cap, the receiver stops applying subsequent chain operations (block processing, snapshot creation) until the scorer consumes one — node state goes stale rather than the disk filling. This bounds how many completed dumps can pile up, including removing the orphaned-directory case a crash mid-dump used to leave behind, but it does not bound the size of any single dump; an oversized dump can still fill the volume and still needs manual cleanup. Upgrade: this change's receiver code (the cap check and startup cleanup) needs a `consensus` image rebuild; after that, changing `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS` only needs a container recreation (`docker compose up -d consensus_receiver`), since `config.env` is supplied at runtime, not baked into the image. `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS` is optional (defaulted) so existing `config.env` files keep working. No schema or database change; no backup impact.
