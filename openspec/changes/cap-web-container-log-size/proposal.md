## Why

`docker-compose.yml`'s `web` service (nginx) sets no logging options, so it inherits the Docker daemon's default — on a stock install, `json-file` with no rotation, and the container's log file grows without bound. One operator reported it larger than the database and had to `truncate` it by hand (upstream [BrightID-Node#365](https://github.com/BrightID/BrightID-Node/issues/365)). Other long-lived services inherit the same default; this change fixes `web`, the one that has bitten an operator, and leaves the rest to a follow-up.

## What Changes

- `docker-compose.yml`: the `web` service gets a `logging` block using the `json-file` driver with `max-size: "10m"` and `max-file: "3"`.
- `docs/installation-guide.md` gets a line noting the cap, how to raise it, that it replaces any daemon-level logging configuration for this container, and that recreating the container removes the old log — capture it first with `docker logs --timestamps web > web-nginx-logs-<date>.txt 2>&1`.

## Impact

- Rotated-out nginx access and error lines are gone, not archived; anyone who needs long-lived nginx logs must ship them elsewhere.
- An operator whose Docker daemon forwards container logs to a collector loses that forwarding for `web` specifically, because a per-service `logging:` block replaces the daemon default.
- Recreating the container removes its old `-json.log` along with the old container directory, so the oversized file needs no manual cleanup — but capture anything worth keeping first.
- Upgrade: Docker applies `logging:` changes only when the container is recreated; `docker compose up -d web` recreates it once it detects the config change. No image rebuild, no data volume touched, no downtime beyond that container's restart.
