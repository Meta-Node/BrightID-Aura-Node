## Purpose

Keep the `web` (nginx) container's log file from growing without bound on a
long-running node.

## ADDED Requirements

### Requirement: Bounded web container log size
The `web` service SHALL run with a `json-file` logging driver configured with
a maximum per-file size and a maximum file count, so its total retained log
size is bounded.

#### Scenario: Long-running node
- **WHEN** the `web` container has been running and logging for an extended
  period
- **THEN** the total size of its log files on disk stays approximately at or
  below `max-size` × `max-file` (Docker checks size before each write, so a
  single write can push a file slightly past the threshold before rotation),
  with the oldest entries rotated out first

#### Scenario: Stock docker compose install
- **WHEN** an operator runs `docker compose up -d` on an unmodified checkout
- **THEN** the bound applies with no extra host configuration (no logrotate
  setup, no Docker daemon config changes)

### Requirement: Override takes effect regardless of daemon-level logging config
The `web` service's per-service `logging:` configuration SHALL apply on
container recreate regardless of any logging driver or forwarding the host's
Docker daemon is configured with by default.

#### Scenario: Daemon configured with remote log forwarding
- **WHEN** the host's Docker daemon default logging driver forwards container
  logs to a remote collector
- **THEN** after the `web` container is recreated with this change, its logs
  are captured by the `json-file` driver with the configured cap instead of
  reaching that collector
