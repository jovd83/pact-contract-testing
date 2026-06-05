// Petstore provider we CONTROL (so we can set provider states and introduce a
// breaking change in iteration 4). It mirrors the Pet shape served by the live
// swaggerapi/petstore3 container.
//
// Env:
//   PORT                 listen port (default 8082)
//   PROVIDER_BREAKING=1  iteration-4 breaking change: rename `status` -> `availability`
const express = require("express");

const app = express();
app.use(express.json());

const BREAKING = process.env.PROVIDER_BREAKING === "1";

// In-memory data store (seeded). Provider states ensure specific rows exist.
const pets = new Map();
function seedPet(id) {
  pets.set(id, {
    id,
    category: { id: 2, name: "Cats" },
    name: `Cat ${id}`,
    photoUrls: ["url1", "url2"],
    tags: [{ id: 1, name: "tag1" }, { id: 2, name: "tag2" }],
    status: "available",
  });
}
seedPet(1);

function serialize(pet) {
  const out = { ...pet };
  if (BREAKING) {
    // Breaking change: the field consumers rely on (`status`) is renamed.
    out.availability = out.status;
    delete out.status;
  }
  return out;
}

// --- Pact provider-state setup endpoint (used by the verifier's state handlers) ---
app.post("/_pact/provider-states", (req, res) => {
  const state = req.body && req.body.state;
  if (state === "pet 1 exists") seedPet(1);
  if (state === "no pet 999 exists") pets.delete(999);
  res.status(200).json({ result: `state set: ${state}` });
});

// --- The actual API under contract ---
app.get("/api/v3/pet/:petId", (req, res) => {
  const id = Number(req.params.petId);
  const pet = pets.get(id);
  if (!pet) return res.status(404).json({ code: 1, type: "error", message: "Pet not found" });
  res.status(200).json(serialize(pet));
});

const port = Number(process.env.PORT || 8082);
app.listen(port, () => {
  console.log(`petstore-provider listening on http://localhost:${port}  (breaking=${BREAKING})`);
});
