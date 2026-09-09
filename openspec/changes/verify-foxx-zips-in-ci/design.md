## Context

`scripts/build-foxx.sh` already builds all four zips inside a container
matching production (`scripts/foxx-builder.Dockerfile`) and runs both
versions' Mocha suites; it's documented in `scripts/README.md` and exercised
by contributors and by `scripts/build-foxx.test.sh` (a stub-based control-flow
test, no docker). Nothing runs it in CI — there is no `.github/workflows`
directory in this repo at all. The zips it produces are committed straight
into `web_services/foxx/`.

The packaging step in `scripts/foxx-build-inner.sh` copies each version's
source into a fresh staging directory and runs plain `zip -rq` over it
(`scripts/foxx-build-inner.sh:74`). `zip -r` walks the directory in
filesystem order (not sorted) and records each entry's modification time by
default, so two builds from the identical source tree — even run back to
back — produce different zip bytes. A byte-for-byte comparison against a
committed zip would fail on every rebuild regardless of whether the source
changed, which makes that comparison useless until packaging is made
deterministic first.

## Goals / Non-Goals

**Goals:** two independent builds of the same source tree produce
byte-identical zips; an automatic, PR-visible check that rebuilt zips match
the committed ones; artifacts on tags; keep using `scripts/build-foxx.sh` as
the build entry point.

**Non-Goals:** changing how zips are deployed (`docker-entrypoint.sh` still
reads them from `/code/foxx/*.zip`, built into the `ws` image as today);
committing CI-built zips back to the branch automatically (a bot commit on
every PR is more disruptive than a failing check with a clear fix); building
zips for anything but the four existing ones; making the check a required
status check for merge (a separate, optional repository setting — see
`tasks.md`).

## Decisions

**D1. Build inside the pinned builder image, make packaging deterministic,
and preserve the archive's intended contents — not only file bytes — before
adding a comparison check.** Two independent builds are only comparable if
both the toolchain and the packaging step are controlled:
- pin `scripts/foxx-builder.Dockerfile`'s base image by digest (not the
  floating `node:20-alpine` tag) and pin the versions of the packages it
  `apk add`s, so a rebuild months later uses the same toolchain, not
  whatever `node:20-alpine` and Alpine's repos currently resolve to;
- in `build_test_install` (around `scripts/foxx-build-inner.sh:74`),
  enumerate files in a fixed order — `find "$dir" | LC_ALL=C sort` — instead
  of relying on `zip -r`'s filesystem-order walk;
- normalize modification times on the staged files before zipping (e.g.
  `find "$dir" -exec touch -d "@${SOURCE_DATE_EPOCH:-0}" {} +`) so the
  timestamp isn't whatever moment `npm ci`/`cp` happened to run;
- zip with `-X` (strip extra file attributes — UID/GID, extended
  timestamps) so the container running the build doesn't leak into the
  archive bytes;
- dereference symlinks the same way the existing archives do. `npm ci`
  creates `node_modules/.bin/*` as symlinks into the packages that provide
  them; checking one existing archive with `unzip -Z brightid6.zip | grep
  '\.bin'` shows those entries as ordinary files (`-rwxr-xr-x`, real byte
  counts, not `l...` symlink entries), meaning the current build already
  follows links into the archive. Plain `zip` (without `-y`) follows
  symlinks by default, so no packaging change is needed here — but it must
  stay that way; a future change to add `-y` would silently start omitting
  `.bin` commands' content, breaking the packages that need them.

This is a build-script and builder-image change only; it does not change
any file's *content* inside the zip beyond continuing to dereference
symlinks as today, only the metadata and ordering the zip format records
alongside it — `docker-entrypoint.sh` unzips by content and never reads zip
timestamps or entry order. Unix permission bits (the `-rwxr-xr-x` above) are
preserved because `zip -X` strips only *extra* fields (UID/GID, extended
timestamps), not the standard external file attributes zip stores permission
bits in. *Alternative rejected:* run a general-purpose tool like
`strip-nondeterminism` post-hoc on the existing `zip -rq` output — an extra
dependency in the builder image for a problem `find | sort` plus `zip -X`
already solves without one.

