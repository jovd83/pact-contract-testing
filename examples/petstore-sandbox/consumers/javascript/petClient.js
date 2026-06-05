// Real JavaScript client for the Petstore API. The consumer Pact test exercises
// THIS code against the mock provider — we never hand-build the request.
class PetClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  async getPet(id) {
    const res = await fetch(`${this.baseUrl}/api/v3/pet/${id}`, {
      headers: { Accept: "application/json" },
    });
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`unexpected status ${res.status}`);
    const body = await res.json();
    // The client only reads these fields — the contract should cover exactly them.
    return {
      id: body.id,
      name: body.name,
      status: body.status,
      photoUrls: body.photoUrls,
    };
  }
}

module.exports = { PetClient };
