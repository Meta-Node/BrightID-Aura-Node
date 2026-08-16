# core

Seed for shared logic between `v5` (soulbound verification) and `v6`
(blind-signature verification). Both serve the same underlying social
graph (users, connections, groups) from the same ArangoDB database — most
of what each version's `db.js`/`operations.js` does today is conceptually
identical, having only diverged because the two versions have lived on
separate branches for years rather than because the logic is actually
different.

This directory is currently empty on purpose. The plan is to move code
here incrementally, only once it's been verified byte-for-byte (or
functionally) identical between `v5` and `v6` — starting with whatever's
easiest to prove equivalent (e.g. group/connection graph operations that
don't touch verification), not by rewriting either version up front. See
[`docs/development-guide.md`](../../../docs/development-guide.md) for the
current state of this effort and how `v5`/`v6` are built and tested.

Do not add anything here that's specific to one verification scheme.
