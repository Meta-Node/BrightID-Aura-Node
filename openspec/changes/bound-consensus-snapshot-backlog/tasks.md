## 1. Config

- [ ] 1.1 Add `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS` (default `3`) to
      `config.env` and read it in `consensus/config.py`; reject a configured
      value ≤ 0 at startup with a clear error (D3).

## 2. Code

- [ ] 2.1 `consensus/receiver.py`: on startup, before the main loop, remove
      any `dump_*` directory in `/snapshots` that lacks the `_fnl` suffix
      (D3).
- [ ] 2.2 `consensus/receiver.py`: add a `pending_snapshots()` helper counting
      completed snapshot directories (`dump_*_fnl`) in `/snapshots`; call it
      before `save_snapshot()`
      in `main()`'s loop and block (sleep/recheck) while the count is at or
      above the cap (D1).

## 3. Docs

- [ ] 3.1 `docs/installation-guide.md`: one line documenting
      `BN_CONSENSUS_MAX_PENDING_SNAPSHOTS` and the default.

## 4. Verify

- [ ] 4.1 Behavioral check: run the receiver against a cap of `1` (or a
      scripted test), fill it, and confirm the receiver blocks and resumes
      once the scorer consumes a snapshot — not just that validation passes.
- [ ] 4.2 Confirm a leftover non-`_fnl` `dump_*` directory is removed on
      startup and does not count toward the cap (D3).

## 5. Review

- [ ] 5.1 `openspec validate bound-consensus-snapshot-backlog --strict`
      passes.
- [ ] 5.2 A human reads every changed word before the PR opens.
