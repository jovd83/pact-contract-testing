---
name: pact-java
description: Use when writing Pact (Pact.io) consumer-driven contract tests in Java or any JVM language with pact-jvm and JUnit 5 (au.com.dius.pact) — consumer tests that generate a pact, provider verification with state handlers, message pacts, and Maven/Gradle wiring. Pairs with the pact-contract-testing core skill for the shared workflow, matchers, schema-driven scaffolding, and Pact Broker/CI guidance.
license: MIT
metadata:
  version: "1.0.0"
  maturity: "stable"
  author: "jovd83"
  dispatcher-category: "testing"
  dispatcher-risk: "medium"
  dispatcher-writes-files: "true"
  requires: "pact-contract-testing"
  dispatcher-capabilities: "contract-testing, pact, pact-jvm, java, junit5"
  dispatcher-stack-tags: "pact, jvm, java, junit5, gradle, maven"
---

# Pact for Java / JVM (`pact-jvm`)

Language pack for the **pact-contract-testing** family. Install the core skill for the shared workflow, matcher rules, schema-driven scaffolding, and broker/CI guidance.

## When to use

Writing Pact contract tests in Java/Kotlin/Groovy with JUnit 5 and `au.com.dius.pact`.

## Setup

Gradle:

```groovy
testImplementation 'au.com.dius.pact.consumer:junit5:4.6.+'
testImplementation 'au.com.dius.pact.provider:junit5:4.6.+'
```

Maven: `au.com.dius.pact.consumer:junit5` and `au.com.dius.pact.provider:junit5` (scope `test`).

## Consumer test (generates the pact)

```java
@ExtendWith(PactConsumerTestExt.class)
@PactTestFor(providerName = "OrderService", pactVersion = PactSpecVersion.V4)
class OrderClientPactTest {

  @Pact(consumer = "OrderWebApp")
  V4Pact getOrder(PactDslWithProvider builder) {
    return builder
        .given("an order 42 exists")
        .uponReceiving("a request for order 42")
        .path("/orders/42").method("GET")
        .willRespondWith().status(200)
        .headers(Map.of("Content-Type", "application/json"))
        .body(newJsonBody(o -> {
            o.integerType("id", 42);
            o.stringMatcher("status", "OPEN|SHIPPED|CLOSED", "OPEN");
            o.eachLike("lines", l -> l.numberType("qty", 1));
        }).build())
        .toPact(V4Pact.class);
  }

  @Test
  @PactTestFor(pactMethod = "getOrder")
  void getsOrder(MockServer mock) {
    var order = new OrderClient(mock.getUrl()).fetch(42);  // REAL client code
    assertThat(order.id()).isEqualTo(42);
  }
}
```

Pacts are written to `build/pacts` (Gradle) / `target/pacts` (Maven).

## Provider verification (replays the pact)

```java
@Provider("OrderService")
@PactBroker(url = "${PACT_BROKER_BASE_URL}",
            authentication = @PactBrokerAuth(token = "${PACT_BROKER_TOKEN}"))
class OrderServiceVerificationTest {

  @BeforeEach
  void target(PactVerificationContext ctx) {
    ctx.setTarget(new HttpTestTarget("localhost", port));
  }

  @State("an order 42 exists")
  void order42Exists() { repository.save(new Order(42, "OPEN")); }

  @TestTemplate
  @ExtendWith(PactVerificationInvocationContextProvider.class)
  void verify(PactVerificationContext ctx) { ctx.verifyInteraction(); }
}
```

Provider system properties: `-Dpact.provider.version=$GIT_SHA -Dpact.verifier.publishResults=true -Dpactbroker.consumerversionselectors.rawselectors='[{"mainBranch":true},{"deployedOrReleased":true}]' -Dpact.provider.branch=$BRANCH`. Enable pending/WIP via `-Dpactbroker.enablePending=true -Dpactbroker.providertags=...` and `includeWipPactsSince`.

## Message pacts

Use `MessagePactBuilder` + `@PactTestFor` with `AsynchronousMessage`; on the provider, return the body from a method annotated `@PactVerifyProvider("<description>")`. See the core skill's `references/matchers-and-states.md`.

## Spring Boot note

For provider verification, start the app on a random port (`@SpringBootTest(webEnvironment = RANDOM_PORT)`) and point `HttpTestTarget` at it; set provider state in `@State` handlers using your repositories/`@MockBean`s.

## Notes & gotchas

- Use **V4** for plugins (gRPC via `pact-protobuf-plugin`, Avro) and mixed pact types.
- Matchers, not literals; one interaction per test (core skill rules).
- A `@State` handler is required for every `given(...)` consumers use.
