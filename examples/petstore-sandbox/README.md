# Petstore contract-testing sandbox

A **fully executed** Pact sandbox that proves the `pact-contract-testing` skill end to end against a real Pet API. Four consumer clients in four languages, one provider we control, a real Pact Broker, and four iterations that demonstrate exactly what contract testing detects — and what the broker is for.

> Everything in [docs/ITERATIONS.md](docs/ITERATIONS.md) was run on Docker Desktop (Windows) with the captured output shown verbatim. The reference API is the live `swaggerapi/petstore3` container (`http://localhost:8081/api/v3`); the **verifiable** provider is our own Node service so we can control provider states and the breaking change.

## Cast

| Component | Language / tool | Role |
|---|---|---|
| `JsPetClient` | JavaScript (Node, native) | consumer |
| `JavaPetClient` | Java 21 + Maven + pact-jvm | consumer |
| `PythonPetClient` | Python 3.12 (Docker) + pact-python | consumer |
| `GoPetClient` | Go 1.22 (Docker) + pact-go | consumer |
| `BadPetClient` | JavaScript | iteration-3 consumer that **misread** the contract |
| `PetstoreProvider` | Node/Express (`provider/`) | provider we control (states + breaking change) |
| Pact Broker | `pactfoundation/pact-broker` + Postgres (`docker-compose.yml`) | system of record + `can-i-deploy` |

All four good consumers test the same interaction: **`GET /api/v3/pet/1` → a `Pet`**, each reading only the fields it needs (`id`, `name`, `status`) and using matchers (type/regex/eachLike) instead of literals.

## The contract under test

```
GET /api/v3/pet/1
200 { id: int, name: string, status: "available|pending|sold",
      photoUrls: [string], category: {id,name}, tags: [{id,name}] }
```

## The four iterations (what each proves)

1. **Mocks + stubs** — each consumer test runs against the Pact **mock provider**, generates a pact, and publishes it. A **broker-fed stub server** then serves canned responses with no real provider.
2. **Replay / provider verification** — the provider replays the **stored** pacts from iteration 1. Catches an over-specified Java pact, then all four pass.
3. **A misinterpreting 5th consumer** — `BadPetClient` expects `status` in UPPERCASE and a non-existent `priceUsd`. Its own test passes against its own mock, but provider verification reports the exact mismatch — and **pending pacts** keep the provider build green.
4. **A provider breaking change** — the provider renames `status` → `availability`. Verification **hard-fails** for all four consumers and `can-i-deploy` **blocks** the deploy.

Full narrative with verbatim output: **[docs/ITERATIONS.md](docs/ITERATIONS.md)**.
Per-test reference (what each does / detects / the broker's role): **[docs/TEST-CATALOG.md](docs/TEST-CATALOG.md)**.

## Run it

```bash
# from this folder, in Git Bash (Windows) with Docker Desktop running
./scripts/run-sandbox.sh
```

Or step through manually (the script is fully commented). Key endpoints while running:

- Pact Broker UI: http://localhost:9292 (basic auth `pact` / `pact`)
- Provider (good): http://localhost:8082/api/v3/pet/1
- Provider (breaking): http://localhost:8083/api/v3/pet/1

### Layout

```
docker-compose.yml          Pact Broker + Postgres
provider/                   Node/Express provider we control (server.js) + verifier (verify.js)
consumers/javascript/       JsPetClient + consumer test
consumers/java/             JavaPetClient (Maven) + consumer test
consumers/python/           PythonPetClient + consumer test (runs in python:3.12 container)
consumers/go/               GoPetClient + consumer test (runs in golang:1.22 container)
consumers/javascript-bad/   BadPetClient — the iteration-3 misinterpretation
scripts/
  run-sandbox.sh            one-shot runner for all 4 iterations
  publish-pact.js           publish any pact JSON via the broker's /contracts/publish API
pacts/                      generated pact files (git-ignored)
docs/                       ITERATIONS.md, TEST-CATALOG.md
```

### Teardown

```bash
docker compose down -v
docker rm -f petstore-stub 2>/dev/null
```

## Why our own provider (not the live petstore3)?

Provider verification needs to (a) set up **provider states** and (b) let us introduce a **controlled breaking change**. The third-party `swaggerapi/petstore3` container allows neither. We keep it as the OpenAPI reference / data shape source and verify against a provider we own — the standard Pact approach. The live spec could additionally be used for **bi-directional** contract testing (see the skill's `assets/pactflow-bidirectional/`).
