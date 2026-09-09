## Context

`docker-compose.yml`'s `web` service is stock `nginx`, no `logging:` key, so
Compose leaves whatever logging driver the host's Docker daemon defaults to
in place — typically `json-file` with no size limit, but a daemon can be
configured with a different default driver or its own rotation. The service
mounts the repo's own `web/brightid-nginx.conf` over the image's
`/etc/nginx/nginx.conf` (`docker-compose.yml:84`), replacing the default
config wholesale. That repo config still points `access_log`/`error_log` at
`/var/log/nginx/access.log` and `/var/log/nginx/error.log`
(`web/brightid-nginx.conf:33`) — the same paths the `nginx` image
pre-symlinks to `/dev/stdout`/`/dev/stderr` at build time — so nginx's access
and error output still lands on the container's stdout/stderr despite the
config replacement, and from there is captured by whichever logging driver
is in effect. The issue's repro truncated the resulting `-json.log` file by
hand.

## Goals / Non-Goals

**Goals:** bound total on-disk log size for the `web` service; no new
dependency, no change to nginx's own config; apply cleanly on a stock
`docker compose` install.

**Non-Goals:** shipping logs off-host; per-request log filtering; changing
what nginx logs or its format; applying the same bound to the other services
in this change (out of scope for this issue; worth a follow-up if wanted).

## Decisions

**D1. Docker `json-file` logging options (`max-size`, `max-file`) on the
`web` service, not in-container logrotate or an nginx-side change.** Compose
already controls this per-service with a few lines; it needs no package
inside the `nginx` image and no cron/logrotate process to keep alive in a
container that has none today. *Alternatives rejected:* in-container
logrotate — adds a package and a scheduler to an image that has neither, for
a class of logging that Docker already rotates natively; nginx `error_log`
level tuning — doesn't bound file size, only verbosity.

**D2. The per-service override applies regardless of any daemon-level
logging config, and this is documented rather than avoided.** Compose has no
way to set logging options conditionally on what the daemon already does;
setting `logging:` on the `web` service always takes effect for that
container once recreated, replacing whatever driver (including a
daemon-configured remote/collector driver) would otherwise apply. An
operator who has configured daemon-level log forwarding for this host loses
that forwarding for the `web` service specifically — `docs` will state this
explicitly rather than the change silently overriding it. *Alternative
rejected:* skip setting `logging:` when a non-default daemon driver might be
in play — Compose can't detect that at apply time, and skipping the cap
entirely would leave the original unbounded-growth problem unaddressed for
the common case (no daemon-level config) this change exists to fix.

**D3. `max-size: "10m"`, `max-file: "3"` (approximately 30MB retained).**
Small enough to keep the failure mode (a log file outgrowing the database)
from recurring; approximately 30MB across three files, though how much time
that covers depends on traffic. Both are operator-adjustable in
`docker-compose.yml` if a deployment needs more. The retained total is
approximate, not exact — Docker
checks the current file's size before writing the next log entry, so a
single write can push a file slightly past `max-size` before rotation.

## Risks / Trade-offs

- Rotated-out log lines are gone, not archived. An operator who needs
  long-term nginx logs must ship them elsewhere (out of scope here).
- An operator relying on daemon-level log forwarding/collection for this
  host loses it for the `web` service once this override takes effect (D2).
- Docker only applies `logging:` changes on container recreate
  (`up -d --force-recreate` or a normal `up -d` that detects the config
  change), not to an already-running container without one.

## Migration Plan

`docker compose up -d web` (or a full `docker compose up -d`) recreates the
`web` container with the new logging config. Recreating the container
removes its container directory, including the existing oversized
`-json.log` file for the old container ID — there is nothing to clean up
manually. An operator who wants to keep the existing log history should
capture it before recreating, with `docker logs --timestamps web >
web-nginx-logs-<date>.txt 2>&1` (redirecting stderr keeps both the access
and error streams); `docs` will note this as the one-time step, replacing
the previous manual-removal recipe.
