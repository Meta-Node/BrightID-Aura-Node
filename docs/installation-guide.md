# Installation Guide

**Important:** Operators should follow the [node-operator discord channel](https://discord.gg/FPQjA5uCv6) or [keybase](https://keybase.io/team/brightid) #node channel for critical updates.

## DappNode setup

See the [DappNode guide](dappnode.md).

## HTTPS

See the [guide for setting up HTTPS for your BrightID node](https-setup.md).

## Docker install/setup

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
INIT_BRIGHTID_DB=1 docker-compose up -d
```

### Upgrade db
If the release includes arangodb version upgrade, following command should be run after stopping old containers and before running new ones to upgrade data in volumes using a temporary container.

```sh
docker-compose run --rm db arangod --database.auto-upgrade
```

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