"Byte-for-byte identical" means: two builds of the same commit, run
independently (separate checkouts, separate container invocations) inside
the pinned builder image, produce zips whose bytes match exactly (`cmp`
returns no difference) — this is the acceptance test for D1, and every
artifact in this change (proposal, design, tasks, spec) uses this exact
phrase and this exact test for it.

**D2. The CI check compares rebuilt zips to committed ones byte-for-byte.**
With D1 in place, two builds from the same source are byte-identical, so a
plain `cmp` (or equivalent) between the freshly built zip and the committed
one is a valid pass/fail signal: a difference means the source changed
without a rebuild, not build nondeterminism. Every artifact in this change —
proposal, design, tasks, spec — uses "byte-for-byte" for this comparison, not
"content comparison after unzip" or any looser phrasing, so there's one
definition of what "matches" means. *Alternative rejected:* unzip both and
diff extracted file contents (ignoring zip-level metadata) — weaker than
necessary once D1 makes true byte-for-byte equality achievable, and it would
mask a regression in D1's determinism fix instead of catching it.

**D3. Trigger on paths that can affect the zips, including the build
scripts and the workflow itself; run on GitHub-hosted `ubuntu-latest`.** Path
filters — `web_services/foxx/**`, `scripts/build-foxx.sh`,
`scripts/foxx-build-inner.sh`, `scripts/foxx-builder.Dockerfile`, and
`.github/workflows/foxx-zips.yml` — keep the job off unrelated PRs while
covering every file that controls what gets packaged; the earlier filter
(`web_services/foxx/**`, `scripts/build-foxx*.sh`) missed
`foxx-build-inner.sh` and the Dockerfile, so a change to either would ship
unverified. `docker build`/`docker run` work out of the box on the standard
runner, same as a contributor's machine. *Alternative rejected:* run on every
push regardless of path — wastes CI minutes on changes that can't affect the
zips.

**D4. Upload artifacts on tag push, in the same job.** One workflow does both
verification (every relevant push/PR) and uploading the four zips as
*workflow artifacts* (GitHub Actions' build-artifact mechanism, downloadable
from the run — not a GitHub Release asset) on tags only, via an
`if: startsWith(github.ref, 'refs/tags/')` step, since the build step is
identical either way. Every artifact in this change says "workflow
artifacts" for this, not "release assets" — the two are different GitHub
mechanisms and this change only touches the former; attaching to a GitHub
Release is a separate, unimplemented step. *Alternative rejected:* a second
workflow file — extra duplication for one conditional step.

## Risks / Trade-offs

- CI job time is bounded by the Docker image build plus both Mocha suites —
  the same cost `build-foxx.sh` already has locally; no new cost class, just
  now paid on every relevant PR instead of only when a contributor
  remembers to run it.
- A contributor who forgets to rebuild now gets a failing check instead of a
  silent stale zip — intended, per the issue. Until the optional
  branch-protection task is done, this check does not block merging; it
  only surfaces the mismatch.
- D1's determinism fix touches the packaging step every existing zip was
  built with; the first CI run on this change must confirm all four
  currently-committed zips still match a rebuild under the new packaging
  (or be rebuilt and recommitted once, per `tasks.md`).

## Migration Plan

No code or data migration for deployment. Landing this change requires, in
order: (1) apply D1's packaging fix, (2) rebuild all four zips locally and
confirm two independent builds from a clean checkout produce identical bytes
(`cmp`), (3) if any committed zip now differs from a fresh build under the
new packaging, rebuild and recommit it as part of this change, (4) add the
workflow. Existing zips are otherwise unaffected; a zip that already matches
a deterministic rebuild needs no recommit.
