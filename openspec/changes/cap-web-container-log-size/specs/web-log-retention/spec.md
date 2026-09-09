## ADDED Requirements

### Requirement: Bounded web container log size
The `web` service SHALL run with the `json-file` logging driver configured with
a maximum per-file size (`max-size`) and a maximum file count (`max-file`), so
its total retained log size is bounded.

#### Scenario: Long-running node
- **WHEN** the `web` container has been running and logging for an extended
  period
- **THEN** the total size of its log files stays approximately at or below
  `max-size` × `max-file` — a single write can push a file slightly past
  `max-size` before rotation — with the oldest entries rotated out first

### Requirement: Override replaces daemon-level logging config
The `web` service's `logging:` configuration SHALL apply on container recreate
regardless of the logging driver the host's Docker daemon is configured with by
default.

#### Scenario: Daemon configured with remote log forwarding
- **WHEN** the host's Docker daemon default logging driver forwards container
  logs to a remote collector
- **THEN** after the `web` container is recreated, its logs are captured by the
  `json-file` driver with the configured cap instead of reaching that collector
