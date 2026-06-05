# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-06-05

Iteration 2 of the skill-creator eval loop (edit-delta vs the v1.2.0 snapshot, 9 evals × 2 runs): 100% pass rate maintained in both versions with **~3% fewer tokens overall and ~5% fewer on conceptual questions** (anti-pattern-refusal eval −10.4%), confirming the changes cut cost with no correctness regression.

### Changed
- `SKILL.md`: front-loaded a **"Use the bundled tooling first"** section (reach for the shipped scripts/assets instead of reinventing) plus a **"Don't over-read"** rule (answer conceptual questions from the page; don't load `references/` for a one-line answer) — the measured token reduction comes from here.
- `SKILL.md`: added **Core mental model #5 — "Test the real client, not a throwaway request"** (drive the actual client class against the mock server, never an inline HTTP call written just for the test).
- `SKILL.md`: added a dedicated **PactFlow** section consolidating bi-directional contract testing, PactFlow AI, encrypted webhook secrets, governance (RBAC/SSO/audit), and the managed-vs-OSS decision — bringing PactFlow to parity with Pact.
- `SKILL.md`: sharpened the **description** for triggering — promotes PactFlow, fires even when the user doesn't say "Pact", names message transports + `can-i-merge`, and adds a "Not for" boundary (API mocking, schema validation, OpenAPI authoring, E2E/integration/load, unit tests).

### Added
- `evals/evals.json`: rewrote assertions to be **discriminating** (bundled-tooling reference vs reinvention, real-client-under-test, the final report contract, the `can-i-deploy` hollow-gate nuance) and added **eval-9** (PactFlow trunk-based `can-i-merge`).

## [1.2.0] - 2026-06-03

### Added
- Broker provisioning for when no broker exists yet: `scripts/start_broker.sh` / `.ps1` boot a self-hosted Docker Pact Broker (`assets/broker/docker-compose.yml`: postgres + `pactfoundation/pact-broker`, persistent volume, read-only credentials, healthcheck), wait for the heartbeat, and print the env vars to export.
- `assets/broker/README.md`: three-way broker decision (existing broker / PactFlow managed / self-host Docker), defaults table, and a "don't provision a second broker if you already have one" rule.

### Changed
- `SKILL.md`: "Pact Broker & CI/CD" now states the broker is a separate application you must supply, adds the existing/PactFlow/self-host decision table, and references the new script; required-inputs broker line and helper-scripts table updated. Version bumped to 1.2.0.
- `references/broker-and-cicd.md`: new "Provisioning a broker (if you don't have one)" section.

## [1.1.0] - 2026-06-03

### Added
- `references/advanced-features.md`: generators and provider-state value injection (`fromProviderState`), request filters for verifying secured providers, V4 synchronous-message interactions, the Pact plugin framework (`pact-plugin-cli`), `can-i-merge`, webhook events/templates, PactFlow AI, and telemetry (`PACT_DO_NOT_TRACK`).
- `examples/petstore-sandbox/`: a fully executed worked example — 4 consumer clients (Java, JavaScript, Python, Go), a controlled Node/Express provider, a Dockerized Pact Broker, and 4 iterations (mock+publish+stub, provider verification, a misinterpreting consumer caught by pending pacts, and a breaking change blocked by `can-i-deploy`) with verbatim captured output in `docs/ITERATIONS.md` and `docs/TEST-CATALOG.md`.
- `can-i-merge` + `--build-url` guidance in `references/broker-and-cicd.md`.

### Changed
- Core `SKILL.md` gains an "Advanced features" section and a pointer to the sandbox example; version bumped to 1.1.0.

## [1.0.0] - 2026-06-03

### Added
- Core `pact-contract-testing` skill: scope, core mental model, required inputs, decision tree, HTTP consumer-driven workflow, Java worked example, anti-patterns, troubleshooting, and final response contract.
- Eleven selectable language packs under `languages/`: `pact-java`, `pact-scala`, `pact-javascript`, `pact-dotnet`, `pact-go`, `pact-python`, `pact-ruby`, `pact-php`, `pact-rust`, `pact-swift`, `pact-cpp`.
- References: `languages.md` (pack index + cross-language rules), `matchers-and-states.md`, `derivation-modes.md` (code/schema/requirements/cookbook-driven), `schema-driven.md` (OpenAPI, Swagger, JSON Schema, XSD, WSDL, Protobuf/gRPC, Avro, AsyncAPI, GraphQL, Pact files), `broker-and-cicd.md`.
- Scripts: `scaffold_from_schema.py` (multi-contract-type scaffolder), `publish_pacts.sh`/`.ps1`, `can_i_deploy.sh`/`.ps1`, `validate_skill.py` (family-aware).
- Assets: GitHub Actions CI template, test templates, PactFlow bi-directional config.
- Repository scaffolding: README with selective-install guidance, MIT license, Keep-a-Changelog, `agents/openai.yaml`, `evals/evals.json`, validation workflow.
