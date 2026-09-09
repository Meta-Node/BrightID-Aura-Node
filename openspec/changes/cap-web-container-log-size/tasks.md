## 1. Compose

- [ ] 1.1 `docker-compose.yml`: add `logging: driver: json-file, options:
      max-size: "10m", max-file: "3"` to the `web` service (D1, D3).

## 2. Docs

- [ ] 2.1 `docs/installation-guide.md`: note the log cap (approximately
      30MB retained), how to raise `max-size`/`max-file`, that the override
      replaces any daemon-level logging config for this container (D2), and
      that recreating the container removes the old log — copy it out first
      if it's needed.

## 3. Review

- [ ] 3.1 `openspec validate cap-web-container-log-size --strict` passes.
- [ ] 3.2 A human reads every changed word before the PR opens.
