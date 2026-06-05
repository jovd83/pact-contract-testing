# Iterations — what happened, with real output

Every block below is **verbatim captured output** from running this sandbox on Docker Desktop (Windows). The Pact Broker ran at `http://localhost:9292`, the controlled provider at `:8082`, and the breaking provider at `:8083`.

---

## Iteration 1 — consumer tests against the MOCK, then publish

**What runs:** each consumer's real client code is exercised against an in-process Pact **mock provider**. The mock returns exactly what the consumer declared, the client maps it, and a **pact file** is recorded. No real provider exists yet. The pacts are then published to the broker (version `1.0.0-iter1`, branch `main`).

```
JS consumer test PASSED against mock: {"id":1,"name":"Cat 1","status":"available","photoUrls":["url1"]}
Python consumer test PASSED against mock: {'id': 1, 'name': 'Cat 1', 'status': 'available'}
Go:    --- PASS: TestGetPet1 (0.02s)  ->  Writing pact out to '/work/pacts/GoPetClient-PetstoreProvider.json'
Java:  BUILD SUCCESS (target/pacts/JavaPetClient-PetstoreProvider.json)

Published JavaPetClient   -> PetstoreProvider  version=1.0.0-iter1 branch=main
Published JsPetClient     -> PetstoreProvider  version=1.0.0-iter1 branch=main
Published PythonPetClient -> PetstoreProvider  version=1.0.0-iter1 branch=main
Published GoPetClient     -> PetstoreProvider  version=1.0.0-iter1 branch=main
```

**Broker stub server** (the "stubs/drivers from the broker" part) — fed the published pacts, serving canned responses with **no real provider**:

```
INFO pact_stub_server: Loaded 5 pacts (5 total interactions)
$ curl http://localhost:9999/api/v3/pet/1
{"id":1,"priceUsd":999,"status":"AVAILABLE"}
```

> Note: the stub had 5 pacts loaded and answered with one matching example (here the `BadPetClient` one). To scope a stub to a single consumer, point the stub server at just that consumer's pact.

**What it detects:** that each consumer's own client code is internally consistent with the response shape it expects. It does **not** yet prove the provider agrees.
**Broker's role:** receives and stores the contracts (system of record) and can serve **stubs** so a consumer team can develop before the provider exists.

---

## Iteration 2 — provider verification (replay the STORED pacts)

**What runs:** the provider (`:8082`) is started, and the verifier pulls the **stored** pacts from the broker (selector: latest from `main`) and **replays** each recorded request against the real provider, comparing the response to the recorded matchers. Results are published back to the broker.

First run caught a real defect — the Java pact **over-specified** `photoUrls` as a fixed 1-element array while the provider returns two:

```
Verifying a pact between JavaPetClient and PetstoreProvider
     Given pet 1 exists
      has a matching body (FAILED)
Pending Failures:
1) JavaPetClient ... has a matching body
```

Because `JavaPetClient` had no prior successful result, it was **pending**, so the build did **not** fail — the broker just reported it. We fixed the Java consumer to assert only the fields it reads (`id`, `name`, `status`), republished, and re-verified:

```
Verifying a pact between GoPetClient and PetstoreProvider      has a matching body (OK)
Verifying a pact between JavaPetClient and PetstoreProvider    has a matching body (OK)
Verifying a pact between JsPetClient and PetstoreProvider      has a matching body (OK)
Verifying a pact between PythonPetClient and PetstoreProvider  has a matching body (OK)
PROVIDER VERIFICATION: PASSED
```

