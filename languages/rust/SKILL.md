---
name: pact-rust
description: Use when writing Pact (Pact.io) consumer-driven contract tests in Rust with the pact_consumer and pact_verifier crates — consumer tests that generate a pact, provider verification with state handlers, and cargo wiring. Pairs with the pact-contract-testing core skill for the shared workflow, matchers, schema-driven scaffolding, and Pact Broker/CI guidance.
license: MIT
metadata:
  version: "1.0.0"
  maturity: "stable"
  author: "jovd83"
  dispatcher-category: "testing"
  dispatcher-risk: "medium"
  dispatcher-writes-files: "true"
  requires: "pact-contract-testing"
  dispatcher-capabilities: "contract-testing, pact, pact-rust, rust, cargo"
  dispatcher-stack-tags: "pact, rust, cargo"
---

# Pact for Rust (`pact_consumer` / `pact_verifier`)

Language pack for the **pact-contract-testing** family. Install the core skill for the shared workflow, matcher rules, schema-driven scaffolding, and broker/CI guidance. The Rust crates **are** the FFI core that the other languages wrap, so they track the spec most closely (V4).

## Setup

```toml
# Cargo.toml
[dev-dependencies]
pact_consumer = "1"
expectest = "0.12"
```

## Consumer test (generates the pact)

```rust
use pact_consumer::prelude::*;
use pact_consumer::*;

#[tokio::test]
async fn get_order_42() {
    let pact = PactBuilder::new("OrderWebApp", "OrderService")
        .interaction("a request for order 42", "", |mut i| {
            i.given("an order 42 exists");
            i.request.method("GET").path("/orders/42");
            i.response
                .status(200)
                .header("Content-Type", "application/json")
                .json_body(json_pattern!({
                    "id": like!(42),
                    "status": term!("OPEN|SHIPPED|CLOSED", "OPEN"),
                }));
            i
        })
        .start_mock_server(None, None);

    let order = OrderClient::new(pact.url()).fetch(42).await.unwrap(); // REAL client
    expect!(order.id).to(be_equal_to(42));
}
```

The pact is written when the mock server is dropped and expectations were met.

## Provider verification (replays the pact)

Use the `pact_verifier` crate or the `pact_verifier_cli`:

```bash
pact_verifier_cli \
  --hostname localhost --port 8080 \
  --broker-url "$PACT_BROKER_BASE_URL" --token "$PACT_BROKER_TOKEN" \
  --provider-name OrderService --provider-version "$(git rev-parse --short HEAD)" \
  --publish --enable-pending \
  --state-change-url http://localhost:8080/provider-states
```

## Notes & gotchas

- Matchers via the `like!`, `term!`, `each_like!` macros / `json_pattern!`.
- One interaction per test; a state setup per `given(...)`.
- Plugins (Protobuf/Avro) are supported directly via the plugin framework (V4).
