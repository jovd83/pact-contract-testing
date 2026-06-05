# Dependency review — pre-ship gate (modern-dependency-guard)

**Date:** 2026-06-05 · **Reviewer:** modern-dependency-guard v1.1.1 · **Context:** publishing `pact-contract-testing` v1.3.0 to GitHub.

## Scope
The skill itself has **no runtime npm/pip dependencies** (Markdown + Python stdlib scripts). The only third-party dependency surface is the bundled Node example `examples/petstore-sandbox/provider/` (not part of skill execution; demo only). `node_modules/` is gitignored and not published.

## Finding (npm audit) — RESOLVED
Initial `npm audit` reported **3 high-severity** vulnerabilities:
- `underscore <=1.13.7` — unbounded recursion DoS in `_.flatten`/`_.isEqual` (GHSA-qpx9-hpmf-5gmw), pulled transitively via `@pact-foundation/pact-core` ← `@pact-foundation/pact@^13.1.4`.

## Action taken
| Package | Was | Now | Rationale (primary evidence: npm registry) |
|---|---|---|---|
| `@pact-foundation/pact` | `^13.1.4` | `^16.5.0` | Latest is **16.5.0** (2026-05-24), actively maintained, not deprecated. 16.5.x resolves the transitive `underscore` advisory (`underscore` now 1.13.8). Major bump 13→16; the demo uses the stable `PactV4`/`Verifier` surface. |
| `express` | `^4.19.2` | `^4.22.2` | Express **4.x is still maintained** (4.22.2, 2026-05-11) and patched. Stayed on 4.x deliberately — Express 5.x (5.2.1) is a major with routing/middleware breaking changes not worth the risk for a trivial demo server. Legacy-compatible, current, safe. |

Lockfile regenerated (`npm install --package-lock-only`); resolved: `@pact-foundation/pact 16.5.0`, `express 4.22.2`, `underscore 1.13.8`.

## Verification
`npm audit` after the bump: **found 0 vulnerabilities** (see `npm-audit.txt`).

## Caveat
The captured walkthrough in `examples/petstore-sandbox/docs/` was recorded against `@pact-foundation/pact` 13.x. The dependency declarations are now bumped for security; if the example is re-executed, minor output/API differences vs the captured docs are possible. The docs remain a valid historical record of a passing run.

## Language packs (quick sanity)
The language packs reference current major lines with floating ranges (e.g. Java `au.com.dius.pact.consumer:junit5:4.6.+` — pact-jvm 4.6.x is current). No deprecated libraries identified. No changes required.
