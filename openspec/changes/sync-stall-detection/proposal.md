## Why

`receiver.py` records `LAST_BLOCK` each cycle and keeps nothing about the distance to the chain head. A node that has stopped applying blocks looks, from outside, exactly like one keeping up: `/state` reports no head, no lag, no RPC error. Operators find out from their users.

## What Changes

- `receiver.py`: the five fields, plus a stall detector on its own thread with timeouts on every IDChain and Foxx call.
- Foxx `v5`/`v6`: `/state` gains `chainHead`, `syncLag`, `headAge`, `headRpcError` and `recoveryState`.
- `config.py`, `config.env`, compose: the `BN_RECOVERY_*` detector settings.
- `_recovery` is reserved as the recovery journal's database name; nothing is created under it here.

## Capabilities

### New Capabilities
- `sync-stall-detection`: a node reports its distance from the chain and says plainly when it has stopped advancing.

## Out of scope / follow-up

`recoveryState` carries only `ok` and `stalled` here; `recovering` and `failed` arrive with **`verified-restore-cutover`**, which also moves the five fields out of `variables`. Acting on a stalled node is that change.

## Impact

- **Operators** get a stall signal they can alert on instead of inferring one from user complaints.
- **Clients** see five additive `/state` fields; the BrightID app does not change.
- Nothing else moves: no restore path, no new database, no worker behaviour, no route gated.
