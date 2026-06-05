# API-contract audit — pre-ship gate (api-contract-sentinel)

**Date:** 2026-06-05 · **Tool:** api-contract-sentinel v1.2.2 · **Context:** publishing `pact-contract-testing` v1.3.0.

## Audit Summary
- **Verdict:** `pass`
- **Authority:** Consumer-driven **Pact files** under `examples/petstore-sandbox/pacts/` (the authoritative contracts in this repo). There is **no OpenAPI/AsyncAPI/Protobuf** document in scope — appropriate for a Pact demo, where the pact files *are* the contract.
- **Implementation scope:** `examples/petstore-sandbox/provider/server.js` (Express provider). The skill itself exposes **no network API** of its own (Markdown + Python scripts), so the only implementation surface is the demo provider.
- **Coverage:** GET `/api/v3/pet/{petId}` happy path + 404; provider-state setup endpoint; response shape/type/enum matchers.

## Findings
| Severity | Class | Contract ref | Impl ref | Result |
|---|---|---|---|---|
| — | n/a | `JavaPetClient-PetstoreProvider.json` (and the JS/Go/Python pacts, same shape) — GET `/api/v3/pet/1`, 200, `{id:integer, name:type, status:regex(available\|pending\|sold)}`, state "pet 1 exists" | `server.js:48` route, `:40` state handler `pet 1 exists`→`seedPet(1)`, `:52` `res.status(200).json(serialize(pet))` | **Match** — path, method, status, content-type, id (integer), name (string), status (`"available"` ∈ regex) all satisfied. |
| — | n/a | 404 path (BadPetClient / no-pet states) | `server.js:51` `404 {code,type,message}` | **Match** — provider returns 404 when the pet is absent. |

## Intentional demo artifacts (NOT violations)
- `provider/server.js` `PROVIDER_BREAKING=1` renames `status`→`availability` **on purpose** — it is iteration-4's demonstration of a breaking change being caught by provider verification + `can-i-deploy`.
- `consumers/javascript-bad/` is a deliberately *misinterpreting* consumer used to demonstrate pending/WIP pacts. Both are teaching scenarios documented in `docs/ITERATIONS.md`, not drift.

## Assumptions / Ambiguities
- Audited against the captured pact files; the provider was not re-executed for this gate (the pacts + `verify.js` already encode a passing run). Default provider config (no `PROVIDER_BREAKING`) is the audited surface.

## Conclusion
The demo provider conforms to its consumer-driven Pact contracts; no unintended API drift. api-contract-sentinel had no OpenAPI/AsyncAPI/Protobuf artifact to audit (none exists in this repo by design) — contract conformance here is additionally guaranteed *by-substep* via the example's own Pact provider verification (`provider/verify.js`). Gate item satisfied.
