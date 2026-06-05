# Pact Contract Testing Skill

[![version](https://img.shields.io/badge/version-1.3.0-blue)](CHANGELOG.md)
[![status](https://img.shields.io/badge/status-stable-3fb950)](SKILL.md)
[![category](https://img.shields.io/badge/category-testing-0a7ea4)](SKILL.md)
[![validation](https://img.shields.io/badge/validation-GitHub%20Actions-2088ff)](.github/workflows/validate.yml)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/jovd83)

`pact-contract-testing` helps an AI coding agent design and implement **consumer-driven contract tests** with [Pact](https://docs.pact.io/) in any supported language, optionally derived from an existing contract source (OpenAPI, XSD, WSDL, JSON Schema, Protobuf, AsyncAPI, GraphQL, Avro) or from code, requirements, or a recipe cookbook.

It ships as a **skill family**: a language-agnostic core plus one optional skill per language. Install only what you need.

## What This Skill Does

- Scaffolds and writes **consumer** tests (generate a pact) and **provider** verification.
- Derives expectations and **matchers** from a contract source, code, requirements (user stories / Gherkin), or cookbook recipes.
- Sets up **message/event pacts** (Kafka, SQS, SNS, AMQP) using ports-and-adapters.
- Configures **bi-directional contract testing** (PactFlow: OpenAPI as the provider contract).
- Wires the **Pact Broker / PactFlow** lifecycle: publish, `can-i-deploy`, `can-i-merge`, `record-deployment`, webhooks, pending/WIP pacts.
- Covers **advanced features**: generators & `fromProviderState`, request filters for secured providers, V4 synchronous messages, the plugin framework, and PactFlow AI.
- Refuses common anti-patterns (treating Pact as schema/E2E testing, over-specifying with literals, copy-pasting pact files).
- Ships a **fully executed worked example** in [`examples/petstore-sandbox/`](examples/petstore-sandbox/): 4 language clients, a real broker, and 4 iterations with captured output.

## When To Use It

Use it when you need to verify that a consumer and provider agree on the **messages** they exchange — across microservices, public-sector SOAP/XML integrations, event streams, or any client/API pair — without standing up full end-to-end environments.

Use it whenever a consumer and provider could break each other when an API or event shape changes — even if you don't say the word "Pact".

## What This Skill Does Not Do

- **Not** functional, integration, E2E, or load testing, and it does not validate provider **business logic** — only the **shape** of the messages exchanged.
- **Not** general API mocking/stubbing (WireMock/MSW) for local development.
- **Not** request validation against a schema in middleware, nor authoring an OpenAPI spec (it *consumes* contract sources, it doesn't write them).
- **Does not** fabricate a "classic" pact directly from a schema — Pact is code-first; a schema is a design source or a bi-directional provider contract.

## Installation

This repo contains multiple selectable skills (the core + 11 language packs). Using the [`skills` CLI](https://github.com/vercel-labs/skills):

```bash
# Interactive: choose the core skill and only the languages you want
npx skills add jovd83/pact-contract-testing

# Preview what's in the repo first
npx skills add jovd83/pact-contract-testing --list

# Non-interactive: core + Java + Python only
npx skills add jovd83/pact-contract-testing \
  --skill pact-contract-testing --skill pact-java --skill pact-python -y

# Install a single skill by subpath
npx skills add jovd83/pact-contract-testing/languages/go
```

Nothing is mandatory: the core skill and each language pack are independent selections. Each language pack pairs with the core skill for the shared workflow, matchers, schema-driven scaffolding, and broker/CI guidance.

### Available skills

| Skill | Path | Purpose |
|---|---|---|
| `pact-contract-testing` | `/` | Language-agnostic core: workflow, decision tree, matchers, schema-driven, broker/CI |
| `pact-java` | `/languages/java` | Java/JVM — pact-jvm + JUnit 5 |
| `pact-scala` | `/languages/scala` | Scala — pact4s |
| `pact-javascript` | `/languages/javascript` | JS/TS — @pact-foundation/pact |
| `pact-dotnet` | `/languages/dotnet` | .NET — PactNet |
| `pact-go` | `/languages/go` | Go — pact-go/v2 |
| `pact-python` | `/languages/python` | Python — pact-python |
| `pact-ruby` | `/languages/ruby` | Ruby — pact gem |
| `pact-php` | `/languages/php` | PHP — pact-php |
| `pact-rust` | `/languages/rust` | Rust — pact_consumer/pact_verifier |
| `pact-swift` | `/languages/swift` | Swift — PactSwift |
| `pact-cpp` | `/languages/cpp` | C++ — pact-cplusplus |

### Manual installation

Clone and place where your agent looks for local skills:

```bash
git clone https://github.com/jovd83/pact-contract-testing.git
```

## Repository layout

```
SKILL.md                     core skill
references/                  workflow, matchers, derivation modes, schema-driven, broker/CI
scripts/                     scaffold_from_schema.py, publish_pacts.*, can_i_deploy.*, validate_skill.py
assets/                      CI template, test templates, PactFlow bi-directional config
languages/<lang>/SKILL.md    one selectable skill per language
```

## Validation

```bash
python scripts/validate_skill.py .
```

## License

MIT — see [LICENSE](LICENSE).
