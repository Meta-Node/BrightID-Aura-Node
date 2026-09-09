## Purpose

A node reports its distance from the chain and says plainly when it has stopped advancing.

## ADDED Requirements

### Requirement: Lag and chain health are reported separately
A node SHALL report `chainHead`, `syncLag`, `headAge`, `headRpcError` and `recoveryState` on `/state`. `recoveryState` SHALL take the value `ok` or `stalled` and no other, and SHALL be `stalled` only under the conditions defined in design D1.

#### Scenario: IDChain RPC is unreachable
- **WHEN** the node's IDChain RPC fails or times out
- **THEN** `headRpcError` is set, `recoveryState` is not `stalled`, and `/state` still answers

#### Scenario: Node gains a single block per window
- **WHEN** `syncLag` is above `BN_RECOVERY_MIN_LAG`, the chain is producing blocks, and the node applies one block per window
- **THEN** `recoveryState` stays `ok`, whereas a node whose `LAST_BLOCK` does not change becomes `stalled`

### Requirement: The detector reports independently of the block loop
The detector SHALL run on a thread of its own, per design D2, and every IDChain and Foxx call it makes SHALL have a timeout.

#### Scenario: Receiver is inside a long block iteration
- **WHEN** the receiver is blocked in `save_snapshot()`
- **THEN** `/state` continues to report a current `chainHead` and `headAge`
