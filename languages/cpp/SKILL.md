---
name: pact-cpp
description: Use when writing Pact (Pact.io) consumer-driven contract tests in C++ with pact-cplusplus — consumer tests that generate a pact against a mock server and provider verification via the FFI/CLI, with CMake wiring. Pairs with the pact-contract-testing core skill for the shared workflow, matchers, schema-driven scaffolding, and Pact Broker/CI guidance.
license: MIT
metadata:
  version: "1.0.0"
  maturity: "stable"
  author: "jovd83"
  dispatcher-category: "testing"
  dispatcher-risk: "medium"
  dispatcher-writes-files: "true"
  requires: "pact-contract-testing"
  dispatcher-capabilities: "contract-testing, pact, pact-cplusplus, cpp"
  dispatcher-stack-tags: "pact, cpp, cmake, gtest"
---

# Pact for C++ (`pact-cplusplus`)

Language pack for the **pact-contract-testing** family. Install the core skill for the shared workflow, matcher rules, schema-driven scaffolding, and broker/CI guidance. `pact-cplusplus` provides a C++ wrapper over the Rust FFI core; tests are typically driven with GoogleTest.

## Setup

- Build/install the `pact_ffi` shared library (from pact-reference releases).
- Add the `consumer` library headers from `pact-cplusplus` to your CMake test target and link against `pact_ffi`.

## Consumer test (generates the pact)

```cpp
#include "consumer.h"     // pact-cplusplus
#include <gtest/gtest.h>

using namespace pact_consumer;
using namespace pact_consumer::matchers;

TEST(OrderClient, GetsOrder42) {
  auto provider = Pact("OrderWebApp", "OrderService");
  provider
    .given("an order 42 exists")
    .uponReceiving("a request for order 42")
    .withRequest("GET", "/orders/42")
    .willRespondWith(200)
    .withResponseJsonBody(JsonObject({
        { "id", Integer(42) },
        { "status", Matching("OPEN|SHIPPED|CLOSED", "OPEN") },
    }));

  auto result = provider.run_test([](auto mock_server) {
    auto order = OrderClient(mock_server->get_url()).fetch(42); // REAL client
    return order.id == 42;
  });
  EXPECT_TRUE(result.is_ok());
}
```

## Provider verification

Verify the generated pact with the standalone `pact_verifier_cli` (or the verifier FFI), pulling pacts from the broker, passing the provider version (git SHA), and a `--state-change-url` that seeds data per `given(...)`.

## Notes & gotchas

- Matchers via the matcher helpers (`Integer`, `Matching`/regex, `EachLike`).
- One interaction per test; a state setup per `given(...)`.
- Keep the `pact_ffi` library version aligned with the `pact-cplusplus` headers.
