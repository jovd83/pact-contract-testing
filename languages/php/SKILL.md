---
name: pact-php
description: Use when writing Pact (Pact.io) consumer-driven contract tests in PHP with pact-php — PHPUnit consumer tests that generate a pact, provider verification with state handlers, and composer wiring. Pairs with the pact-contract-testing core skill for the shared workflow, matchers, schema-driven scaffolding, and Pact Broker/CI guidance.
license: MIT
metadata:
  version: "1.0.0"
  maturity: "stable"
  author: "jovd83"
  dispatcher-category: "testing"
  dispatcher-risk: "medium"
  dispatcher-writes-files: "true"
  requires: "pact-contract-testing"
  dispatcher-capabilities: "contract-testing, pact, pact-php, php, phpunit"
  dispatcher-stack-tags: "pact, php, phpunit, composer"
---

# Pact for PHP (`pact-php`)

Language pack for the **pact-contract-testing** family. Install the core skill for the shared workflow, matcher rules, schema-driven scaffolding, and broker/CI guidance. `pact-php` wraps the Rust FFI core (spec V3/V4).

## Setup

```bash
composer require --dev pact-foundation/pact-php
```

## Consumer test (generates the pact)

```php
use PhpPact\Consumer\InteractionBuilder;
use PhpPact\Consumer\Matcher\Matcher;
use PhpPact\Consumer\Model\ConsumerRequest;
use PhpPact\Consumer\Model\ProviderResponse;
use PhpPact\Standalone\MockService\MockServerConfig;

$matcher = new Matcher();

$request = (new ConsumerRequest())->setMethod('GET')->setPath('/orders/42');
$response = (new ProviderResponse())
    ->setStatus(200)
    ->addHeader('Content-Type', 'application/json')
    ->setBody([
        'id'     => $matcher->like(42),
        'status' => $matcher->regex('OPEN', 'OPEN|SHIPPED|CLOSED'),
    ]);

$builder = new InteractionBuilder($config);   // MockServerConfig with consumer/provider
$builder->given('an order 42 exists')
        ->uponReceiving('a request for order 42')
        ->with($request)
        ->willRespondWith($response);

$order = (new OrderClient($config->getBaseUri()))->fetch(42); // REAL client
$this->assertSame(42, $order->id);
$this->assertTrue($builder->verify());
```

## Provider verification (replays the pact)

Use the `Verifier` with broker source, provider base URL, provider version (git SHA), and a provider-state setup endpoint that seeds data per `given(...)`. Enable pending/WIP via verifier options.

## Notes & gotchas

- Matchers via the `Matcher` class (`like`, `regex`, `eachLike`); one interaction per test; a state per `given(...)`.
- Requires the standalone mock-server binary (installed by the package).
