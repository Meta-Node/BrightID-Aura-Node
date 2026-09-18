## Why

`update_num_sealers()` in `consensus/receiver.py` posts to `BN_CONSENSUS_IDCHAIN_RPC_URL` with no `timeout=`, and `requests` has no default timeout. An endpoint that accepts the connection and never answers blocks the single-threaded receiver loop indefinitely; nothing is raised, so nothing is logged and the node stops applying blocks without saying why ([AUR-324](https://linear.app/brightid/issue/AUR-324)).

## What Changes

- `consensus/receiver.py`: a module constant `IDCHAIN_RPC_TIMEOUT = 10`, passed as `timeout=IDCHAIN_RPC_TIMEOUT` to the `requests.post` in `update_num_sealers()`.
- `consensus/test_receiver.py`: `test_timeout_is_passed_and_caught`.

Other `requests` calls without a timeout are listed in design.md and left alone.

## Capabilities

### New Capabilities
- `sealer-count-refresh`: how the receiver's read of the IDChain sealer count behaves when the RPC endpoint does not answer.

### Modified Capabilities

None.

## Impact

- **Operators:** an RPC endpoint that stops answering no longer freezes the receiver silently. Mid-run, the receiver logs `Error from update_num_sealers`, keeps the sealer count it already has, and goes on applying blocks. At startup it logs, waits 5 seconds and tries again, as it already does for any other failed read.
- An endpoint that takes longer than 10 seconds to accept a connection, or goes silent for longer than 10 seconds while answering `clique_status`, is now treated as a failed read. A node pointed at one would log errors instead of waiting, and at startup would not begin applying blocks until a read succeeds.
- No new setting, no `config.env` or compose change, no change to `docs/installation-guide.md`. Upgrade is a rebuild of the `brightid/consensus` image.
