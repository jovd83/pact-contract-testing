---
name: pact-scala
description: Use when writing Pact (Pact.io) consumer-driven contract tests in Scala with pact4s (ScalaTest, munit, or weaver) backed by pact-jvm — consumer tests that generate a pact, provider verification with state handlers, and sbt wiring. Pairs with the pact-contract-testing core skill for the shared workflow, matchers, schema-driven scaffolding, and Pact Broker/CI guidance.
license: MIT
metadata:
  version: "1.0.0"
  maturity: "stable"
  author: "jovd83"
  dispatcher-category: "testing"
  dispatcher-risk: "medium"
  dispatcher-writes-files: "true"
  requires: "pact-contract-testing"
  dispatcher-capabilities: "contract-testing, pact, pact4s, scala, scalatest"
  dispatcher-stack-tags: "pact, scala, sbt, scalatest"
---

# Pact for Scala (`pact4s` + pact-jvm)

Language pack for the **pact-contract-testing** family. Install the core skill for the shared workflow, matcher rules, schema-driven scaffolding, and broker/CI guidance. `pact4s` provides idiomatic Scala test integrations on top of `pact-jvm`.

## Setup

```scala
// build.sbt — pick the module for your test framework
libraryDependencies += "com.github.jbwheatley" %% "pact4s-scalatest" % "0.x" % Test
// or: pact4s-munit-cats-effect, pact4s-weaver
```

## Consumer test (generates the pact)

```scala
import pact4s.scalatest.RequestResponsePactForger
import au.com.dius.pact.consumer.dsl._

class OrderClientPactTest extends AnyFlatSpec with RequestResponsePactForger {
  override val pact: RequestResponsePact =
    ConsumerPactBuilder
      .consumer("OrderWebApp")
      .hasPactWith("OrderService")
      .given("an order 42 exists")
      .uponReceiving("a request for order 42")
      .path("/orders/42").method("GET")
      .willRespondWith().status(200)
      .body(newJsonBody(o => {
        o.integerType("id", 42)
        o.stringMatcher("status", "OPEN|SHIPPED|CLOSED", "OPEN")
      }).build())
      .toPact()

  it should "get order 42" in {
    val order = new OrderClient(mockServer.getUrl).fetch(42) // REAL client
    assert(order.id == 42)
  }
}
```

## Provider verification (replays the pact)

Use `pact4s`'s `PactVerifier` mix-in: configure the broker source (`ConsumerVersionSelectors`), provider base URL, provider version (git SHA), pending/WIP, and a `ProviderState` partial function that seeds data per `given(...)`. Underlying engine is pact-jvm.

## Notes & gotchas

- Matchers come from the pact-jvm DSL (`newJsonBody`, type/regex matchers).
- One interaction per test; a provider-state handler per `given(...)`.
- Use V4 for plugins; see the core skill's `references/schema-driven.md`.
