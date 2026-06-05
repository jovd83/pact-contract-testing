# Advanced Pact features

Capabilities beyond the basic consumer/provider HTTP loop. Most require **spec V4** (and a recent library); generators and request filters work from **V3**. Use these when the basics aren't enough — don't reach for them by default.

## 1. Generators (and provider-state value injection)

A **matcher** says "any value of this shape is acceptable" during verification. A **generator** says "when replaying, *produce* a value here" — used when the value cannot be a fixed example.

When they run:
- **Consumer side**: when the mock generates the example (e.g. a random request id).
- **Provider side**: when the verifier builds the request to replay (e.g. inject a real, server-generated id into the path).

Common generators: random int / decimal / hex / string, `uuid`, `date` / `time` / `datetime` (with format), `regex`, and **`mockServerURL`** (inject the mock server's base URL into a HAL/HATEOAS link).

### `fromProviderState` — the important one

For server-generated values (a DB id, an order number) you cannot hard-code, inject the value the **provider state returns** into the request:

```java
// JVM consumer: the request path uses a value the provider state will supply
.pathFromProviderState("/orders/${id}", "/orders/1001")   // example used by the mock
.given("an order exists", Map.of("id", 1001))
```

```js
// pact-js: fromProviderState(expression, exampleValue)
path: fromProviderState("/orders/${id}", "/orders/1001")
```

On the provider side, the `@State`/state handler **returns** `{ id: <realId> }`; the verifier substitutes `${id}` into the replayed request. This keeps tests data-independent when the consumer must reference an id only the provider knows.

> Rule: use a **matcher** for response fields (shape), a **generator** for values you must produce at replay time, and **`fromProviderState`** when the provider owns the value.

## 2. Verifying secured providers — request filters

Real providers need auth. The consumer should **not** bake real tokens into the pact. Instead, inject auth at verification time with a **request filter** (a hook that mutates each request before it hits the provider):

```js
// pact-js Verifier
requestFilter: (req, res, next) => { req.headers["Authorization"] = `Bearer ${mintTestToken()}`; next(); },
```

```java
// pact-jvm JUnit5
@TestTemplate
void verify(PactVerificationContext ctx, HttpRequest request) {
    request.addHeader("Authorization", "Bearer " + mintTestToken());
    ctx.verifyInteraction();
}
```

Use this for bearer tokens, HMAC signatures, custom headers, or date headers — anything environmental. Keep the **contract** about the message shape; keep **credentials** in the filter.

## 3. V4 interaction types: async vs synchronous messages

V4 distinguishes three interaction kinds — pick the right one:

| Kind | Use for | Pact API |
|---|---|---|
| Synchronous / HTTP | REST / request-response over HTTP | `addInteraction()` (the default) |
| Asynchronous messages | fire-and-forget events (Kafka, SNS/SQS, AMQP) | message pact — test the domain **port** |
| **Synchronous messages** | request/response messaging (gRPC, RPC-over-queue, WebSocket req/resp) | `addSynchronousMessageInteraction()` |

Synchronous messages capture a **request payload and a response payload** (not HTTP). Combined with the **protobuf/gRPC plugin**, this is how you contract-test gRPC.

## 4. The plugin framework

Plugins extend Pact to new **transports** (gRPC, WebSockets) and **content types/protocols** (Protobuf, Avro, CSV, `matt`) without changing the core. They work across all three interaction types above and require **V4**.

```bash
# install the plugin CLI, then a plugin
pact-plugin-cli install protobuf
pact-plugin-cli install avro
pact-plugin-cli list                 # see installed plugins
```

In a test, declare the plugin and use its matching:

```js
// pact-js (conceptual)
const pact = new PactV4({ consumer, provider }).usingPlugin({ plugin: "protobuf", version: "0.5.4" });
```

- Browse the **Pact Plugin Directory** for available plugins before writing your own.
- Provider verification loads the same plugin to decode/match the payload.
- See `schema-driven.md` for Protobuf (gRPC) and Avro (Kafka) specifics.

## 5. `can-i-merge` and verification metadata

- **`can-i-merge`** — a variant of `can-i-deploy` for trunk-based development: "is it safe to merge this branch?" It checks the integration against the main branch rather than an environment:
  ```bash
  pact-broker can-i-merge --pacticipant OrderWebApp --version "$GIT_SHA" \
    --broker-base-url "$PACT_BROKER_BASE_URL" --broker-token "$PACT_BROKER_TOKEN"
  ```
- Attach **build metadata** to verification results with `--build-url` (links the broker result to the CI run) and always set the **provider/consumer version** to the git SHA.

## 6. Webhooks (detail)

Webhooks let the broker drive your CI. Key events:

- `contract_requiring_verification_published` — a consumer published a pact the provider hasn't verified → trigger provider verification.
- `contract_content_changed` — the pact content actually changed → re-verify.
- `provider_verification_published` — verification finished → notify / unblock.

Use broker template parameters in the payload, e.g. `${pactbroker.consumerName}`, `${pactbroker.providerVersionNumber}`, `${pactbroker.githubVerificationStatus}` (to set a GitHub commit status). Configure once per provider.

## 7. PactFlow extras

- **Bi-directional contract testing** — OpenAPI as the provider contract (see `assets/pactflow-bidirectional/`).
- **PactFlow AI** — generates consumer Pact tests / scaffolding from an OpenAPI spec or sample requests. Treat output the same as `scripts/scaffold_from_schema.py`: a **starting point** to review (tighten matchers, set provider states), not a finished test.
- **Secrets** — store broker/provider secrets in PactFlow for use in webhooks instead of committing them.

## 8. Telemetry

Pact tools emit anonymous usage metrics. To disable in CI:

```bash
export PACT_DO_NOT_TRACK=true
```

## When NOT to use these

- No server-generated values → you don't need generators or `fromProviderState`.
- Unauthenticated provider in test → you don't need request filters.
- Plain HTTP/JSON → you don't need plugins or synchronous messages.

Reach for the basic consumer/provider loop first; add these only when a concrete need appears.
