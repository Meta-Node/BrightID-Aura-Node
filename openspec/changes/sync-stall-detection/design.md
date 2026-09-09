## Context

`getState()` (`web_services/foxx/v6/db.js:833`) reads `variables`. Nothing here replaces it, so the detector's output can live there; the change that restores the graph will have to move it.

**Non-goals:** any restore path, the archive format, an automatic trigger, gating any route.

## Decisions

**D1 — A stall is no gain while the chain moves.** `recoveryState` becomes `stalled` when `syncLag` is at or above `BN_RECOVERY_MIN_LAG` and, in each of `BN_RECOVERY_STALL_WINDOWS` consecutive `BN_RECOVERY_CHECK_PERIOD` windows, `LAST_BLOCK` did not change **and** `chainHead` advanced by at least `BN_RECOVERY_MIN_HEAD_GAIN`. No gain, not low throughput: a node clearing a backlog at one block per window is progressing and stays `ok`. `headRpcError` suppresses the verdict, so an RPC outage is never read as a stall.
*Rejected:* a fixed distance threshold; a wall-clock timeout (measures the chain, not the node).

**D2 — The detector runs on its own thread and holds no durable state.** The long synchronous work is *inside* one block iteration (`save_snapshot()`, `receiver.py:144`), so a detector driven by the block loop goes quiet exactly when the node is worst off. It gets a thread of its own, a timeout on every IDChain and Foxx call, and an in-memory window: a restart re-warms it rather than reading a journal, which is why this change needs no database.
*Rejected:* a per-block heartbeat; persisting the window.

**D3 — Five fields, published where `/state` already looks.** The receiver writes `chainHead`, `syncLag` (`chainHead` minus `LAST_BLOCK`), `headAge`, `headRpcError` and `recoveryState` to `variables`; `v5` and `v6` serve them. `recoveryState` is `ok` or `stalled` and nothing else here. Reporting is the whole of it.
*Rejected:* a `_recovery` database now (ceremony while nothing replaces `variables`); publishing `syncLag` alone and leaving each client its own threshold, which is how two clients come to disagree about whether a node is healthy.

## Risks / Trade-offs

- Thresholds are operator-tunable, so a badly chosen `BN_RECOVERY_MIN_HEAD_GAIN` can hide a stall; defaults ship in `config.env`.
- A crash-looping receiver never reaches a verdict; `headAge` still shows it.

## Migration Plan

Additive. A node keeping up sees only the new `/state` fields.
