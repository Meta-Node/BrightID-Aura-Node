# Installation Guide

**Important:** Operators should follow the [node-operator discord channel](https://discord.gg/FPQjA5uCv6) or [keybase](https://keybase.io/team/brightid) #node channel for critical updates.

## DappNode setup

See the [DappNode guide](dappnode.md).

## HTTPS

See the [guide for setting up HTTPS for your BrightID node](https-setup.md).

## Docker install/setup

This section covers the published-image path for `BrightID/BrightID-Node`: pulling and running images that project publishes to Docker Hub. To build and run this repository's own images from source instead, see [Building from this repository](#building-from-this-repository) below.

### Minimum requirements:
- 2 processor core
- 4GB RAM
- 10GB free storage space for pulling docker images and creating database volume

### Download BrightID-Node-docker release
```sh
wget https://github.com/BrightID/BrightID-Node/archive/refs/tags/docker.tar.gz
```
### Extract and change directory
```sh
tar -xvf docker.tar.gz
cd BrightID-Node-docker
```
### Configure BrightID-Node
```sh
nano config.env
```
#### Required settings

##### `BN_SEED`
This is an ASCII string that is used as a seed to generate singing keypairs of the node. As the SHA256 hash of the seed will be used as input to create private keys, an ASCII string that represents 32 random bytes should be used to maximize the security of the seed. For example, you can create a random Nacl keypair [here](https://tweetnacl.js.org/#/sign) and use the base64 representation of the public key as a secure seed phrase.

##### `BN_UPDATER_MAINNET_WSS`
This is an infura (or other wss) API url and should be set to `wss://mainnet.infura.io/ws/v3/{INFURA_PROJECT_ID}` where `INFURA_PROJECT_ID` is an Infura ethereum project id. If you create an [Infura](https://infura.io) account, and an [Ethereum project](https://infura.io/dashboard/ethereum) under that account, you can find the project id under `settings` tab of the project.


#### Optional settings

All the variables other than the above two required ones are optional.

##### `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`
Maximum number of completed consensus snapshots kept pending for the scorer before the receiver starts deleting the oldest ones to make room. Defaults to `3`.

##### `BN_CONSENSUS_TO_ADDRESS`
When running a local node for testing purpose, you should also update `BN_CONSENSUS_TO_ADDRESS` to `0xb1d04A87FdcdB3aAe3dBc846948F25Bd34411e6a` which is the BrightID test network address.

> Note: this repo's `config.env` currently ships a *different* default value (`0xb1d1CDd5C4C541f95A73b5748392A6990cBe32b7`) for production use. That's expected — the two addresses serve different purposes (production default vs. an explicit test-network override) — but the test-network address above wasn't independently re-verified while porting this page, so double-check it's still current before relying on it.

_The following private keys are automatically generated when `BN_SEED` is configured, but they can optionally be configured manually too._

##### `BN_CONSENSUS_PRIVATE_KEY`
This is the private key for an ethereum address.

##### `BN_WS_PRIVATE_KEY`
This is the private key of an EdDSA keypair used to sign verifications. There are several ways to generate an EdDSA key pair. An easy way is to use the `random` button on the [TweetNaCl.js sign test interface](https://tweetnacl.js.org/#/sign).

##### `BN_WS_ETH_PRIVATE_KEY`
This is the private key for an Ethereum address that is used to sign verifications for ethereum smart contracts. An easy way to create an ethereum address and retrieve its private key is through the [Vanity-ETH web interface](https://vanity-eth.tk/).

##### `BN_WS_WISCHNORR_PASSWORD`
This is the password that is used as a seed to generate the WI-Schnorr keypair for blind signatures. As the SHA256 hash of the seed will be used as input to create the keypair, an ASCII string that represents 32 random bytes should be used to maximize the security of the pair. For example, you can create a random Nacl keypair [here](https://tweetnacl.js.org/#/sign) and use the base64 representation of the public key as a secure seed phrase.

##### Other settings
`config.env` has several other variables (endpoints, gas parameters, rate limits, `BN_DEVELOPMENT`, `BN_PEERS`, `BN_ARANGO_EXTRA_OPTS`, etc.) that ship with working defaults and are mostly internal plumbing — see the comments in `config.env` itself if you need to change one.

### Pull BrightID Docker images
To be able to use `docker pull` you should have an account on [docker.com](https://docker.com). After creating account and logging in, go to [here](https://hub.docker.com/settings/security) and create a new access token. Then use the `docker login --username <username>` and enter your access token as password. If you got `Error saving credentials` error, you may be able to solve that by `sudo apt install gnupg2 pass`. You can start pulling BrightID containers after logging in.

```sh
docker-compose pull
```

### Start BrightID node
After pulling images, the node can be started using:

```sh
docker-compose up -d
```

### Check logs and state
The node logs can be checked using:
```sh
docker-compose logs -f
```
BrightID node consists of `db`, `ws`, `scorer`, `consensus_receiver`, `consensus_sender`, `updater` and `web` services <!-- corrected: the wiki version of this page omitted `scorer`, which is its own docker-compose service --->. Each service logs can also be independently checked using:
```sh
docker-compose logs -f <service-name>
```
`/state` endpoint from the API can also be be queried to get some key variables like `lastProcessedBlock` as the number of the last block that `consensus_receiver` processed its operations or `verificationsBlock` as the number of the last block that `scorer` processed and calculated verifications based on.
This endpoint can be queried using:
```sh
curl http://<your-server-address>/brightid/v6/state
```
When the node is synced, `lastProcessedBlock` should be equal to the total number of IDChain blocked that can be checked from [here](https://explorer.idchain.one/). `verificationsBlock` should also be updated in 240 blocks intervals if `scorer` is active.

### Send Eidi

Make sure the consensus sender address has enough Eidi (IDChain native token) for gas to write operations to IDChain.

This address is either automatically generated using the `BN_SEED` or manually configured by setting its private key to the `BN_CONSENSUS_PRIVATE_KEY`. This address can be found in the `consensusSenderAddress` field of the `/state` API endpoint.
```sh
curl http://<your-server-address>/brightid/v6/state
```

Eidi tokens can be freely claimed from [this faucet](https://idchain.one/begin).
When running a local node for testing purpose, you need the address to have Eidi only if you want to connect a mobile client to your test node and send operations to test network.

### Upgrade
If [BrightID-Node-docker](#download-brightid-node-docker-release) is not updated, nodes can be upgraded by pulling and running new images.

```sh
docker-compose pull
docker-compose stop
docker-compose up -d
```

If new [BrightID-Node-docker](#download-brightid-node-docker-release) is released, you should [download](#download-brightid-node-docker-release), [extract](#extract-and-change-directory) and [configure](#configure-brightid-node) node again before pulling and running new images. Same configurations that used to configure previous version of `config.env` can be used to configure the new one.

### Re-initialize

The node database is initialized by fetching the latest hourly backup of [official BrightID node](http://node.brightid.org/brightid/v5/state) when you run the node for the first time. Pulling new images and running them in upgrade process will not re-initialize the node. The node database can be re-initialized using the following command when your node was down for a long time or there are other problems.

```sh
INIT_BRIGHTID_DB=1 docker compose up -d --force-recreate db scorer
```

A re-initialization request is served once. The containers keep
`INIT_BRIGHTID_DB=1` in their environment afterwards, but they will not act on
it again - a crash, a reboot, or `docker compose stop` followed by
`docker compose up -d` leaves the database alone. `--force-recreate` is what
makes a new request, so the command above works the first time and every time
after.

**Important - on an Aura node, re-initializing destroys Aura evaluations.** The upstream backup does not carry the `auraEvaluations` array this repository stores on `connections` documents, so restoring it erases every Aura evaluation the node holds. This has been confirmed on a live node. Before re-initializing a node that holds evaluations:

1. Bring the node up *without* initializing (`docker compose up -d`).
2. Export every connection with `auraEvaluations != null` to a JSON file.
3. Re-initialize with the command above.
4. Re-import the exported evaluations.

The export and import tooling is not part of this repository; ask the Aura maintainers for it.

### Upgrade db
If the release includes arangodb version upgrade, following command should be run after stopping old containers and before running new ones to upgrade data in volumes using a temporary container.

```sh
docker-compose run --rm db arangod --database.auto-upgrade
```

## Building from this repository

This path builds this repository's images from source, rather than pulling `BrightID/BrightID-Node`'s published images. Use it when running this repository directly (for example, an Aura node) rather than the upstream published node.

### Clone the repository
```sh
git clone <this repository's URL>
cd <the cloned directory>
```

### Configure BrightID-Node
Copy or edit `config.env` in the repository root. The required and optional settings are the same as [above](#configure-brightid-node) - at minimum, set `BN_SEED` and `BN_UPDATER_MAINNET_WSS`.

### Build the images
```sh
docker compose build
```
This builds the six services that declare a `build:` context (`ws`, `scorer`, `consensus_receiver`/`consensus_sender`, `updater`, `db`) from source; `web` uses the published `nginx` image as-is. The Foxx services (`web_services/foxx/`) ship as pre-built zips; `scripts/build-foxx.sh` rebuilds them (see the [Development Guide](development-guide.md)).

### Start the node
```sh
docker compose up -d
```
On a fresh machine the database initializes itself from the latest hourly backup of the [official BrightID node](http://node.brightid.org/brightid/v5/state). Check state as [above](#check-logs-and-state); `/brightid/v6/state` should answer and `lastProcessedBlock` should advance.

### Restart behaviour
Every service runs with `restart: unless-stopped`. Services come back automatically if a container exits unexpectedly or the host reboots (with Docker enabled at boot), while a deliberate `docker compose stop` is respected - those services stay stopped, including across a subsequent host reboot.

## Configure firewall
Port 80 needs to be exposed for clients. Ports 8529 and 3000 are used internally by BrightID-Node (confirmed against this repo's `docker-compose.yml`, which `expose`s exactly those two ports for `db` and `ws` respectively), but should not be exposed externally.

## System tuning
Consider running
```
sudo sysctl -w vm.max_map_count=4096000
```
on a Linux host system. ArangoDB makes extensive use of memory mapped files. This repo currently pins ArangoDB 3.9.1 (see `db/Dockerfile`), not the 3.4 the wiki previously referenced. `docs.arangodb.com` has since moved to `docs.arango.ai`; search that site for "Linux OS configuration" for current tuning guidance rather than relying on the old deep link, which no longer resolves.

## Connect to ArangoDB GUI
BrightID data can be explored and settings can be configured through ArangoDB's web interface.
If you installed the node locally, you can access the web interface from `localhost:8529`, and if you installed on a server, you can create an SSH tunnel as described bellow to access it.

### Create an SSH tunnel on your local machine
Create a tunnel to any port you like. This example uses port `3333`.

On your local machine that has SSH access to the server, run
```
ssh -nNTL 3333:localhost:8529 <your-server-address> &
```
### Browse to ArangoDB
Now open a browser with the following address:
```
http://localhost:3333/
```
### Useful locations in the ArangoDB interface
* "Collections" - shows all of the collections in the db
* "Queries" - explore the graph and other collections with queries and visualizations
* "Services"
  * API - shows the API endpoints for the BrightID web service
  * Settings - configure settings for the BrightID web service (Can also be edited as constants in [config.env](#configure-brightid-node))
*  Logs - view warnings and errors

## Running your own IDChain node

By default `config.env` points every IDChain call at `idchain.one`. If that host is unreachable, `consensus_receiver`, `consensus_sender` and `updater` stall. This section builds and runs your own IDChain sync node from this repository's `idchain/` directory, so your Aura node keeps advancing as long as your IDChain node has a peer. This is a non-sealing full node: no validator key, no `--mine`, no vote. Validator setup is out of scope.

### Prerequisites
Docker and Docker Compose (the same requirement as the rest of this guide). No Go toolchain needed on the host — the build happens inside the Docker image. At least one reachable IDChain peer (the committed `idchain/static-nodes.json` ships with one confirmed-live peer; see "Contributing a peer entry" below if you need more).

### Build
From the repository root:
```sh
cd idchain
docker compose build
```
This builds `IDChain-eth/IDChain` tag `idc1.9.18` from source with `golang:1.14-alpine`, matching that tag's own build recipe. Record the resolved commit and the built image's digest (`docker image inspect idchain-geth --format '{{.Id}}'` — Compose names a built image `<project>-<service>`, and the project is the directory name, `idchain`) somewhere you'll find again — you'll want both if you ever need to prove what you're running.

### Initialize the data directory
Seed the peer list first, while `data/` is still yours (the container runs as root and `init` leaves root-owned files). Geth 1.9 reads static peers from `$DATADIR/geth/static-nodes.json`:
```sh
mkdir -p data/geth && cp static-nodes.json data/geth/static-nodes.json
```
Then initialize from the committed genesis, which `idchain/docker-compose.yml` mounts read-only at `/idchain-genesis.json`:
```sh
docker compose run --rm geth init --datadir /data /idchain-genesis.json
```

### Data directory and key backup
The node's identity — its enode public key — lives in `geth/nodekey` inside the data directory (`./data` next to `idchain/docker-compose.yml` by default). Re-running `init` against an *existing* data directory does not change it; pointing the container at a *new, empty* data directory does. Back up the data directory (or at minimum `geth/nodekey`) before any operation that might replace it, so you don't have to re-announce a new enode to every peer that has yours in their static list.

### Start the node
```sh
docker compose up -d
```
Confirm it's alive and on the right chain:
```sh
curl -s -X POST -H 'content-type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}' \
  http://127.0.0.1:8545
```
should return `0x4a` (74). RPC (HTTP `8545` and WS `8546`) is reachable from `127.0.0.1` only — the `idchain/docker-compose.yml` binds the listener to `0.0.0.0` *inside* the container but publishes the port on the host's loopback address only, so it never reaches the network. Only the `eth`, `net`, `web3` and `clique` namespaces are enabled; `admin`, `personal`, `miner` and `debug` are not, on either transport.

### Firewall and NAT for the peer-to-peer port
The node listens on `30329` (TCP and UDP) for peer-to-peer traffic — distinct from Geth's default `30303`, and the port the published IDChain peer list uses. Open `30329/tcp` and `30329/udp` inbound on your host firewall, and forward both on your router/NAT if the host is behind one, so other IDChain nodes can dial in.

### Contributing a peer entry
The committed `idchain/static-nodes.json` is reviewed by pull request, not self-served: an entry is added after a reviewer connects to it and fetches a block, and removed after it fails to connect from two hosts on two different days. If your node needs more peers than the committed list provides, open a pull request adding your enode (from `admin.nodeInfo.enode`, read below) once someone else has verified it the same way — don't add unverified enodes yourself.

### Checking sync readiness
Compare your node's block hash at genesis (block 0) and at block 4,000,000 against `https://idchain.one/rpc/`'s `eth_getBlockByNumber` for the same heights. A match at both confirms you're on the same chain. Sync time depends on how many peers you have and how fast they are — expect single digit hours from one slow peer; the peer list above is the remedy if it's taking too long.

To read your node's enode (for backup, or to share it if you're contributing a peer entry), attach over IPC rather than opening `admin` on RPC:
```sh
docker compose exec geth geth attach --exec 'admin.nodeInfo.enode' /data/geth.ipc
```

### Cutover
Run this on the same host as your Aura node: RPC is published on `127.0.0.1` only, and `consensus_receiver`, `consensus_sender` and `updater` use the host's network. Once your node is synced and has at least one live peer, set these four variables in `config.env`:

- `BN_CONSENSUS_INFURA_URL=ws://127.0.0.1:8546` (the name is legacy; this is IDChain traffic)
- `BN_CONSENSUS_IDCHAIN_RPC_URL=http://127.0.0.1:8545/`
- `BN_UPDATER_IDCHAIN_WSS=ws://127.0.0.1:8546`
- `BN_UPDATER_SEED_GROUPS_WS_URL=ws://127.0.0.1:8546`

Then, from the repository root:
```sh
docker compose build consensus_receiver updater
docker compose up -d consensus_receiver consensus_sender updater
```
`lastProcessedBlock` in `/brightid/v6/state` should keep advancing with `idchain.one` unreachable from the host.

The four variables cover the node's own IDChain calls. Apps carry their own RPC endpoints, stored with each app in the node's database; those are unaffected by cutover.

### Rollback
Set `BN_CONSENSUS_IDCHAIN_RPC_URL` back to `https://idchain.one/rpc/` and the other three (`BN_CONSENSUS_INFURA_URL`, `BN_UPDATER_IDCHAIN_WSS`, `BN_UPDATER_SEED_GROUPS_WS_URL`) back to `wss://idchain.one/ws/`, then recreate the same three services. Your IDChain node itself can keep running or be stopped independently — it isn't part of the rollback.
