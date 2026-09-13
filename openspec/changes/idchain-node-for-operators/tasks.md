## 1. Node files

- [ ] 1.1 Add `idchain/Dockerfile`, `idchain/docker-compose.yml`, `idchain/idchain-genesis.json`, `idchain/static-nodes.json` (entries per D4 only). Verify: `docker compose -f idchain/docker-compose.yml build` succeeds on a clean checkout; the build log records commit and digest.
- [ ] 1.2 Start from the committed files. Verify every spec scenario except cutover: chain id, peers, checkpoint hashes at 1 and 4,000,000, loopback-only on both transports, restricted methods on both transports, identity after recreate.

## 2. Code

- [ ] 2.1 `updater/config.py`: `IDCHAIN_RPC_URL = os.environ['BN_CONSENSUS_IDCHAIN_RPC_URL']`. Verify: `docker compose build updater` and the updater starts against the default.
- [ ] 2.2 `consensus/receiver.py`: inject PoA middleware unconditionally. Verify: `docker compose build consensus` and `consensus_receiver` advances against the default.

## 3. Guide

- [ ] 3.1 Add "Running your own IDChain node" to `docs/installation-guide.md`: prerequisites, build, init, data directory and key backup, enode via IPC, firewall and NAT for `30329`, contributing a peer entry, sync readiness, cutover with the four variables, rollback. Verify: the cutover scenario passes on a node following only that section.

## 4. Review

- [ ] 4.1 `openspec validate idchain-node-for-operators --strict` passes.
- [ ] 4.2 A human reads every changed word before the PR opens.
