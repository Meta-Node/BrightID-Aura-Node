## Context

See proposal.md — Why. Three facts about the code on `dev` shape the fix:

- The `requests.post` in `update_num_sealers()` already sits inside
  `try / except Exception`, which prints `Error from update_num_sealers` and
  returns. `requests.Timeout` derives from `RequestException` → `IOError` →
  `Exception`, so the existing handler catches it. No handler change is needed.
- A failed read leaves `NUM_SEALERS` as it was. Mid-run (the refresh every 100
  blocks) a timeout therefore never lowers the confirmation margin; the node
  carries on with the last good count.
- `wait_for_sealer_count()` calls `update_num_sealers()` in a loop, sleeping 5
  seconds while `NUM_SEALERS == 0`. A timeout at startup is one more failed read
  in that loop: it retries, and neither hangs nor crashes.

Other `requests` calls in `consensus/` and `updater/` with no timeout — listed,
not changed here:

| Call | Where | Talks to |
|---|---|---|
| `requests.put(url, json=op)` | `consensus/receiver.py` `process_op()` | Foxx `apply` on the local ArangoDB — same loop, same hang |
| `requests.request('POST', config.IDCHAIN_RPC_URL, …)` | `updater/tools.py` `get_idchain_block_number()` | IDChain RPC |
| `requests.get(url)` | `updater/apps.py` `get_logo()` | a URL supplied by each app |
| `requests.get(config.APPS_JSON_API_URL)` | `updater/apps.py` `update()` | apps API |

Outside those two directories, `scorer/verifications/predefined.py` has one
more: `requests.get(file['url'])`.

## Goals / Non-Goals

**Goals:** the sealer-count read cannot block the receiver loop indefinitely.

**Non-Goals:** the calls in the table above; any change to retry or error
handling; making the value configurable.

## Decisions

**D1. A module constant, `IDCHAIN_RPC_TIMEOUT = 10`, in `receiver.py` beside
`NUM_SEALERS`.** Passed as `timeout=IDCHAIN_RPC_TIMEOUT`. *Rejected:* a
`BN_CONSENSUS_*` setting — `config.py` reads those with `os.environ[...]`, so a
new one is a line every operator must add to `config.env` before the receiver
will start, for a value nobody has asked to tune.

**D2. 10 seconds, one value for both connect and read.** `clique_status` is a
small request with a small response. *Rejected:* 60, the value
`updater/` gives its web3 providers — a dead endpoint would then cost a minute
per 100 blocks while a node catches up.

## Risks / Trade-offs

- `timeout=` bounds the connect and each wait for data, not the whole request;
  an endpoint that trickles bytes can hold the call longer than 10 seconds. →
  Accepted; the `clique_status` response is a few hundred bytes.
- While catching up, a dead endpoint costs up to 10 seconds per 100 blocks. →
  Accepted; before this change it cost forever.
- #46 (`philip/idchain-node`) and #47 (`philip/snapshot-backlog-cap`) also edit
  `receiver.py`, and #47 adds its own constant directly after `NUM_SEALERS = 0`.
  → Whichever merges second takes a trivial merge.
