## 1. Detector

- [ ] 1.1 `receiver.py`: the five fields, the D1 detector on its own thread per D2, timeouts on every IDChain and Foxx call. Verify: of a stalled node, a node gaining one block per window, a frozen chain and a blackholed RPC, only the first is `stalled`; the detector still reports during `save_snapshot()`.
- [ ] 1.2 Foxx `v5`/`v6`: `/state` serves the five fields. Verify: both Mocha suites green.
- [ ] 1.3 `config.py`, `config.env`, compose: the `BN_RECOVERY_*` variables. Verify: receiver starts on defaults.
- [ ] 1.4 `docs/installation-guide.md`: what the five fields mean and how to read a `stalled` node.
- [ ] 1.5 `openspec validate sync-stall-detection --strict` passes.
