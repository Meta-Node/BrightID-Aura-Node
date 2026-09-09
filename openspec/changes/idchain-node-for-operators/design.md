## Context

See proposal.md — Why. Observed 2026-09-09 from one host: tag `idc1.9.18` built with `golang:1.14-alpine`, no source changes; block hashes at 1 and 4,000,000 match `idchain.one`; of the seven seeds in the published `static-nodes.json`, none answered a discovery ping, one accepted a connection (a May-2020 Geth build), five refused. Details and timestamps are in the operator notes.

## Goals / Non-Goals

**Goals:** a build that repeats; a node that is safe by default; a peer list that stays true; a cutover that redirects every IDChain call and rolls back.

**Non-Goals:** validator setup; client upgrades; public RPC hosting; IDChain's future.

## Decisions

**D1 — Build from source with the tested toolchain, here.** `golang:1.14-alpine` matches the tag's own Dockerfile and built first time. Record the resolved commit and image digest.
*Alternatives:* DAppNode package (DAppNode only); published image (no registry owner yet).

**D2 — Loopback RPC, `eth,net,web3` on HTTP and WS, `30329` inbound.** The RPC serves the Aura node on the same host; `admin`, `personal`, `miner`, `debug` and `clique` stay off both transports. `30329` TCP and UDP inbound so others can connect; it's the port the published list uses.
*Alternatives:* RPC on the open internet (2020 client — no); Geth's default `30303` (not what operators expect).

**D3 — Complete the cutover in code.** `updater/config.py` reads `BN_CONSENSUS_IDCHAIN_RPC_URL`; `consensus/receiver.py` always injects PoA middleware. Otherwise a redirected node still calls `idchain.one` from the updater, and a loopback URL disables block handling in the receiver.
*Alternatives:* require the local URL to contain `idchain` (a trap); a separate updater variable (one URL, one variable).

**D4 — Peer list reviewed here, by pull request.** Added after a reviewer connects and fetches a block; removed after failing from two hosts on different days. The file on `idchain.one` should point here once merged.
*Alternatives:* discovery (nothing answered ours); private enode exchange (the status quo).

## Risks / Trade-offs

- A 2020 client with an open p2p port has unpatched exposure. Loopback RPC and a short API list limit access; they don't fix the client.
- Sync time depends on peers: about eight hours from one slow peer. The list is the remedy.
- Identity lives in `geth/nodekey` in the data directory. A new directory means a new key; `init` on the same directory does not. Back it up.
- D3 needs `consensus` and `updater` rebuilt; without that, the old behavior stays.
