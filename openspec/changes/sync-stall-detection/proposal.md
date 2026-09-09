## Why

`receiver.py` persists `LAST_BLOCK` and throws away the distance to the chain head every cycle. A node that has stopped applying blocks looks, from outside, exactly like one keeping up: `/state` reports no head, no lag, no RPC error. Operators find out from their users.

## What Changes

- `receiver.py`: publish `chainHead`, `syncLag`, `headAge`, `headRpcError`, `recoveryState`; a stall detector on its own thread; timeouts on every IDChain and Foxx call.
- Foxx `v5`/`v6`: `/state` gains the five fields.
- `config.py`, `config.env`, compose: the `BN_RECOVERY_*` detector settings.
- The database name `_recovery` is reserved for the recovery journal; nothing is created under it here. The detector's window is in memory and the five fields go to the existing `variables` collection, which nothing in this change replaces.

## Capabilities

### New Capabilities
- `sync-stall-detection`: a node reports its distance from the chain and says plainly when it has stopped advancing.

### Modified Capabilities
(none — this repository has no accepted specs yet)

## Out of scope / follow-up

`recoveryState` takes the values `ok` and `stalled` here. `recovering` and `failed` arrive with **`verified-restore-cutover`**, which also moves where the five fields are stored — a restore replaces `variables`, and status cannot live in the data being restored. Doing anything about a stalled node is that change; this one only reports.

## Impact

**Operators** get a stall signal they can alert on instead of inferring one from user complaints. Nothing else moves: no restore path, no new database, no worker behaves differently, no route gated.

**Clients** see five additive `/state` fields; the BrightID app does not change. Consuming them in the Aura status panel is a separate task outside this repository.
