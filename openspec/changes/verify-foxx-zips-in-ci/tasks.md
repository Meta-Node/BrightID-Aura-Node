## 1. Deterministic packaging

- [ ] 1.1 `scripts/foxx-builder.Dockerfile`: pin the base image by digest and
      the `apk add` package versions (D3).
- [ ] 1.2 `scripts/foxx-build-inner.sh`, `build_test_install`: normalize
      modification times and permissions on the staged tree; fail if it contains
      a symlink to a directory; replace `zip -rq` with a sorted `find` list of
      files and symlinks piped to `zip -X -q -@`; keep `-y` off (D1).
- [ ] 1.3 Build all four zips twice from independent clean checkouts in the
      pinned image; confirm each pair is byte-for-byte identical (D2), with the two checkouts
      made under different umasks (022 and 002).
- [ ] 1.4 Rebuild and recommit `brightid5.zip`, `apply5.zip`, `brightid6.zip`,
      `apply6.zip` under the new packaging.
- [ ] 1.5 Confirm the recommitted archives still unzip to the same file
      contents, including dereferenced `node_modules/.bin` entries.

## 2. Workflow

- [ ] 2.1 Add `.github/workflows/foxx-zips.yml` on `ubuntu-latest`, triggered
      by the five paths in D4.
- [ ] 2.2 Run `scripts/build-foxx.sh`, then `cmp` each rebuilt zip against its
      committed copy; fail naming any mismatch (D2).

## 3. Docs

- [ ] 3.1 `scripts/README.md`: the check, the fix when it fails, and the rule
      that packaging changes preserve determinism and never add `zip -y` (D1).

## 4. Verify

- [ ] 4.1 The workflow passes against the zips committed on this branch after
      task 1.4.

## 5. Optional, not part of landing this change

- [ ] 5.1 Branch protection requiring the `foxx-zips` check before merge.
- [ ] 5.2 Upload the built zips as workflow artifacts on tag pushes (D4).

## 6. Review

- [ ] 6.1 `openspec validate verify-foxx-zips-in-ci --strict` passes.
