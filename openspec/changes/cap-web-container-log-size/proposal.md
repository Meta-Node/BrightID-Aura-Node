## Why

`docker-compose.yml`'s `web` service (nginx) sets no logging options, so Docker's default `json-file` driver keeps every log line forever in that container's log file (unless the host's Docker daemon has its own default logging config, which this override replaces). On a long-running node that file grows unbounded — one operator reported it larger than the database and had to `truncate` it by hand (upstream [BrightID-Node#365](https://github.com/BrightID/BrightID-Node/issues/365)).

## What Changes

- `docker-compose.yml`: the `web` service gets a `logging` block using the `json-file` driver with `max-size`/`max-file` options, capping total retained log size instead of leaving it unbounded.
- `docs/installation-guide.md` gets a line noting the cap, how to raise it, and that it overrides any daemon-level logging configuration for this container.

## Capabilities

### New Capabilities
- `web-log-retention`: bounding the disk nginx container logs can use.

### Modified Capabilities
(none)

## Impact

Operators: nginx access/error logs older than the retained window are rotated out, not archived — anyone relying on long-lived nginx logs for audit needs their own log shipping. An operator whose Docker daemon is already configured to forward container logs to a collector loses that forwarding for the `web` service specifically, since this per-service override replaces whatever driver the daemon default would otherwise apply; `docs/installation-guide.md` will call this out. Upgrade: `docker compose up -d web` recreates the container to pick up the new logging options (Docker applies `logging:` changes on recreate, not to an already-running container); no image rebuild, no data volume touched, no downtime beyond that container's own restart.
