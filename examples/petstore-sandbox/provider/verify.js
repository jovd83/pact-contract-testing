// Provider verification (ITERATION 2 and 4): replay the STORED pacts that the
// consumers published to the broker against our running provider.
//
// Env: PACT_BROKER_BASE_URL, PACT_BROKER_USERNAME, PACT_BROKER_PASSWORD,
//      PROVIDER_BASE_URL (default http://localhost:8082), PROVIDER_VERSION.
const { Verifier } = require("@pact-foundation/pact");

const providerVersion = process.env.PROVIDER_VERSION || `dev-${Date.now()}`;

new Verifier({
  provider: "PetstoreProvider",
  providerBaseUrl: process.env.PROVIDER_BASE_URL || "http://localhost:8082",

  pactBrokerUrl: process.env.PACT_BROKER_BASE_URL || "http://localhost:9292",
  pactBrokerUsername: process.env.PACT_BROKER_USERNAME || "pact",
  pactBrokerPassword: process.env.PACT_BROKER_PASSWORD || "pact",

  // Verify the latest pact from every consumer's main branch (the stored
  // requests/responses recorded in iteration 1).
  consumerVersionSelectors: [{ mainBranch: true }],

  publishVerificationResult: true,
  providerVersion,
  providerVersionBranch: process.env.PROVIDER_BRANCH || "main",

  // Pending + WIP: a brand-new consumer expectation is reported but does NOT
  // fail this provider build (see iteration 3).
  enablePending: true,
  includeWipPactsSince: "2020-01-01",

  // The provider sets up data via its own /_pact/provider-states endpoint.
  stateHandlers: {
    "pet 1 exists": async () => {
      await fetch((process.env.PROVIDER_BASE_URL || "http://localhost:8082") + "/_pact/provider-states", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ state: "pet 1 exists" }),
      });
      return "pet 1 seeded";
    },
  },
})
  .verifyProvider()
  .then(() => {
    console.log("PROVIDER VERIFICATION: PASSED");
    process.exit(0);
  })
  .catch((e) => {
    console.error("PROVIDER VERIFICATION: FAILED\n", e.message || e);
    process.exit(1);
  });
