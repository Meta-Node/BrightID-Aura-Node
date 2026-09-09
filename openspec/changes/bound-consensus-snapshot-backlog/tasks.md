## 1. Config

- [ ] 1.1 `config.env` + `consensus/config.py`: add
      `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS`, default `3`; reject `0` or less at
      startup (D2, D4).

## 2. Code

- [ ] 2.1 `consensus/receiver.py`: on startup, remove every `dump_*` directory
      in `/snapshots` lacking `_fnl` (D3).
- [ ] 2.2 `consensus/receiver.py`: count completed snapshot directories
      (`dump_*_fnl`) before `save_snapshot()`; block while at or above the cap,
      resume when below (D1).

## 3. Docs

- [ ] 3.1 `docs/installation-guide.md`: one line for the variable and default.

## 4. Verify

- [ ] 4.1 At cap `1`, confirm the receiver blocks and resumes once the scorer
      consumes a snapshot.
- [ ] 4.2 Confirm a leftover non-`_fnl` `dump_*` directory is removed on
      startup.

## 5. Review

- [ ] 5.1 `openspec validate bound-consensus-snapshot-backlog --strict` passes.
