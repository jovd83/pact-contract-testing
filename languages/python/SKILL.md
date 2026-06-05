---
name: pact-python
description: Use when writing Pact (Pact.io) consumer-driven contract tests in Python with pact-python (the v3 FFI-backed API) — consumer tests that generate a pact, provider verification with state handlers, message pacts, and pytest/pip wiring. Pairs with the pact-contract-testing core skill for the shared workflow, matchers, schema-driven scaffolding, and Pact Broker/CI guidance.
license: MIT
metadata:
  version: "1.0.0"
  maturity: "stable"
  author: "jovd83"
  dispatcher-category: "testing"
  dispatcher-risk: "medium"
  dispatcher-writes-files: "true"
  requires: "pact-contract-testing"
  dispatcher-capabilities: "contract-testing, pact, pact-python, python, pytest"
  dispatcher-stack-tags: "pact, python, pytest, pip"
---

# Pact for Python (`pact-python`)

Language pack for the **pact-contract-testing** family. Install the core skill for the shared workflow, matcher rules, schema-driven scaffolding, and broker/CI guidance.

## When to use

Writing Pact contract tests in Python with pytest and `pact-python`. Prefer the **v3** (`pact.v3`) FFI-backed API for new work; the legacy `pact` API still exists.

## Setup

```bash
pip install pact-python
```

## Consumer test (generates the pact)

```python
from pact.v3 import Pact, match

def test_get_order():
    pact = Pact("OrderWebApp", "OrderService")
    (
        pact.upon_receiving("a request for order 42")
        .given("an order 42 exists")
        .with_request("GET", "/orders/42")
        .will_respond_with(200)
        .with_header("Content-Type", "application/json")
        .with_body({
            "id": match.int(42),
            "status": match.regex("OPEN", regex="OPEN|SHIPPED|CLOSED"),
            "lines": match.each_like({"qty": match.int(1)}),
        })
    )

    with pact.serve() as mock:
        order = OrderClient(mock.url).fetch(42)   # REAL client
        assert order.id == 42

    pact.write_file("./pacts")
```

## Provider verification (replays the pact)

```python
from pact.v3 import Verifier
import os

def test_provider():
    (
        Verifier("OrderService")
        .add_transport(url="http://localhost:8080")
        .broker_source(os.environ["PACT_BROKER_BASE_URL"], token=os.environ["PACT_BROKER_TOKEN"])
        .set_publish_options(version=os.environ["GIT_SHA"], branch=os.environ.get("GIT_BRANCH"))
        .filter_consumers()  # use selectors / pending+WIP as supported
        .state_handler(STATE_HANDLERS, body=True)
        .verify()
    )
```

Register a handler for each `given(...)` (e.g. an HTTP state-setup endpoint or a callable map) that seeds the data.

## Notes & gotchas

- API differs between `pact` (legacy) and `pact.v3` — use **v3** for matchers/plugins.
- Matchers via `pact.v3.match`; one interaction per test; a state handler per `given(...)`.
- Message pacts and plugins (Protobuf/Avro) are available through the v3 API + `pact-plugin-cli`.
