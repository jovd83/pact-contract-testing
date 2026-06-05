---
name: pact-javascript
description: Use when writing Pact (Pact.io) consumer-driven contract tests in JavaScript or TypeScript with @pact-foundation/pact (PactV4) — consumer tests that generate a pact, provider verification with state handlers, message pacts, and npm/Jest/Mocha/Vitest wiring. Pairs with the pact-contract-testing core skill for the shared workflow, matchers, schema-driven scaffolding, and Pact Broker/CI guidance.
license: MIT
metadata:
  version: "1.0.0"
  maturity: "stable"
  author: "jovd83"
  dispatcher-category: "testing"
  dispatcher-risk: "medium"
  dispatcher-writes-files: "true"
  requires: "pact-contract-testing"
  dispatcher-capabilities: "contract-testing, pact, pact-js, javascript, typescript"
  dispatcher-stack-tags: "pact, javascript, typescript, npm, jest"
---

# Pact for JavaScript / TypeScript (`@pact-foundation/pact`)

Language pack for the **pact-contract-testing** family. Install the core skill for the shared workflow, matcher rules, schema-driven scaffolding, and broker/CI guidance.

## When to use

Writing Pact contract tests in JS/TS (Node) with Jest, Mocha, or Vitest.

## Setup

```bash
npm i -D @pact-foundation/pact
```

## Consumer test (generates the pact)

```ts
import { PactV4, MatchersV3 } from "@pact-foundation/pact";
const { integer, regex, eachLike } = MatchersV3;

const pact = new PactV4({ consumer: "OrderWebApp", provider: "OrderService" });

it("gets order 42", () =>
  pact
    .addInteraction()
    .given("an order 42 exists")
    .uponReceiving("a request for order 42")
    .withRequest("GET", "/orders/42")
    .willRespondWith(200, (b) =>
      b.headers({ "Content-Type": "application/json" }).jsonBody({
        id: integer(42),
        status: regex("OPEN|SHIPPED|CLOSED", "OPEN"),
        lines: eachLike({ qty: integer(1) }),
      })
    )
    .executeTest(async (mock) => {
      const order = await new OrderClient(mock.url).fetch(42); // REAL client
      expect(order.id).toBe(42);
    }));
```

## Provider verification (replays the pact)

```ts
import { Verifier } from "@pact-foundation/pact";

await new Verifier({
  provider: "OrderService",
  providerBaseUrl: "http://localhost:8080",
  pactBrokerUrl: process.env.PACT_BROKER_BASE_URL,
  pactBrokerToken: process.env.PACT_BROKER_TOKEN,
  providerVersion: process.env.GIT_SHA,
  providerVersionBranch: process.env.GIT_BRANCH,
  publishVerificationResult: true,
  enablePending: true,
  includeWipPactsSince: "2024-01-01",
  consumerVersionSelectors: [{ mainBranch: true }, { deployedOrReleased: true }],
  stateHandlers: {
    "an order 42 exists": async () => { await repo.save({ id: 42, status: "OPEN" }); },
  },
}).verifyProvider();
```

## Message pacts

Use the `MessageConsumerPact` / `MessageProviderPact` APIs (or V4 `addInteraction` with `.withMessage...`). Provider side supplies `messageProviders` keyed by description. See core `references/matchers-and-states.md`.

## Notes & gotchas

- Prefer **`PactV4`** + `MatchersV3` for new tests; legacy `Pact`/`Matchers` still works.
- GraphQL: model as `POST` to the endpoint with `{ query, variables }` (core `references/schema-driven.md`).
- Matchers, not literals; one interaction per test; a state handler per `given(...)`.
