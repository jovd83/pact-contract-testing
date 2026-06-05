# Pact Broker / PactFlow & CI/CD

The broker is the **system of record** for contracts and verification results. It decouples consumer and provider pipelines and powers `can-i-deploy`. It is a **separate application** from the Pact client libraries — you publish/verify against it; it is not bundled with your test dependencies.

## Provisioning a broker (if you don't have one)

The skill needs a broker to publish to. Three ways to get one — full comparison and credentials matrix in `assets/broker/README.md`:

| Option | When | Auth |
|---|---|---|
| **Existing broker** (PactFlow / org-hosted) | One already exists — **reuse it, don't provision another** | as provided |
| **PactFlow (managed)** | Zero-ops, bi-directional contract testing, free Developer plan | `PACT_BROKER_TOKEN` |
| **Self-host (Docker)** | Local dev, on-prem/air-gapped, data-residency/no-cloud constraints | `PACT_BROKER_USERNAME` / `PACT_BROKER_PASSWORD` |

Self-host quickstart (boots postgres + `pactfoundation/pact-broker` with a persistent volume, waits for health, prints the env vars to export):

```bash
./scripts/start_broker.sh        # bash; or ./scripts/start_broker.ps1 on Windows
# → http://localhost:9292 (basic auth pact/pact by default — change before exposing it)
```

Override port/credentials via env before starting (`PACT_BROKER_PORT`, `PACT_BROKER_USERNAME`, `PACT_BROKER_PASSWORD`). The bundled `assets/broker/docker-compose.yml` is the reusable broker; the one under `examples/petstore-sandbox/` is a throwaway for the demo only.

## Configuration (never hardcode)

| Env var | Purpose |
|---|---|
| `PACT_BROKER_BASE_URL` | Broker / PactFlow base URL |
| `PACT_BROKER_TOKEN` | PactFlow bearer token (preferred) |
| `PACT_BROKER_USERNAME` / `PACT_BROKER_PASSWORD` | Basic auth (self-hosted broker) |

## Versioning (do this right or `can-i-deploy` is meaningless)

- **Application version = git commit SHA** (`git rev-parse --short HEAD`). Unique, traceable.
- Tag the version with the **branch** (`--branch $(git rev-parse --abbrev-ref HEAD)`).
- Record **deployments/releases to environments** (e.g. `test`, `production`) — this is the modern replacement for tags.

## Publish pacts (consumer side)

```bash
pact-broker publish ./pacts \
  --consumer-app-version "$(git rev-parse --short HEAD)" \
  --branch "$(git rev-parse --abbrev-ref HEAD)" \
  --broker-base-url "$PACT_BROKER_BASE_URL" \
  --broker-token "$PACT_BROKER_TOKEN"
```

Use `scripts/publish_pacts.sh` / `.ps1` which fills version and branch from git.

## Verify pacts (provider side)

Select **which** pacts to verify with **consumer version selectors** (don't just verify "latest"):

- `{ "mainBranch": true }` — latest from each consumer's main branch.
- `{ "deployedOrReleased": true }` — what's currently in environments.
- `{ "matchingBranch": true }` — the consumer branch matching the provider branch.

Always enable, to protect the provider build:

- **Pending pacts** (`enablePending: true`) — a not-yet-verified consumer change is reported but does **not** fail the provider build.
- **WIP pacts** (`includeWipPactsSince: "<date>"`) — new interactions are surfaced for feedback without breaking the build.

Publish results back with the **provider version** (git SHA) and `publishVerificationResult: true`.

## can-i-deploy (the deploy gate)

```bash
pact-broker can-i-deploy \
  --pacticipant OrderWebApp --version "$(git rev-parse --short HEAD)" \
  --to-environment production \
  --broker-base-url "$PACT_BROKER_BASE_URL" --broker-token "$PACT_BROKER_TOKEN"
```

- Exit `0` → every integration this version participates in has a successful verification in/relative to that environment → safe.
- Exit `1` → missing or failed verification → **block the deploy**.
- Use `scripts/can_i_deploy.sh` / `.ps1`.

## Record deployment / release

After a successful deploy:

```bash
pact-broker record-deployment --pacticipant OrderWebApp \
  --version "$(git rev-parse --short HEAD)" --environment production \
  --broker-base-url "$PACT_BROKER_BASE_URL" --broker-token "$PACT_BROKER_TOKEN"
```

(Use `record-release` for things made available but not actively deployed, e.g. libraries.)

## can-i-merge (trunk-based development)

For teams that gate on **merge** rather than deploy, `can-i-merge` checks the integration against the main branch:

```bash
pact-broker can-i-merge --pacticipant OrderWebApp --version "$(git rev-parse --short HEAD)" \
  --broker-base-url "$PACT_BROKER_BASE_URL" --broker-token "$PACT_BROKER_TOKEN"
```

Attach the CI run to results with `--build-url <ci-job-url>` on publish/verify so a broker result links back to the build.

## Webhooks

Configure the broker to call CI on `contract_content_changed` / `contract_requiring_verification_published` so the **provider verification runs automatically** when a consumer publishes a new pact. The provider job publishes results back, completing the loop before `can-i-deploy`.

## The pipeline (both sides)

```
CONSUMER CI:  test → generate pact → publish (version=SHA, branch) → can-i-deploy → deploy → record-deployment
                                            │
                                webhook ────┘ triggers
                                            ▼
PROVIDER CI:  fetch pacts (selectors) → verify (pending+WIP) → publish results
              ... then provider's own: can-i-deploy → deploy → record-deployment
```

CI template: `assets/ci/github-actions.yml`.

## Tags (legacy)

Tags (`create-version-tag`, `can-i-deploy --to <tag>`) still work but are **deprecated** in favour of environments + `record-deployment`. Only use tags against an older broker that lacks environment support.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `can-i-deploy` exit 1, "no results" | Provider never verified this consumer version | Trigger provider verification (webhook/manual); ensure selectors include this consumer. |
| Provider build fails on a brand-new consumer interaction | Pending/WIP not enabled | Enable `enablePending` + `includeWipPactsSince`. |
| Pact not visible | Publish skipped or wrong broker URL/token | Run `publish_pacts.*`; check env vars. |
| Verifying stale contracts | Selector = "latest" only | Use `mainBranch` / `deployedOrReleased` selectors. |
