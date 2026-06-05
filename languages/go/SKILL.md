---
name: pact-go
description: Use when writing Pact (Pact.io) consumer-driven contract tests in Go with pact-go/v2 — consumer tests that generate a pact, provider verification with state handlers, message pacts, and go test/go mod wiring. Pairs with the pact-contract-testing core skill for the shared workflow, matchers, schema-driven scaffolding, and Pact Broker/CI guidance.
license: MIT
metadata:
  version: "1.0.0"
  maturity: "stable"
  author: "jovd83"
  dispatcher-category: "testing"
  dispatcher-risk: "medium"
  dispatcher-writes-files: "true"
  requires: "pact-contract-testing"
  dispatcher-capabilities: "contract-testing, pact, pact-go, golang"
  dispatcher-stack-tags: "pact, go, golang, gotest"
---

# Pact for Go (`pact-go/v2`)

Language pack for the **pact-contract-testing** family. Install the core skill for the shared workflow, matcher rules, schema-driven scaffolding, and broker/CI guidance.

## When to use

Writing Pact contract tests in Go with the standard `testing` package and `pact-go/v2`.

## Setup

```bash
go get github.com/pact-foundation/pact-go/v2@v2
# install the FFI library once:
go run github.com/pact-foundation/pact-go/v2 install
```

## Consumer test (generates the pact)

```go
import (
    "github.com/pact-foundation/pact-go/v2/consumer"
    "github.com/pact-foundation/pact-go/v2/matchers"
)

func TestGetOrder(t *testing.T) {
    mockProvider, err := consumer.NewV4Pact(consumer.MockHTTPProviderConfig{
        Consumer: "OrderWebApp", Provider: "OrderService",
    })
    assert.NoError(t, err)

    err = mockProvider.
        AddInteraction().
        Given("an order 42 exists").
        UponReceiving("a request for order 42").
        WithRequest("GET", "/orders/42").
        WillRespondWith(200, func(b *consumer.V4ResponseBuilder) {
            b.Header("Content-Type", matchers.S("application/json"))
            b.JSONBody(matchers.Map{
                "id":     matchers.Integer(42),
                "status": matchers.Regex("OPEN", "OPEN|SHIPPED|CLOSED"),
                "lines":  matchers.EachLike(matchers.Map{"qty": matchers.Integer(1)}, 1),
            })
        }).
        ExecuteTest(t, func(c consumer.MockServerConfig) error {
            _, err := NewOrderClient(c.URL()).Fetch(42) // REAL client
            return err
        })
    assert.NoError(t, err)
}
```

## Provider verification (replays the pact)

```go
import "github.com/pact-foundation/pact-go/v2/provider"

func TestProvider(t *testing.T) {
    verifier := provider.NewVerifier()
    err := verifier.VerifyProvider(t, provider.VerifyRequest{
        ProviderBaseURL:            "http://localhost:8080",
        BrokerURL:                  os.Getenv("PACT_BROKER_BASE_URL"),
        BrokerToken:                os.Getenv("PACT_BROKER_TOKEN"),
        ProviderVersion:            os.Getenv("GIT_SHA"),
        ProviderBranch:             os.Getenv("GIT_BRANCH"),
        PublishVerificationResults: true,
        EnablePending:              true,
        IncludeWIPPactsSince:       &wipSince,
        ConsumerVersionSelectors:   []provider.Selector{&provider.ConsumerVersionSelector{MainBranch: true}},
        StateHandlers: provider.StateHandlers{
            "an order 42 exists": func(setup bool, s provider.ProviderStateV3) (provider.ProviderStateV3Response, error) {
                repo.Save(Order{ID: 42, Status: "OPEN"})
                return nil, nil
            },
        },
    })
    assert.NoError(t, err)
}
```

## Notes & gotchas

- `NewV4Pact` is the current API; run the one-time `install` step in CI too.
- Matchers via the `matchers` package; one interaction per test; a state handler per `Given(...)`.
- Message pacts: `consumer.NewMessagePactV4` + provider message verification.
