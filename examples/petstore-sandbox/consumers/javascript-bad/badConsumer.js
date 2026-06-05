// ITERATION 3: a FIFTH consumer that MISINTERPRETED the contract.
// Its OWN consumer test passes (the mock returns whatever this consumer declares),
// but the pact it publishes does NOT match what the real provider returns, so
// provider verification will FAIL — and the broker reports exactly why.
//
// Two misinterpretations baked in:
//   1. Expects `status` in UPPERCASE ("AVAILABLE|PENDING|SOLD")  -> provider sends "available"
//   2. Expects a `priceUsd` field                                -> provider never returns it
const path = require("path");
const { PactV4, MatchersV3 } = require("@pact-foundation/pact");
const { integer, string, regex } = MatchersV3;

// The mis-built client reads fields the real provider does not serve as expected.
class BadPetClient {
  constructor(baseUrl) { this.baseUrl = baseUrl; }
  async getPet(id) {
    const res = await fetch(`${this.baseUrl}/api/v3/pet/${id}`, { headers: { Accept: "application/json" } });
    const body = await res.json();
    return { id: body.id, status: body.status, priceUsd: body.priceUsd };
  }
}

const pact = new PactV4({
  consumer: "BadPetClient",
  provider: "PetstoreProvider",
  dir: path.resolve(__dirname, "../../pacts"),
  logLevel: "warn",
});

async function main() {
  await pact
    .addInteraction()
    .given("pet 1 exists")
    .uponReceiving("a request for pet 1 (misinterpreted)")
    .withRequest("GET", "/api/v3/pet/1", (b) => b.headers({ Accept: "application/json" }))
    .willRespondWith(200, (b) => {
      b.headers({ "Content-Type": "application/json" });
      b.jsonBody({
        id: integer(1),
        status: regex("AVAILABLE|PENDING|SOLD", "AVAILABLE"), // WRONG: provider sends lowercase
        priceUsd: integer(999), // WRONG: field does not exist on the provider
      });
    })
    .executeTest(async (mock) => {
      const pet = await new BadPetClient(mock.url).getPet(1);
      if (pet.status !== "AVAILABLE" || pet.priceUsd !== 999) throw new Error("bad client mapping");
      console.log("BAD consumer test PASSED against ITS OWN mock:", JSON.stringify(pet));
    });
}

main().then(() => process.exit(0)).catch((e) => { console.error("bad consumer error:", e.message || e); process.exit(1); });
