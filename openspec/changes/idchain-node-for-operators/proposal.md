## Why

An Aura node talks to IDChain through `idchain.one` and nothing else: the updater hard-codes that URL, and the consensus receiver only handles IDChain blocks correctly when the URL contains `idchain`. There is no documented way to run your own chain source. I stood one up on 2026-09-09; this change makes it repeatable and closes the two code gaps.

This is two changes in one: the two code fixes (the URL and the PoA middleware) can land on their own, without the node package, if that is easier to approve.

## What Changes

- New `idchain/` directory: `Dockerfile`, `docker-compose.yml`, `idchain-genesis.json`, `static-nodes.json`. Builds `IDChain-eth/IDChain` tag `idc1.9.18` with `golang:1.14-alpine`; RPC on host loopback; p2p on `30329`.
- `updater/config.py`: `IDCHAIN_RPC_URL` comes from `BN_CONSENSUS_IDCHAIN_RPC_URL` instead of a literal.
- `consensus/receiver.py`: PoA middleware is always injected, not only when the URL contains `rinkeby` or `idchain`.
- `docs/installation-guide.md`: section "Running your own IDChain node" — build, init, key backup, inbound `30329`, contributing your enode, cutover with `BN_CONSENSUS_INFURA_URL`, `BN_CONSENSUS_IDCHAIN_RPC_URL`, `BN_UPDATER_IDCHAIN_WSS`, `BN_UPDATER_SEED_GROUPS_WS_URL`, and rollback.
- `idchain/static-nodes.json` is reviewed by pull request: added after a reviewer connects and fetches a block; removed after failing from two hosts on different days.

## Capabilities

### New Capabilities
- `idchain-node`: run an IDChain sync node from this repository and point an Aura node at it.

### Modified Capabilities
(none)

## Impact

Defaults are unchanged, so existing nodes behave as before; `consensus` and `updater` images need a rebuild to get the two fixes. An operator who adopts this keeps their Aura node advancing when `idchain.one` is unreachable, as long as their IDChain node has a peer. `BN_UPDATER_MAINNET_WSS` is Ethereum mainnet and is untouched. Validator setup is out of scope.
