# Language packs — index & cross-language rules

This skill is a **family**. The detailed consumer/provider snippets and build config for each language live in that language's **own installable skill** under `languages/<lang>/SKILL.md`. This file is the at-a-glance map and the rules that apply to every language.

## Why a family

`npx skills add` treats each folder with a `SKILL.md` as a separately selectable skill. That lets a user install the core plus only the languages they use, instead of all 11. See the repository README for selective-install commands.

## Pack map

| Language | Pack folder | Skill name | Library | Build/Pkg | Spec default |
|---|---|---|---|---|---|
| Java / JVM | `languages/java` | `pact-java` | `au.com.dius.pact` (pact-jvm) | Maven / Gradle | V4 |
| Scala | `languages/scala` | `pact-scala` | pact-jvm + `pact4s` | sbt | V4 |
| JavaScript / TypeScript | `languages/javascript` | `pact-javascript` | `@pact-foundation/pact` | npm | V4 |
| .NET | `languages/dotnet` | `pact-dotnet` | `PactNet` | NuGet | V4 |
| Go | `languages/go` | `pact-go` | `pact-foundation/pact-go/v2` | go mod | V4 |
| Python | `languages/python` | `pact-python` | `pact-python` | pip | V4 (v3 API) |
| Ruby | `languages/ruby` | `pact-ruby` | `pact` | gem | V3 |
| PHP | `languages/php` | `pact-php` | `pact-php` | composer | V4 |
| Rust | `languages/rust` | `pact-rust` | `pact_consumer`/`pact_verifier` | cargo | V4 |
| Swift | `languages/swift` | `pact-swift` | `PactSwift` | SwiftPM | V3 |
| C++ | `languages/cpp` | `pact-cpp` | `pact-cplusplus` | CMake | V3/V4 |

## Rules that apply to every language

- **Spec version**: choose **V4** for plugins (gRPC/Avro), GraphQL-as-HTTP, and mixed HTTP+message pacts; **V3** for standard provider states with parameters; **V2** only for legacy brokers.
- **One interaction per test.** Express dependencies as **provider states** (`given(...)`), never seed data inside the test body.
- **Matchers, not literals.** See `matchers-and-states.md`.
- **Real client code** runs against the mock server URL in the consumer test — never assert against a hand-built request.
- **Provider verification** must register a **state handler for every `given(...)`** string any consumer uses, and should enable **pending + WIP** pacts so a new consumer expectation cannot break the provider build.
- **Publish with version = git SHA** and the current branch; verify with the provider's git SHA and `publishVerificationResult=true`. See `broker-and-cicd.md`.
- **Plugins** (gRPC/Protobuf, Avro) require V4 and the relevant plugin installed via `pact-plugin-cli`. See `schema-driven.md`.
