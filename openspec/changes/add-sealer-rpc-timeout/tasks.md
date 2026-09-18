## 1. Code

- [x] 1.1 `consensus/receiver.py`: add `IDCHAIN_RPC_TIMEOUT = 10` beside
      `NUM_SEALERS` and pass `timeout=IDCHAIN_RPC_TIMEOUT` to the
      `requests.post` in `update_num_sealers()` (D1, D2). Verify: no other line
      of the function changes.

## 2. Test

- [x] 2.1 `consensus/test_receiver.py`: `test_timeout_is_passed_and_caught` —
      `requests.post` mocked to raise `requests.Timeout`; asserts nothing
      escapes, `NUM_SEALERS` is unchanged, and the call carried
      `timeout=IDCHAIN_RPC_TIMEOUT`. Verify: `python3 -m unittest -v
      test_receiver` passes in the `brightid/consensus` image.

## 3. Review

- [x] 3.1 `openspec validate add-sealer-rpc-timeout --strict` passes.
