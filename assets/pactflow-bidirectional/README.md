# Bi-directional contract testing (PactFlow)

Use when you only have the **provider's OpenAPI spec** and cannot write provider verification code. PactFlow treats the OpenAPI document as the **provider contract** and cross-verifies each consumer pact against it — no provider test code, no replay.

> Requires **PactFlow** (the hosted/enterprise broker). The open-source Pact Broker does **not** support bi-directional contract testing.

## Flow

```
CONSUMER: normal consumer test → pact → publish (as today)
PROVIDER: publish the OpenAPI spec as a "provider contract" + a self-verification result
PACTFLOW: cross-verifies consumer pact ⊆ OpenAPI spec → can-i-deploy reflects the result
```

## Publish the provider contract (OpenAPI)

```bash
pactflow publish-provider-contract openapi.yaml \
  --provider OrderService \
  --provider-app-version "$(git rev-parse --short HEAD)" \
  --branch "$(git rev-parse --abbrev-ref HEAD)" \
  --content-type application/yaml \
  --verification-exit-code 0 \
  --verifier "your-openapi-linter" \
  --verification-results lint-results.txt \
  --verification-results-content-type text/plain
```

(`pactflow` is provided by the pact CLI tools / `pact-broker-client` when targeting PactFlow.)

## Then, as usual

- Consumers publish pacts (`scripts/publish_pacts.sh`).
- PactFlow performs the cross-verification automatically.
- Both sides gate with `can-i-deploy` (`scripts/can_i_deploy.sh`).

## When NOT to use it

- You own the provider and can write verification → prefer **classic** consumer-driven verification (richer, supports provider states, messages, plugins).
- Non-HTTP/JSON contracts (SOAP/XSD, gRPC, Avro) → bi-directional does not apply; use design-source scaffolding + matchers/plugins (see `references/schema-driven.md`).
