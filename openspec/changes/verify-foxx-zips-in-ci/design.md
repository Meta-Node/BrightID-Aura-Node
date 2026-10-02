## Decisions

**D1. Make packaging deterministic before adding any comparison.** In
`scripts/foxx-build-inner.sh`, after the staging copy: normalize modification
times and permissions on the staged tree (times to `${SOURCE_DATE_EPOCH:-0}`;
files to 644, or 755 if executable); enumerate files and symlinks, with no
directory entries, using `find | LC_ALL=C sort`, and hand that list to `zip` on
stdin (`zip -X -q -@`) instead of letting `zip -r` walk the directory; keep
`-y` off so symlinks are stored dereferenced, as the committed archives
already are; and fail if the staged tree contains a symlink to a directory,
which would otherwise be stored as an empty entry. `-X` drops the extra fields
(UID/GID, extended timestamps) but not the permission bits, which follow the
checkout's umask. *Rejected:* `strip-nondeterminism` over the existing
`zip -rq` output — another dependency in the builder image for what this step
already does.

**D2. "Byte-for-byte identical" means `cmp` reports no difference.** Two builds
of one commit, run independently — separate checkouts, separate container
invocations, same pinned builder image — produce zips that `cmp` finds equal;
the CI check applies the same `cmp` between each rebuilt zip and its committed
copy. A difference therefore means the committed zip no longer matches what its
source and packaging build.
*Rejected:* unzip both and diff the extracted files — looser than D1 makes
possible, and it would hide a regression in D1 rather than catch it.

**D3. Pin the builder image.** Pinning `node:20-alpine` by digest fixes the
base layer exactly; pinning the `apk add` versions (`gnupg`, `pwgen`,
`binutils`, `numactl`, `numactl-tools`, `zip`) fixes the packages it names.
`foxx-cli@2.1.1` and the ArangoDB package version are already pinned in the
Dockerfile. *Rejected:* leave the floating tag — the same commit would build
against a different Node months later.

**D4. Trigger on every path that can change the zips; run on
`ubuntu-latest`.** Path filters: `web_services/foxx/**`,
`scripts/build-foxx.sh`, `scripts/foxx-build-inner.sh`,
`scripts/foxx-builder.Dockerfile`, and `.github/workflows/foxx-zips.yml`. The
narrower filter first considered (`web_services/foxx/**`,
`scripts/build-foxx*.sh`) missed the inner script and the Dockerfile, so a
packaging change would have shipped unverified. `docker build`/`docker run`
work as-is on the standard runner. *Rejected:* run on every push — CI minutes
for changes that cannot affect the zips. Tag pushes run the check too: GitHub does not evaluate path filters
for tags. Uploading the zips as artifacts is not needed for this check and
stays an optional task.

## Risks / Trade-offs

- D1's packaging fix is what forces the one-time recommit of all four
  archives; until that recommit lands, the check fails on an unchanged source
  tree.
- The archives contain dereferenced symlinks today. If a later change adds
  `zip -y`, `node_modules/.bin` entries become links with no content and the
  packages that need them break — the docs note in `scripts/README.md` guards
  this.
- D3's `apk` pins fail a fresh image build once Alpine drops the pinned
  version from its index, which it does when the package updates; the pin then
  has to be bumped. It fails loudly rather than drifting.
