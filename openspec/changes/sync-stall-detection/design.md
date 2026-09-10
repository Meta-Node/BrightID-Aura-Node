## Context

`getState()` (`web_services/foxx/v6/db.js`) reads `variables`; nothing here replaces it, so the detector's output can live there.

**Non-goals:** any restore path, the archive format, an automatic trigger, gating any route.

## Decisions

**D1 — A stall is no gain while the chain moves.** `recoveryState` becomes `stalled` when `syncLag` is at or above `BN_RECOVERY_MIN_LAG` and, in each of `BN_RECOVERY_STALL_WINDOWS` consecutive `BN_RECOVERY_CHECK_PERIOD` windows, `LAST_BLOCK` did not change **and** `chainHead` advanced by at least `BN_RECOVERY_MIN_HEAD_GAIN`. A node clearing a backlog at one block per window is progressing and stays `ok`. `headRpcError` suppresses the verdict.
Proposed defaults, from the 5 s block period and seven days of our node's samples (no legitimate iteration held `LAST_BLOCK` still for a full five minutes): `BN_RECOVERY_CHECK_PERIOD=60` (seconds), `BN_RECOVERY_STALL_WINDOWS=10`, `BN_RECOVERY_MIN_HEAD_GAIN=6` (blocks, half the nominal 12 per window), `BN_RECOVERY_MIN_LAG=60` (blocks). A verdict therefore takes ten minutes. Better values welcome; the snapshot dump is the longest legitimate iteration and must fit inside the stall window.
*Rejected:* a fixed distance threshold, or a wall-clock timeout — both measure the chain, not the node.

**D2 — The detector runs on its own thread and holds no durable state.** The long synchronous work is *inside* one block iteration (`receiver.py`, `save_snapshot()`), so a detector driven by the block loop goes quiet exactly when the node is worst off. It gets its own thread, a timeout on every IDChain and Foxx call, and an in-memory window a restart re-warms — which is why this change needs no database.
*Rejected:* a per-block heartbeat; persisting the window.

**D3 — Five fields, published where `/state` already looks.** The receiver writes `chainHead`, `syncLag` (`chainHead` minus `LAST_BLOCK`), `headAge`, `headRpcError` and `recoveryState` to `variables`; `v5` and `v6` serve them. `recoveryState` is `ok` or `stalled` and nothing else here.
*Rejected:* creating `_recovery` now, while nothing replaces `variables`; publishing `syncLag` alone and leaving each client its own threshold, which is how two clients come to disagree about whether a node is healthy.

## Risks / Trade-offs

- A crash-looping receiver never reaches a verdict; `headAge` still shows it.
- A receiver that exits and is not restarted never reaches a verdict either; `headAge` and `syncLag` still show it. Restart policy is `fresh-machine-build` (#37).
- One window in which the chain gains fewer than `BN_RECOVERY_MIN_HEAD_GAIN` blocks resets the count, so a stuck node behind a flapping chain is reported late. Accepted over summing gain across windows, which is harder to state.

## Migration Plan

Additive.
