// Publish one pact file to the broker via POST /contracts/publish.
// Works for any language's generated pact (they are all JSON pact files),
// so all 4 consumers use the same publisher — no per-language broker CLI needed.
//
// Usage: node publish-pact.js <pactFile> <version> [branch]
const fs = require("fs");

const [, , pactFile, version, branch = "main"] = process.argv;
if (!pactFile || !version) {
  console.error("Usage: node publish-pact.js <pactFile> <version> [branch]");
  process.exit(2);
}

const broker = process.env.PACT_BROKER_BASE_URL || "http://localhost:9292";
const user = process.env.PACT_BROKER_USERNAME || "pact";
const pass = process.env.PACT_BROKER_PASSWORD || "pact";

const pact = JSON.parse(fs.readFileSync(pactFile, "utf8"));
const consumerName = pact.consumer.name;
const providerName = pact.provider.name;

const payload = {
  pacticipantName: consumerName,
  pacticipantVersionNumber: version,
  branch,
  contracts: [
    {
      consumerName,
      providerName,
      specification: "pact",
      contentType: "application/json",
      content: Buffer.from(JSON.stringify(pact)).toString("base64"),
    },
  ],
};

fetch(`${broker}/contracts/publish`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: "Basic " + Buffer.from(`${user}:${pass}`).toString("base64"),
  },
  body: JSON.stringify(payload),
})
  .then(async (res) => {
    const text = await res.text();
    if (!res.ok) {
      console.error(`PUBLISH FAILED (${res.status}) for ${consumerName}:`, text.slice(0, 400));
      process.exit(1);
    }
    console.log(`Published ${consumerName} -> ${providerName}  version=${version} branch=${branch}`);
  })
  .catch((e) => {
    console.error("PUBLISH ERROR:", e.message || e);
    process.exit(1);
  });
