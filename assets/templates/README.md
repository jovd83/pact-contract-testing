# Templates

Starting points to copy into a project. They are deliberately minimal — adapt names, paths, and matchers. The authoritative, per-language snippets live in each language pack (`languages/<lang>/SKILL.md`); these files are language-neutral checklists you fill in.

## consumer-test.md — consumer interaction skeleton

```
GIVEN  <provider state name>                  # precondition the provider sets up
UPON RECEIVING  <human description>
WITH REQUEST
  method:  GET|POST|PUT|PATCH|DELETE
  path:    /resource/{id}                      # match exactly what the client sends
  headers: { ... required headers ... }
  query:   { ... required params ... }
  body:    { ... request matchers (POST/PUT) ... }
WILL RESPOND WITH
  status:  200
  headers: { Content-Type: application/json }
  body:    { ... RESPONSE MATCHERS, not literals ... }
TEST BODY
  call the REAL client against mockServer.url
  assert the client mapped the response correctly
```

## provider-verification.md — provider skeleton

```
PROVIDER  <provider name>
SOURCE    pact broker (selectors: mainBranch, deployedOrReleased) + token from env
TARGET    http://localhost:<port>             # the running provider
STATE HANDLERS
  for EACH given(...) used by ANY consumer:
    seed the data this state requires; tear down after
OPTIONS
  providerVersion = git SHA ; branch = current branch
  publishVerificationResult = true
  enablePending = true ; includeWipPactsSince = <date>
```

## message-pact.md — async (Kafka/SQS/SNS/AMQP) skeleton

```
CONSUMER (expectation)
  expectsToReceive  <message description>
  withContent       { ... payload matchers ... }
  TEST: feed the content to the REAL domain PORT handler (not the transport adapter)

PROVIDER (producer)
  for <message description>: produce the message body given the state
  verifier checks producer output ⊇ consumer expectation
```

See `references/matchers-and-states.md` and `references/derivation-modes.md` for how to fill these in.
