# Provisioning a Pact Broker (when you don't have one)

The Pact Broker is a **separate application** from the Pact client libraries — the
skill publishes/verifies *against* a broker, it is not bundled in your test
dependencies. Pick one of the three options below. The skill works with any of them
once `PACT_BROKER_BASE_URL` (+ auth) is set.

| Option | When to choose it | Hosting | Auth |
|---|---|---|---|
| **PactFlow (managed)** | You want zero-ops, bi-directional contract testing, SSO, the free Developer plan. | SaaS (cloud) | `PACT_BROKER_TOKEN` (bearer) |
| **Self-host (this folder)** | Local dev, on-prem/air-gapped, GDPR/data-residency constraints, no cloud allowed. | Docker (postgres + `pactfoundation/pact-broker`) | `PACT_BROKER_USERNAME` / `PACT_BROKER_PASSWORD` (basic) |
| **Existing broker** | Your org already runs one. | n/a | as provided |

> If you already have a broker, **do not provision another** — just set the env vars.

## Self-host with the bundled compose

This folder ships a production-leaning local broker (persistent volume, read-only
credentials, healthcheck) — distinct from the throwaway one under
`examples/petstore-sandbox/`.

```bash
# Start (idempotent) and wait until healthy:
./scripts/start_broker.sh            # bash / macOS / Linux / WSL / Git-Bash
# or
./scripts/start_broker.ps1           # Windows PowerShell

# Stop (keep data):           docker compose -f assets/broker/docker-compose.yml down
# Stop and wipe contracts:    docker compose -f assets/broker/docker-compose.yml down -v
```

On success the script prints the exact `export`/`$env:` lines to point the rest of
the skill (`publish_pacts.*`, `can_i_deploy.*`) at the new broker.

### Defaults (override via env before starting)

| Env var | Default | Purpose |
|---|---|---|
| `PACT_BROKER_PORT` | `9292` | Host port for the broker UI/API |
| `PACT_BROKER_USERNAME` / `PACT_BROKER_PASSWORD` | `pact` / `pact` | Read-write basic auth |
| `PACT_BROKER_READONLY_USERNAME` / `PACT_BROKER_READONLY_PASSWORD` | `readonly` / `readonly` | Read-only basic auth (dashboards, CI reads) |
| `PACT_BROKER_DB_USER` / `PACT_BROKER_DB_PASSWORD` / `PACT_BROKER_DB_NAME` | `pactbroker` | Postgres credentials |

**Change the default credentials before exposing the broker beyond localhost.**
These defaults exist only so local dev works out of the box; they are not safe for
a shared or internet-reachable deployment.

## PactFlow instead

Sign up at <https://pactflow.io> (free Developer plan), create an API token, then:

```bash
export PACT_BROKER_BASE_URL=https://<your-org>.pactflow.io
export PACT_BROKER_TOKEN=<token>     # never hardcode; use CI secrets
```

PactFlow is also required for **bi-directional contract testing** — see
`assets/pactflow-bidirectional/`.
