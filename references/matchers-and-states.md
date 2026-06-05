# Matchers, provider states & message pacts

## Why matchers

A pact is **contract by example**: it records one concrete request/response, but verification should pass for any value of the **right shape**. Use matchers so the provider can return real data (different ids, timestamps) without breaking the contract. Literal values are only correct when the value is genuinely fixed (an enum constant, a required header name).

> Rule of thumb: **be strict in what you send (request), liberal in what you accept (response)**. Over-specified responses are the #1 cause of false provider failures.

## Matcher catalogue (concepts; names vary per language)

| Intent | Concept | JVM example | JS (MatchersV3) | Notes |
|---|---|---|---|---|
| Match by type | type matcher | `integerType("id", 42)` | `integer(42)` | value is the example only |
| Match by regex | regex/term | `stringMatcher("status", "A|B", "A")` | `regex("A|B","A")` | derive from schema `pattern`/`format` |
| Array of like items | `eachLike` | `eachLike("lines", l -> ...)` | `eachLike({...})` | set `min`/`max` where relevant |
| Object present, any shape | `like` | `object("meta", o -> ...)` | `like({...})` | |
| Date/time | datetime matcher | `datetime("ts","yyyy-MM-dd'T'HH:mm:ssZ")` | `datetime(format, example)` | avoid asserting exact instants |
| Number / decimal | number/decimal | `numberType`, `decimalType` | `decimal`, `integer` | |
| UUID / email etc. | regex preset | `uuid("id")` | `uuid()` | |
| Value from a set | (V4) values matcher | builder-specific | builder-specific | |
| XML element/attr | XML matcher | `PactXmlBuilder` | `XML` helpers | for XSD/SOAP — see schema-driven.md |

**Request matching**: keep requests as **specific** as the consumer actually sends (exact path, method, required query/headers). Loosen only fields that legitimately vary.

## Spec versions & matchers

- **V2**: regex + type matching, single body matcher tree. Widest broker compatibility.
- **V3**: adds typed provider states with **parameters**, `eachLike` min/max, generators, message pacts.
- **V4**: adds **plugins** (Protobuf/gRPC, Avro, etc.), combined HTTP + async message pacts in one file, richer matchers. Prefer V4 for new work.

## Provider states

A provider state is a **named precondition** the provider sets up before replaying an interaction.

- Consumer: `.given("an order 42 exists")` — and with V3+, parameters: `.given("an order exists", Map.of("id", 42))`.
- Provider: register a **state handler** per name that seeds the data (DB insert, stub, in-memory repo). It runs **before** the matching interaction and should be torn down after.
- States must be **idempotent** and isolated. Never rely on global ordering.
- A missing handler → verification error "state not found". Every `given(...)` used by any consumer needs a handler.

```java
@State("an order exists")
void orderExists(Map<String, Object> params) {        // V3 parameters
    repository.save(new Order((int) params.get("id"), "OPEN"));
}
```

## Message (event) pacts — Kafka, SQS, SNS, AMQP

Pact tests the **message payload**, not the transport. Use **ports-and-adapters (hexagonal)**:

- **Adapter** = protocol code (Kafka consumer, Lambda handler). Not under Pact test.
- **Port** = the domain function that takes the decoded payload. **This is what Pact tests.**

**Consumer (message expectation)** — assert your handler can process a message of the expected shape:

```java
// pact-jvm message DSL (V4)
@Pact(consumer = "InventoryService")
V4Pact orderPlaced(MessagePactBuilder builder) {
  return builder
    .expectsToReceive("an order placed event")
    .withContent(newJsonBody(o -> {
        o.integerType("orderId", 42);
        o.stringType("sku");
        o.integerType("qty", 1);
    }).build())
    .toPact(V4Pact.class);
}

@Test @PactTestFor(pactMethod = "orderPlaced")
void handles(V4Interaction.AsynchronousMessage msg) {
    orderPlacedHandler.handle(msg.getContents().getContents()); // real port
}
```

**Provider (message producer)**: register a **message provider** that, given the state, produces the message body; the verifier checks it matches the consumer's expectation. In JS use `messageProviders`, in pact-jvm use `@PactVerifyProvider("an order placed event")` returning the message body.

- For binary encodings (Avro, Protobuf) use the matching **plugin** and V4 — see `schema-driven.md`.
- AsyncAPI describes these channels and can seed the expected payload shape (design source).

## Checklist

- [ ] One interaction per test.
- [ ] Matchers used for every varying field; literals only for true constants.
- [ ] Request matched as specifically as the consumer sends.
- [ ] A provider-state handler exists for every `given(...)`.
- [ ] Message pacts test the **port**, not the transport adapter.
- [ ] V4 selected when using plugins or mixed pact types.
