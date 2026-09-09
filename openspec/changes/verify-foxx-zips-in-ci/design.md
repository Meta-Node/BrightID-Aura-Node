## Decisions

**D1. Make packaging deterministic before adding any comparison.** In
`scripts/foxx-build-inner.sh`, after the staging copy: normalize modification
times across the staged tree (`touch -d "@${SOURCE_DATE_EPOCH:-0}"`), enumerate
files and symlinks with `find | LC_ALL=C sort` and hand that list to `zip` on
stdin (`zip -X -q -@`) instead of letting `zip -r` walk the directory, and keep
`-y` off so symlinks are stored dereferenced, as the committed archives already
are. `-X` drops the extra fields (UID/GID, extended timestamps) while leaving
the permission bits zip keeps in the standard attributes. *Rejected:*
`strip-nondeterminism` over the existing `zip -rq` output — another dependency
in the builder image for what `sort` plus `-X` already does.

**D2. "Byte-for-byte identical" means `cmp` reports no difference.** Two builds
of one commit, run independently — separate checkouts, separate container
invocations, same pinned builder image — produce zips that `cmp` finds equal;
the CI check applies the same `cmp` between each rebuilt zip and its committed
copy. A difference therefore means the source changed without a rebuild.
*Rejected:* unzip both and diff the extracted files — looser than D1 makes
possible, and it would hide a regression in D1 rather than catch it.

**D3. Pin the builder image, and be clear what the pin does and does not
fix.** Pinning `node:20-alpine` by digest fixes the base layer exactly; pinning
the `apk add` versions (`gnupg`, `pwgen`, `binutils`, `numactl`,
`numactl-tools`, `zip`) fixes what a build installs on top of it. Neither
freezes Alpine's package index: when a pinned version is dropped upstream the
image build fails loudly, which is the point — it cannot drift silently into a
different toolchain. `foxx-cli@2.1.1` and the ArangoDB package version are
already pinned in the Dockerfile. *Rejected:* leave the floating tag — the same
commit would build against a different Node months later.

**D4. Trigger on every path that can change the zips; run on
`ubuntu-latest`.** Path filters: `web_services/foxx/**`,
`scripts/build-foxx.sh`, `scripts/foxx-build-inner.sh`,
`scripts/foxx-builder.Dockerfile`, and `.github/workflows/foxx-zips.yml`. The
narrower filter first considered (`web_services/foxx/**`,
`scripts/build-foxx*.sh`) missed the inner script and the Dockerfile, so a
packaging change would have shipped unverified. `docker build`/`docker run`
work as-is on the standard runner. *Rejected:* run on every push — CI minutes
for changes that cannot affect the zips. *Rejected:* upload the zips as
workflow artifacts on tag pushes in the same workflow — `paths:` filters apply
to tag pushes too, so a tag whose commit touches none of those paths would skip
the job entirely; artifacts are not needed for this check and are kept as an
optional, separate task.

## Risks / Trade-offs

- D1's packaging fix is what forces the one-time recommit of all four
  archives; until that recommit lands, the check fails on an unchanged source
  tree.
- The archives contain dereferenced symlinks today. If a later change adds
  `zip -y`, `node_modules/.bin` entries become links with no content and the
  packages that need them break — the docs note in `scripts/README.md` guards
  this.
