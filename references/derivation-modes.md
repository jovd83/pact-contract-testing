# Test derivation modes — where a contract test comes from

A Pact contract test always ends up the same way (consumer code runs against a mock; provider replays the pact), but the **interactions can be derived from different sources**. Pick the mode by what you have. Modes combine freely — e.g. code-driven structure + schema-driven matchers + cookbook recipes.

| Mode | Start from | Best when | Trap to avoid |
|---|---|---|---|
| **Code-driven** | The real client/provider code | You already have the integration code | Asserting the request you hand-built instead of what the client sends |
| **Schema-driven** | OpenAPI/XSD/WSDL/JSON Schema/Protobuf/Avro/AsyncAPI/GraphQL | A contract source exists | Treating the schema as the pact; copying it verbatim as literals |
| **Requirements-driven** | Use cases, user stories, acceptance criteria (Gherkin) | Designing tests before/with the code | Encoding business behaviour instead of message shape |
| **Cookbook-driven** | A catalogue of reusable recipes | Recurring cross-cutting patterns | Applying a recipe that doesn't match the real API |

## 1. Code-driven (the Pact default)

Pact is consumer-driven and **code-first**, so this is the canonical mode: wrap the consumer's **existing client method** in a test and let the call shape the interaction.

1. Find the client call (e.g. `OrderClient.fetch(id)`).
2. Write one interaction per call path the consumer actually uses.
3. In the test, invoke the **real client** against the mock server URL — never assert a hand-built request.
4. Add matchers for the fields the client reads; ignore fields it never touches.
5. Provider side: derive provider states from the data the existing handlers require.

Use this when the integration code already exists or you are adding contract coverage to a working client.

## 2. Schema-driven

Derive request shape + matchers from a contract source. Full mapping for all 8 source types and the scaffolder is in `schema-driven.md`. Schema-driven typically supplies the **matchers**; code-driven supplies the **call**.

## 3. Requirements-driven (use cases, user stories, acceptance criteria)

Turn each requirement's **external interactions** into Pact interactions.

1. Take the story/use case and its acceptance criteria (ideally Gherkin).
2. For each scenario, identify the consumer→provider call(s) it implies.
3. Map the **`Given`** precondition → Pact **provider state**; the **`When`** action → request; the **`Then`** outcome → response matchers.
4. One scenario interaction per test; keep assertions on message shape, not on UI/business behaviour.

Example mapping:

```
Story: "As a buyer I can view an order so I can track shipping."
AC (Gherkin):
  Given an order 42 exists and is SHIPPED      -> provider state "an order 42 exists" (status SHIPPED)
  When the app requests order 42               -> GET /orders/42
  Then it shows id, status and a tracking code -> response matchers: id(int), status(regex), trackingCode(string)
```

Pairs with `acceptance-criteria-designer` / BDD skills to produce the criteria, and with code-driven once the client exists. Behaviour assertions (does shipping actually update?) belong in functional tests, not the pact.

## 4. Cookbook-driven

Build interactions from a **catalogue of reusable recipes** for cross-cutting concerns, so contracts stay consistent across teams. Each recipe is a named matcher/interaction snippet:

- **Auth header**: required `Authorization: Bearer <jwt-regex>` on the request.
- **Pagination**: `page`, `size` query params; response `items` (`eachLike`), `total` (int), `next` (string/regex).
- **Error envelope (RFC 7807 problem+json)**: `type`, `title`, `status`, `detail` matchers + `Content-Type: application/problem+json`.
- **Idempotency**: required `Idempotency-Key` header (uuid regex).
- **Timestamps**: ISO-8601 datetime matcher, never a literal instant.
- **Correlation/trace id**: header regex.

How to apply:

1. Identify the cross-cutting concern in the interaction.
2. Drop in the recipe's matcher snippet (keep them in your own `cookbook/` and reuse across consumers).
3. Confirm the recipe matches the **real** API — a recipe is a default, not a license to skip checking the actual contract.

## Choosing

- Have working code → **code-driven** (+ schema-driven matchers if a spec exists).
- Designing up front from stories → **requirements-driven**, then code-driven.
- Only a spec → **schema-driven** (or **bi-directional** for an OpenAPI provider contract).
- Repeating the same shapes everywhere → layer in **cookbook-driven** recipes.