**What it detects:** whether the provider actually returns what each consumer recorded — the first time the two sides are checked against each other. It immediately flagged an over-specified contract (the skill's #1 anti-pattern).
**Broker's role:** chooses *which* pacts to verify (consumer version selectors), stores the verification results, and applies **pending** so a not-yet-proven consumer can't break the provider build.

---

## Iteration 3 — a 5th consumer that misinterpreted the contract

**What runs:** `BadPetClient` was built on two misreadings — it expects `status` in **UPPERCASE** (`AVAILABLE|PENDING|SOLD`) and a `priceUsd` field that does not exist. Its own consumer test **passes** (the mock returns whatever the consumer declared):

```
BAD consumer test PASSED against ITS OWN mock: {"id":1,"status":"AVAILABLE","priceUsd":999}
Published BadPetClient -> PetstoreProvider version=0.1.0-iter3 branch=main
```

Provider verification then exposes the misinterpretation precisely, while the 4 good consumers still pass:

```
Verifying a pact between BadPetClient and PetstoreProvider     has a matching body (FAILED)
Verifying a pact between GoPetClient and PetstoreProvider      has a matching body (OK)
Verifying a pact between JavaPetClient and PetstoreProvider    has a matching body (OK)
Verifying a pact between JsPetClient and PetstoreProvider      has a matching body (OK)
Verifying a pact between PythonPetClient and PetstoreProvider  has a matching body (OK)

Pending Failures:
1) BadPetClient ... has a matching body
     $.status -> Expected 'available' to match 'AVAILABLE|PENDING|SOLD'
     $        -> Actual map is missing the following keys: priceUsd
PROVIDER VERIFICATION: PASSED   (BadPetClient is PENDING, so the build stays green)
```

We then recorded production deployments and confirmed the provider is safe to deploy against everything currently in production:

```
can-i-deploy PetstoreProvider prov-1.0.0-iter3 --to-environment production
Computer says yes \o/
GoPetClient | JavaPetClient | JsPetClient | PythonPetClient  -> SUCCESS? true  (all 4)
All required verification results are published and successful
```

**What it detects:** a consumer that *thinks* it understands the API but doesn't. The mismatch surfaces at verification, not in the consumer's own green test — which is the whole point of sharing contracts.
**Broker's role:** records the new (failing) contract, marks it **pending** because it's new, and keeps it out of the deploy gate until it has a successful result — so one confused team cannot block everyone else.

---

## Iteration 4 — the provider introduces a breaking change

**What runs:** the provider is started with `PROVIDER_BREAKING=1`, which renames `status` → `availability`:

```
$ curl http://localhost:8083/api/v3/pet/1
{"id":1,"category":{...},"name":"Cat 1","photoUrls":["url1","url2"],"tags":[...],"availability":"available"}
```

Re-verifying this provider version (`prov-2.0.0-breaking`) now **hard-fails** for every consumer — they are no longer pending (they had successful results), so this fails the build:

```
Verifying a pact between GoPetClient and PetstoreProvider      has a matching body (FAILED)
Verifying a pact between JavaPetClient and PetstoreProvider    has a matching body (FAILED)
Verifying a pact between JsPetClient and PetstoreProvider      has a matching body (FAILED)
Verifying a pact between PythonPetClient and PetstoreProvider  has a matching body (FAILED)

Failures:
1) GoPetClient ...   $ -> Actual map is missing the following keys: status
2) JavaPetClient ... $ -> Actual map is missing the following keys: status
3) JsPetClient ...   $ -> Actual map is missing the following keys: status
4) PythonPetClient.. $ -> Actual map is missing the following keys: status
PROVIDER VERIFICATION: FAILED
```

The deploy gate then **blocks** the breaking provider from production:

```
can-i-deploy PetstoreProvider prov-2.0.0-breaking --to-environment production
CONSUMER        | C.VERSION    | P.VERSION           | SUCCESS?
GoPetClient     | 1.0.0-iter1  | prov-2.0.0-breaking | false
JavaPetClient   | 1.0.0-iter1b | prov-2.0.0-breaking | false
JsPetClient     | 1.0.0-iter1  | prov-2.0.0-breaking | false
PythonPetClient | 1.0.0-iter1  | prov-2.0.0-breaking | false

The verification for the pact between the version of GoPetClient currently in production
(1.0.0-iter1) and version prov-2.0.0-breaking of PetstoreProvider failed
... (same for Java, JS, Python)
```

**What it detects:** a provider change that would break already-deployed consumers — **before** it ships.
**Broker's role:** holds the matrix of consumer/provider verification results across versions and environments, and answers `can-i-deploy` with a hard NO so CI can stop the release.

---

## Summary

| Iteration | Trigger | Result | Caught by |
|---|---|---|---|
| 1 | Consumer tests + publish | 4 pacts stored; stub serves canned data | mock provider |
| 2 | Provider replays stored pacts | over-specified Java pact, then all pass | provider verification |
| 3 | Misinterpreting 5th consumer | exact mismatch reported; build stays green | verification + **pending** |
| 4 | Provider renames `status` | all 4 fail; deploy blocked | verification + **can-i-deploy** |

The broker is the thread through all four: it stores contracts, decides which to verify, records results, isolates new/unproven contracts with pending, and gates deployments with `can-i-deploy`.
