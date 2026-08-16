# Open questions

Things worth doing that weren't done as part of the change that found them —
recorded here instead of fixed on the spot, per the bug-hunter skill's
"write it down" option. Each entry: the cause, what it produced, the
recommendation, the odds, and when it was recorded.

## `db.connect()` conflates validation with bulk replay

**Recorded:** 2026-08-16, during the v5 self-connection-guard backport
(commit `14f0fb5`, branch `fix-v5-bugs`).

**Cause:** `web_services/foxx/v5/db.js`'s `connect()` is both (a) the
business-rule enforcer for the live `Connect`/`Add Connection`/`Remove
Connection` operations, and (b) the primitive `initdb.js`'s historical
migrations (`v5_3` and friends) replay old rows through when upgrading a
legacy database. Any new rule added to `connect()` — like the self-connection
guard this commit added — applies to both at once, so replaying old data
can hit a rule that didn't exist when that data was written, aborting the
entire upgrade chain (`initdb()` fails, `foxx install` fails hard, the
service never installs).

**What it produced:** all 3 bugs fixed in `14f0fb5` were instances of this
exact shape — `v5_3`'s connections/trusted/flaggers replay loops each had to
be taught to skip self-pairs so the new guard in `connect()` wouldn't abort
them. The same class of bug will recur for any future rule added to
`connect()`, unless something changes.

**Recommendation:** separate "validate a Connect operation" from "write a
connection edge" — two functions instead of one, so replay code can call the
edge-writer directly without going through whatever validation rules have
accumulated since the data was written. **Odds: medium** — clean in
principle, but touches replay paths (`v5_3`, the `v5_9_*` chain) that are
effectively dead code on every live node today (they only matter when
upgrading a database that predates whichever migration is running), and v5
is slated to eventually merge with v6 anyway (see
[`web_services/foxx/core/README.md`](../web_services/foxx/core/README.md)),
which would be a natural point to revisit this rather than doing it twice.

**Why not fixed now:** bigger than the change that found it (a single
targeted bug fix), and the actual risk today is low — this only bites when
someone adds a new rule to `connect()`, which won't happen by accident.

**When this stops applying:** once v5 and v6's connection-writing logic is
unified (see `web_services/foxx/core/`), this note should be revisited
alongside that work — the split described above may end up happening
naturally as part of separating shared graph-writing logic from
version-specific validation, rather than as its own dedicated refactor.
