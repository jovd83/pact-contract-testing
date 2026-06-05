---
name: pact-dotnet
description: Use when writing Pact (Pact.io) consumer-driven contract tests in .NET (C#) with PactNet (Pact.V4) — consumer tests that generate a pact, provider verification with state handlers, message pacts, and xUnit/NUnit/NuGet wiring. Pairs with the pact-contract-testing core skill for the shared workflow, matchers, schema-driven scaffolding, and Pact Broker/CI guidance.
license: MIT
metadata:
  version: "1.0.0"
  maturity: "stable"
  author: "jovd83"
  dispatcher-category: "testing"
  dispatcher-risk: "medium"
  dispatcher-writes-files: "true"
  requires: "pact-contract-testing"
  dispatcher-capabilities: "contract-testing, pact, pactnet, dotnet, csharp"
  dispatcher-stack-tags: "pact, dotnet, csharp, xunit, nuget"
---

# Pact for .NET (`PactNet`)

Language pack for the **pact-contract-testing** family. Install the core skill for the shared workflow, matcher rules, schema-driven scaffolding, and broker/CI guidance.

## When to use

Writing Pact contract tests in C# with xUnit/NUnit and `PactNet`.

## Setup

```bash
dotnet add package PactNet
```

## Consumer test (generates the pact)

```csharp
var pact = Pact.V4("OrderWebApp", "OrderService").WithHttpInteractions();

pact.UponReceiving("a request for order 42")
    .Given("an order 42 exists")
    .WithRequest(HttpMethod.Get, "/orders/42")
    .WillRespond()
    .WithStatus(HttpStatusCode.OK)
    .WithHeader("Content-Type", "application/json")
    .WithJsonBody(new
    {
        id = Match.Integer(42),
        status = Match.Regex("OPEN", "OPEN|SHIPPED|CLOSED"),
        lines = Match.MinType(new { qty = Match.Integer(1) }, 1),
    });

await pact.VerifyAsync(async ctx =>
{
    var order = await new OrderClient(ctx.MockServerUri).FetchAsync(42); // REAL client
    Assert.Equal(42, order.Id);
});
```

## Provider verification (replays the pact)

```csharp
using var verifier = new PactVerifier("OrderService");
verifier
    .WithHttpEndpoint(new Uri("http://localhost:8080"))
    .WithPactBrokerSource(new Uri(broker), o => o
        .ConsumerVersionSelectors(new ConsumerVersionSelector { MainBranch = true },
                                  new ConsumerVersionSelector { DeployedOrReleased = true })
        .Token(token)
        .EnablePending()
        .IncludeWipPactsSince(new DateTime(2024, 1, 1))
        .PublishResults(gitSha, c => c.ProviderBranch(branch)))
    .WithProviderStateUrl(new Uri("http://localhost:8080/provider-states"))
    .Verify();
```

Expose a `/provider-states` endpoint (or use the in-process state-handler hooks) that seeds data per `Given(...)`.

## Message pacts

Use `Pact.V4(...).WithMessageInteractions()` on the consumer and `PactVerifier` message scenarios on the provider. See core `references/matchers-and-states.md`.

## Notes & gotchas

- Use **`Pact.V4`** for new tests (plugins, message + HTTP).
- Matchers via `Match.*`; one interaction per test; a state per `Given(...)`.
- Set `providerVersion`/branch from the git SHA in CI.
