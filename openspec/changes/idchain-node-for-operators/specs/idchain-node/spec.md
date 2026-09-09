## Purpose

An IDChain node an operator runs themselves, from this repository, for their Aura node.

## ADDED Requirements

### Requirement: Build and sync
An operator SHALL be able to build the client and start a sync node with Docker Compose, without a Go toolchain on the host.

#### Scenario: Fresh installation
- **WHEN** an operator follows the guide on a Linux host with Docker Compose and at least one reachable IDChain peer
- **THEN** `eth_chainId` returns `0x4a`, `net_peerCount` is at least 1, and the block number advances

### Requirement: Chain verification
The node SHALL be on the same chain as `idchain.one`.

#### Scenario: Checkpoint comparison
- **WHEN** the node has passed a documented checkpoint height
- **THEN** its block hash at genesis and at that checkpoint equal those served by `https://idchain.one/rpc/`

### Requirement: Local RPC
HTTP and WebSocket RPC SHALL be reachable from the host's loopback address only, and the `admin`, `personal`, `miner`, `debug` and `clique` namespaces SHALL NOT be enabled on either.

#### Scenario: Exposure
- **WHEN** a connection is attempted from the host and from another machine
- **THEN** the host connection succeeds and the external connection fails

#### Scenario: Restricted methods
- **WHEN** `admin_peers` or `clique_getSigners` is requested over HTTP and over WebSocket
- **THEN** each returns method unavailable

### Requirement: Persistent identity
The node's enode public key SHALL be unchanged when the container is recreated with the same data directory.

#### Scenario: Recreate
- **WHEN** the container is removed and started again with the same data directory
- **THEN** `admin.nodeInfo.enode` over IPC reports the same public key

### Requirement: Complete cutover
An Aura node SHALL use the local IDChain node for all IDChain traffic when `BN_CONSENSUS_INFURA_URL`, `BN_CONSENSUS_IDCHAIN_RPC_URL`, `BN_UPDATER_IDCHAIN_WSS` and `BN_UPDATER_SEED_GROUPS_WS_URL` point at it.

#### Scenario: Default endpoint unreachable
- **WHEN** the four variables point at a synced local node, the `consensus_receiver`, `consensus_sender` and `updater` services are recreated, and `idchain.one` is blocked from the host
- **THEN** `lastProcessedBlock` advances, a submitted operation is confirmed, and the updater's IDChain checks continue
