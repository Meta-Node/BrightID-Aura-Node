## 1. Compose

- [ ] 1.1 `docker-compose.yml`: add `logging` to the `web` service —
      `driver: json-file`, `max-size: "10m"`, `max-file: "3"` (D1, D3).

## 2. Docs

- [ ] 2.1 `docs/installation-guide.md`: the cap, how to raise it, that it
      replaces any daemon-level logging configuration for this container (D2),
      and the one-time `docker logs` capture before recreation.

## 3. Review

- [ ] 3.1 `openspec validate cap-web-container-log-size --strict` passes.
