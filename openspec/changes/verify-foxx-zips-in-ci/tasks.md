## 1. Deterministic packaging

- [ ] 1.1 `scripts/foxx-builder.Dockerfile`: pin the base image by digest
      and the versions of the packages it `apk add`s (D1).
- [ ] 1.2 `scripts/foxx-build-inner.sh`: change the zip packaging step
      (`build_test_install`, around line 74) to enumerate files in a fixed
      sorted order, normalize modification times on staged files before
      zipping, and use `zip -X`; confirm (`unzip -Z` against one existing
      archive) that the current dereferencing of `node_modules/.bin`
      symlinks is unaffected (D1).
- [ ] 1.3 Verify: build all four zips twice from independent clean
      checkouts in the pinned builder image and confirm each pair is
      byte-for-byte identical (`cmp`) (D1).
- [ ] 1.4 Rebuild all four committed zips under the new packaging; if any
      differs from what's currently committed, recommit it as part of this
      change.

## 2. Workflow

- [ ] 2.1 Add `.github/workflows/foxx-zips.yml`: trigger on push/PR touching
      `web_services/foxx/**`, `scripts/build-foxx.sh`,
      `scripts/foxx-build-inner.sh`, `scripts/foxx-builder.Dockerfile`, or
      the workflow file itself, plus tag pushes (D3).
- [ ] 2.2 Job runs `scripts/build-foxx.sh`, then compares each of the four
      rebuilt zips against the committed copy byte-for-byte; fails and names
      any mismatch (D2).
- [ ] 2.3 On a tag ref, upload the four built zips as workflow artifacts
      (D4).

## 3. Docs

- [ ] 3.1 `scripts/README.md`: short section on the CI check and the fix
      (rebuild via `scripts/build-foxx.sh`, commit the result), and a note
      that any future change to the packaging step must preserve
      byte-for-byte determinism (D1).

## 4. Verify

- [ ] 4.1 Confirm the workflow passes against the zips committed on this
      branch after task 1.4.

## 5. Optional: make the check required

- [ ] 5.1 (Optional, separate from this change landing) Enable branch
      protection on the default branch requiring the `foxx-zips` check to
      pass before merge, in repository settings. Until this is done, the
      workflow surfaces mismatches but does not block merging.

## 6. Review

- [ ] 6.1 `openspec validate verify-foxx-zips-in-ci --strict` passes.
- [ ] 6.2 A human reads every changed word before the PR opens.
