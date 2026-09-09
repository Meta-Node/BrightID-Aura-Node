## Decisions

**D1. Cap with Docker `json-file` logging options on the `web` service, not
in-container logrotate or an nginx-side change.** Compose controls this
per-service in four lines, with no package inside the `nginx` image and no
scheduler to keep alive in a container that has none. *Rejected:* in-container
logrotate — a package and a cron for rotation Docker already does natively;
`error_log` level tuning — bounds verbosity, not file size.

**D2. The per-service override applies regardless of any daemon-level logging
config, and the docs say so.** Compose cannot set logging conditionally on what
the daemon already does: once the container is recreated, this block replaces
whatever driver — including a remote collector — the daemon default would
apply. *Rejected:* skip the block when a non-default daemon driver might be in
play — Compose cannot detect that, and skipping leaves the unbounded growth
unfixed for the common case.

**D3. `max-size: "10m"`, `max-file: "3"` — approximately 30MB retained.** Round
numbers, not measurements: small enough that a log file cannot outgrow the
database again, large enough for basic troubleshooting, and adjustable in
`docker-compose.yml`. The total is approximate — a single write can push a file
slightly past `max-size` before rotation. *Rejected:* a larger cap — the
failure this fixes is size, not retention depth.

## Migration Plan

`docker compose up -d web` recreates the container with the new logging config.
Recreation removes the old container's directory, including its oversized
`-json.log`. An operator who wants that history should capture it first with
`docker logs --timestamps web > web-nginx-logs-<date>.txt 2>&1`.
