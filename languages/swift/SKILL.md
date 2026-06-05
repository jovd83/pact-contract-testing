---
name: pact-swift
description: Use when writing Pact (Pact.io) consumer-driven contract tests in Swift with PactSwift — XCTest consumer tests that generate a pact for iOS/macOS clients, with matchers and SwiftPM wiring. Pairs with the pact-contract-testing core skill for the shared workflow, matchers, schema-driven scaffolding, and Pact Broker/CI guidance.
license: MIT
metadata:
  version: "1.0.0"
  maturity: "stable"
  author: "jovd83"
  dispatcher-category: "testing"
  dispatcher-risk: "medium"
  dispatcher-writes-files: "true"
  requires: "pact-contract-testing"
  dispatcher-capabilities: "contract-testing, pact, pact-swift, swift, xctest"
  dispatcher-stack-tags: "pact, swift, ios, macos, xctest"
---

# Pact for Swift (`PactSwift`)

Language pack for the **pact-contract-testing** family. Install the core skill for the shared workflow, matcher rules, schema-driven scaffolding, and broker/CI guidance. PactSwift is most often used to contract-test iOS/macOS app clients against their backend.

## Setup

Add `PactSwift` via Swift Package Manager to the **test** target only.

## Consumer test (generates the pact)

```swift
import PactSwift
import XCTest

final class OrderClientPactTests: XCTestCase {
    var builder: PactBuilder!

    override func setUp() {
        let pact = try! Pact(consumer: "OrderWebApp", provider: "OrderService")
        builder = PactBuilder(pact: pact, config: PactBuilder.Config())
    }

    func testGetOrder42() async throws {
        try builder
            .uponReceiving("a request for order 42")
            .given("an order 42 exists")
            .withRequest(method: .GET, path: "/orders/42")
            .willRespond(with: 200) { response in
                try response.jsonBody(.like([
                    "id": .integer(42),
                    "status": .regex("OPEN|SHIPPED|CLOSED", example: "OPEN"),
                ]))
            }
            .verify { ctx in
                let order = try await OrderClient(baseURL: ctx.mockServerURL).fetch(42) // REAL client
                XCTAssertEqual(order.id, 42)
            }
    }
}
```

## Provider verification

PactSwift focuses on the **consumer** side. Verify the generated pact against the provider with the **provider's own language pack** (e.g. `pact-java`, `pact-go`) or the standalone `pact_verifier_cli`, pulling the pact from the broker.

## Notes & gotchas

- Matchers via the PactSwift matcher API (`.like`, `.integer`, `.regex`, `.eachLike`).
- One interaction per test; a `given(...)` per precondition (handled by the provider's verifier).
- Publish generated pacts to the broker from CI with `pact-broker publish`.
