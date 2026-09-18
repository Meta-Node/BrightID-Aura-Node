## 1. Config

- [x] 1.1 `config.env` + `consensus/config.py`: add
      `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`, default `3`; reject `0` or less at
      startup (D3, D5).

## 2. Scorer

- [x] 2.1 `scorer/runner.py`: change `next_snapshot()` to select the newest
      `_fnl` directory by block number instead of the oldest, and delete
      every other completed snapshot it finds at that point (D2). Verify:
      with 3 completed snapshots present, the scorer processes only the
      newest and the other 2 are deleted, unprocessed.

## 3. Receiver

- [x] 3.1 `consensus/receiver.py`: on startup, remove every `dump_*`
      directory in `/snapshots` lacking `_fnl` (D4).
- [x] 3.2 `consensus/receiver.py`: before `save_snapshot()`, if the count of
      completed snapshot directories (`dump_*_fnl`) is at or above the cap,
      delete the oldest one(s) until below it, then proceed — never block
      the main loop (D1).

## 4. Docs

- [x] 4.1 `docs/installation-guide.md`: one line for the variable and
      default.

## 5. Verify

- [x] 5.1 At cap `1` with the scorer stopped, confirm the receiver deletes
      the oldest snapshot and keeps advancing rather than pausing.
- [x] 5.2 Confirm a leftover non-`_fnl` `dump_*` directory is removed on
      startup.
- [x] 5.3 With the scorer resumed after a backlog, confirm it processes only
      the newest snapshot and deletes the others.

## 6. Review

- [x] 6.1 `openspec validate bound-consensus-snapshot-backlog --strict`
      passes.
