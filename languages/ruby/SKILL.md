---
name: pact-ruby
description: Use when writing Pact (Pact.io) consumer-driven contract tests in Ruby with the pact gem — RSpec consumer tests that generate a pact, provider verification with provider_states, and pact_broker-client publishing. Pairs with the pact-contract-testing core skill for the shared workflow, matchers, schema-driven scaffolding, and Pact Broker/CI guidance.
license: MIT
metadata:
  version: "1.0.0"
  maturity: "stable"
  author: "jovd83"
  dispatcher-category: "testing"
  dispatcher-risk: "medium"
  dispatcher-writes-files: "true"
  requires: "pact-contract-testing"
  dispatcher-capabilities: "contract-testing, pact, pact-ruby, ruby, rspec"
  dispatcher-stack-tags: "pact, ruby, rspec, gem"
---

# Pact for Ruby (`pact` gem)

Language pack for the **pact-contract-testing** family. Install the core skill for the shared workflow, matcher rules, schema-driven scaffolding, and broker/CI guidance. Ruby is the original Pact implementation; it uses the native Ruby DSL (spec V3).

## Setup

```ruby
# Gemfile
gem "pact"
gem "pact_broker-client"   # publish + can-i-deploy
```

## Consumer test (generates the pact)

```ruby
Pact.service_consumer("OrderWebApp").has_pact_with("OrderService") do
  mock_service :order_service, port: 1234
end

describe OrderClient, pact: true do
  it "gets order 42" do
    order_service
      .given("an order 42 exists")
      .upon_receiving("a request for order 42")
      .with(method: :get, path: "/orders/42")
      .will_respond_with(
        status: 200,
        headers: { "Content-Type" => "application/json" },
        body: { id: Pact.like(42), status: Pact.term(/OPEN|SHIPPED|CLOSED/, "OPEN") }
      )

    expect(OrderClient.new("http://localhost:1234").fetch(42).id).to eq 42  # REAL client
  end
end
```

## Provider verification (replays the pact)

In `pact_helper.rb`:

```ruby
Pact.service_provider "OrderService" do
  honours_pacts_from_pact_broker do
    pact_broker_base_url ENV["PACT_BROKER_BASE_URL"], { token: ENV["PACT_BROKER_TOKEN"] }
  end
end

Pact.provider_states_for "OrderWebApp" do
  provider_state "an order 42 exists" do
    set_up { Order.create!(id: 42, status: "OPEN") }
  end
end
```

Run `rake pact:verify`. Publish with `pact_broker-client`: `pact-broker publish spec/pacts --consumer-app-version $(git rev-parse --short HEAD) --branch $(git rev-parse --abbrev-ref HEAD)`.

## Notes & gotchas

- Matchers: `Pact.like`, `Pact.term`, `Pact.each_like`; one interaction per test; a `provider_state` per `given(...)`.
- The Ruby gem targets spec V3; for V4 plugins use another language pack.
