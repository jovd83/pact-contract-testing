# Schema-driven contract tests — all contract sources

A Pact contract test can be **derived from** an existing contract source, but how depends on the source. Pact itself is **code-first**: a schema never produces a "classic" pact by itself. There are three mechanisms a source can feed into:

1. **Design source** — read the schema to scaffold the consumer DSL and derive **matchers** (types → type matchers, `pattern`/`format` → regex, required → presence, enums → regex of the allowed set). The consumer test still generates the pact. Use `scripts/scaffold_from_schema.py`.
2. **Bi-directional contract testing (PactFlow)** — the **provider contract _is_ the spec** (OpenAPI). PactFlow verifies the consumer pact against the uploaded spec; no provider test code. Best when you only have the provider's OpenAPI.
3. **Plugin** — for non-JSON wire formats (Protobuf/gRPC, Avro), a V4 **Pact plugin** encodes/matches the payload natively.

## Source → mechanism map

| Contract source | Domain | Mechanism | How it feeds Pact |
|---|---|---|---|
| **OpenAPI / Swagger** | REST/JSON over HTTP | Design source **or** bi-directional | Scaffold consumer test + matchers from schema; **or** publish the spec as the provider contract for bi-directional. |
| **JSON Schema** | Any JSON payload / event body | Design source | Map JSON Schema types/`pattern`/`required`/`enum` to matchers for HTTP or message pacts. |
| **XSD** | XML — SOAP, legacy, public sector | Design source + **XML matchers** | Scaffold an HTTP interaction with an XML body using `PactXmlBuilder`/XML matchers derived from element/attribute types. |
| **WSDL** | SOAP service description | Design source + XML matchers | Extract operations, endpoint, SOAPAction header, and the message types (often referencing XSD); scaffold one interaction per operation. |
| **Protobuf / gRPC** | Binary RPC, microservices | **Plugin** (`pact-protobuf-plugin`, V4) | Reference the `.proto`; the plugin matches the binary message. gRPC interactions are V4 sync-message/HTTP2. |
| **Avro** | Kafka schemas | **Plugin** (`pact-avro-plugin`, V4) | Reference the `.avsc`; the plugin matches the Avro record as a **message pact**. |
| **AsyncAPI** | Event-driven (Kafka, AMQP) | Design source → **message pact** | Read channel message payloads; scaffold a message-pact expectation (ports-and-adapters). |
| **GraphQL SDL** | GraphQL APIs | HTTP POST consumer test | Model the query/mutation as an HTTP `POST` to the GraphQL endpoint; matchers on `query`/`variables` (request) and `data`/`errors` (response). |
| **Pact files** | Existing CDC | Verify / republish | An existing pact file is already the contract — verify it against a provider or `publish` it to the broker. |

## Per-source detail

### OpenAPI / Swagger
- **Design source path**: `scaffold_from_schema.py --type openapi --operation "GET /orders/{id}"` emits a consumer test where the request path/method come from the operation and the response body matchers come from the response schema (`$ref` resolved). Tighten any regex it guesses.
- **Bi-directional path**: publish the provider's OpenAPI as a *provider contract* (see `assets/pactflow-bidirectional/`). PactFlow cross-verifies the consumer pact against it. No provider test code; requires PactFlow (not the open-source broker).

### JSON Schema
- Map: `type:string`+`format:email` → email/regex matcher; `type:integer` → integer matcher; `enum:[A,B]` → regex `A|B`; `required` → field present; `items` → `eachLike`.
- Use for both HTTP response bodies and **message** payloads.

### XSD / WSDL (SOAP, public-sector messaging)
- No bi-directional support — use **design source + XML matchers**.
- WSDL: extract `<wsdl:operation>`, the `soap:address` endpoint, and `SOAPAction`. Each operation → one interaction: `POST` to the endpoint, `Content-Type: text/xml` (or `application/soap+xml` for SOAP 1.2), body built with XML matchers from the referenced XSD types.
- Keep namespaces and required elements exact; loosen text content to type/regex matchers.

### Protobuf / gRPC
- Requires **V4** + `pact-protobuf-plugin`: `pact-plugin-cli install protobuf`.
- The consumer test references the `.proto` service/message; the plugin handles binary matching. Provider verification replays via the plugin.

### Avro
- Requires **V4** + `pact-avro-plugin`. Modelled as a **message pact** (Kafka). Reference the `.avsc`; the plugin matches the Avro record.

### AsyncAPI
- AsyncAPI is the **design source** for message pacts. Read the channel's message payload schema, scaffold a message-pact expectation, and test the domain **port** (see `matchers-and-states.md` §Message pacts).

### GraphQL SDL
- Pact has no special GraphQL mode: treat it as **HTTP**. One interaction = `POST <graphql-endpoint>` with body `{ "query": ..., "variables": ... }`. Match the `query` string (often a regex/like) and `variables`; match the response `data`/`errors` shape with matchers derived from the SDL types. Use V4.

### Existing Pact files
- If you already have a pact file (consumer-driven), don't regenerate it — **verify** it against the provider or **publish** it to the broker (`publish_pacts.*`). `scaffold_from_schema.py --type pact` summarizes its interactions and can stub a provider verification.

## Using the scaffolder

```bash
python scripts/scaffold_from_schema.py \
  --type   <openapi|swagger|jsonschema|xsd|wsdl|protobuf|avro|asyncapi|graphql|pact> \
  --input  <path-to-contract> \
  --lang   <java|js|dotnet|go|python> \
  --role   <consumer|provider> \
  [--operation "GET /orders/{id}"]  [--channel orders.placed]  [--message OrderPlaced] \
  --out    <output-path>
```

The scaffolder produces a **starting point**, not a finished test:

- It guesses matchers from the schema — **review every regex** (widen or tighten) and confirm which fields are genuinely fixed.
- It cannot know provider-state names — fill in `given(...)` to match your data setup.
- For Protobuf/Avro it emits the V4 + plugin wiring and references the schema file rather than inlining a body.

## Anti-patterns

- ❌ Claiming the schema "is" the contract in classic Pact — only **bi-directional** treats OpenAPI as the provider contract.
- ❌ Copying the **entire** schema response into the test as literals — derive matchers, keep it minimal.
- ❌ Using JSON matchers for XML/SOAP — use XML matchers.
- ❌ Skipping the plugin install for Protobuf/Avro, then hand-rolling JSON — wrong wire format.
