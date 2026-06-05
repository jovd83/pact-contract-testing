# Test catalog

Every test in the sandbox: what it does, what it detects, and the broker's role. "CDC" = consumer-driven contract.

## Consumer tests (generate pacts)

Each runs the **real client** against a Pact **mock provider**, then writes a pact file. They share one interaction: `GET /api/v3/pet/1 → 200 Pet`.

| Test | File | What it does | What it detects | Broker's role |
|---|---|---|---|---|
| JS consumer | `consumers/javascript/pactConsumer.js` | `PetClient.getPet(1)` vs mock; matchers on id/name/status/photoUrls/category/tags | The JS client correctly issues `GET /api/v3/pet/1` and maps the response; mismatch between client code and its own expectations | Stores the published `JsPetClient` pact; can serve it as a stub |
| Java consumer | `consumers/java/.../PetClientPactTest.java` | `PetClient.getPet(1)` vs mock; asserts only `id/name/status` (minimal contract) | Same for Java; demonstrates **not over-specifying** (only fields the client reads) | Stores the `JavaPetClient` pact |
| Python consumer | `consumers/python/pact_consumer.py` | `PetClient.get_pet(1)` vs mock (pact-python 3.x) | Same for Python | Stores the `PythonPetClient` pact |
| Go consumer | `consumers/go/pact_consumer_test.go` | `PetClient.GetPet(1)` vs mock (pact-go v2) | Same for Go | Stores the `GoPetClient` pact |
| **Bad** consumer | `consumers/javascript-bad/badConsumer.js` | Declares `status` UPPERCASE + a `priceUsd` field; passes vs **its own** mock | Nothing on its own — that's the trap: a green consumer test can still encode a **misreading** of the contract | Stores the (wrong) `BadPetClient` pact for later verification |

Key property: a consumer test passing proves only that the **consumer is self-consistent**. It cannot detect provider disagreement — that needs verification + the broker.

## Provider verification (replays pacts)

| Test | File | What it does | What it detects | Broker's role |
|---|---|---|---|---|
| Provider verify | `provider/verify.js` | Pulls stored pacts (selector `mainBranch`), replays each request against the real provider, compares to recorded matchers, publishes results | Whether the provider's actual responses satisfy each consumer's contract; over-specified pacts; missing/renamed fields; provider-state gaps | Selects which pacts to verify, stores pass/fail results, applies **pending + WIP** so new consumers can't break the build |

What it caught in this sandbox:
- **Iteration 2:** Java pact over-specified `photoUrls` (fixed array vs 2 elements) → `has a matching body (FAILED)`.
- **Iteration 3:** `BadPetClient`: `$.status -> Expected 'available' to match 'AVAILABLE|PENDING|SOLD'` and `missing keys: priceUsd`.
- **Iteration 4:** all four: `Actual map is missing the following keys: status` (provider renamed it).

## Deploy gate

| Check | Command | What it does | What it detects | Broker's role |
|---|---|---|---|---|
| `can-i-deploy` | `pact-broker can-i-deploy --pacticipant X --version V --to-environment production` | Reads the verification **matrix** for what's deployed in the target environment | Whether version `V` is compatible with every counterpart currently in that environment | Owns the matrix + deployment records; returns yes/no (exit 0/1) for CI |
| `record-deployment` | `pact-broker record-deployment ...` | Marks a version as currently deployed to an environment | — | Updates the matrix so future `can-i-deploy` checks are accurate |

Results in this sandbox: **safe** for `prov-1.0.0-iter3` (`Computer says yes \o/`), **blocked** for `prov-2.0.0-breaking` (all four counterparts `false`).

## The mock vs the stub vs verification (don't confuse them)

- **Mock provider** (consumer test): in-process, returns what the consumer declared. Proves the consumer's code path. Generates the pact.
- **Stub server** (`pact-stub-server`): serves canned responses from published pacts so a consumer can develop without the real provider. No verification.
- **Provider verification**: replays the recorded requests against the **real** provider and checks the responses. This is the only step that proves the two sides agree.

## Provider states

Every interaction uses `given("pet 1 exists")`. The provider's `/_pact/provider-states` endpoint seeds that data before replay (here, idempotent — the provider seeds pet 1 on start). This keeps tests **data-independent**: the consumer never assumes pre-existing data, and the provider guarantees the precondition.

## Matchers used (and why)

| Field | Matcher | Why |
|---|---|---|
| `id` | integer | value varies; only the type matters |
| `name` | string/type | free text |
| `status` | regex `available\|pending\|sold` | constrained enum, but not a single literal |
| `photoUrls` | eachLike(string) | variable-length array of strings |
| `category` | like{...} | nested object, type-matched |
| `tags` | eachLike{...} | variable-length array of objects |

Literal values were deliberately avoided (except where a field is a true constant) — the over-specification that *was* present (Java `photoUrls`) is exactly what verification caught in iteration 2.
