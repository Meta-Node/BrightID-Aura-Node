## Purpose
What an operator can rely on when building and running a node from this repository on a supported host, independent of any published images.

## ADDED Requirements

### Requirement: Builds from source on a clean host
The node's images SHALL build with `docker compose build` from a fresh clone on a clean x86_64 Linux host running Docker Engine 29 and Compose v2 or later, with no build cache and no registry credentials.

#### Scenario: First build on a new machine
- **WHEN** an operator clones the repository on such a host and runs `docker compose build`
- **THEN** every service image builds successfully

#### Scenario: First start after the build
- **WHEN** the operator has set `BN_SEED` and `BN_UPDATER_MAINNET_WSS` in `config.env` and runs `INIT_BRIGHTID_DB=1 docker compose up -d` with internet access
- **THEN** all seven services reach `running`, and `/brightid/v6/state` answers with `lastProcessedBlock` advancing

### Requirement: Recovers from a host restart
On a host where Docker is enabled at boot, a node started with `docker compose up -d` SHALL resume after a reboot without operator action.

#### Scenario: Host reboots while the node is running
- **WHEN** the host reboots
- **THEN** all seven services return to `running` and `lastProcessedBlock` advances from where it stopped

#### Scenario: Operator stops the node deliberately
- **WHEN** the operator runs `docker compose stop` and the host later reboots
- **THEN** the services stay stopped
