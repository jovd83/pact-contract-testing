// ITERATION 1 (JavaScript consumer): run the real client against the Pact MOCK
// provider and record a pact file. No real provider is involved here.
const path = require("path");
const { PactV4, MatchersV3 } = require("@pact-foundation/pact");
const { PetClient } = require("./petClient");

const { integer, string, regex, eachLike, like } = MatchersV3;

const pact = new PactV4({
  consumer: "JsPetClient",
  provider: "PetstoreProvider",
  dir: path.resolve(__dirname, "../../pacts"),
  logLevel: "warn",
});

async function main() {
  await pact
    .addInteraction()
    .given("pet 1 exists")
    .uponReceiving("a request for pet 1")
    .withRequest("GET", "/api/v3/pet/1", (b) => b.headers({ Accept: "application/json" }))
    .willRespondWith(200, (b) => {
      b.headers({ "Content-Type": "application/json" });
      b.jsonBody({
        id: integer(1),
        name: string("Cat 1"),
        status: regex("available|pending|sold", "available"),
        photoUrls: eachLike(string("url1")),
        category: like({ id: integer(2), name: string("Cats") }),
        tags: eachLike({ id: integer(1), name: string("tag1") }),
      });
    })
    .executeTest(async (mock) => {
      const pet = await new PetClient(mock.url).getPet(1); // REAL client code
      if (!pet || pet.id !== 1 || pet.status !== "available") {
        throw new Error(`client did not map the response: ${JSON.stringify(pet)}`);
      }
      console.log("JS consumer test PASSED against mock:", JSON.stringify(pet));
    });
}

main()
  .then(() => process.exit(0))
  .catch((e) => {
    console.error("JS consumer test FAILED:", e.message || e);
    process.exit(1);
  });
