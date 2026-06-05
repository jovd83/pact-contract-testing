"""Real Python client for the Petstore API; exercised by the consumer Pact test."""
import json
import urllib.request


class PetClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def get_pet(self, pet_id: int):
        req = urllib.request.Request(
            f"{self.base_url}/api/v3/pet/{pet_id}",
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            if resp.status == 404:
                return None
            body = json.loads(resp.read())
        # The client only reads these fields — the contract should cover them.
        return {"id": body["id"], "name": body["name"], "status": body["status"]}
