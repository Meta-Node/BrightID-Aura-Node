## 1. Deterministic packaging

- [x] 1.1 `scripts/foxx-builder.Dockerfile`: pin the base image by digest and
      the `apk add` package versions (D3).
- [x] 1.2 `scripts/foxx-build-inner.sh`, `build_test_install`: normalize
      modification times on the staged tree; replace `zip -rq` with a sorted
      `find` list piped to `zip -X -q -@`; keep `-y` off (D1).
- [x] 1.3 Build all four zips twice from independent clean checkouts in the
      pinned image; confirm each pair is byte-for-byte identical (D2).
- [x] 1.4 Rebuild and recommit `brightid5.zip`, `apply5.zip`, `brightid6.zip`,
      `apply6.zip` under the new packaging.
- [x] 1.5 Confirm the recommitted archives still unzip to the same file
      contents, including dereferenced `node_modules/.bin` entries.

## 2. Workflow

- [x] 2.1 Add `.github/workflows/foxx-zips.yml` on `ubuntu-latest`, triggered
      by the five paths in D4.
- [x] 2.2 Run `scripts/build-foxx.sh`, then `cmp` each rebuilt zip against its
      committed copy; fail naming any mismatch (D2).

## 3. Docs

- [x] 3.1 `scripts/README.md`: the check, the fix when it fails, and the rule
      that packaging changes preserve determinism (D1).

## 4. Verify

- [x] 4.1 The workflow passes against the zips committed on this branch after
      task 1.4. Not yet done: the compare logic was replicated by hand, but the
      workflow has never run on a GitHub runner, and the Mocha suites
      `build-foxx.sh` runs have never executed (ArangoDB's amd64 binaries will
      not run on the machine the zips were built on). The first CI run is the
      verification.

## 5. Optional, not part of landing this change

- [ ] 5.1 Branch protection requiring the `foxx-zips` check before merge.
- [ ] 5.2 Upload the built zips as workflow artifacts on tag pushes, in a
      workflow whose triggers are not path-filtered (D4).

## 6. Review

- [x] 6.1 `openspec validate verify-foxx-zips-in-ci --strict` passes.
