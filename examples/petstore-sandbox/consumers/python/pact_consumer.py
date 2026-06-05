"""ITERATION 1 (Python consumer): run the real client against the Pact MOCK
provider and record a pact file. Uses pact-python 3.x (top-level `pact` API)."""
import sys
from pathlib import Path

from pact import Pact, match
from pet_client import PetClient

PACTS_DIR = Path(__file__).resolve().parents[2] / "pacts"


def main() -> int:
    pact = Pact("PythonPetClient", "PetstoreProvider")
    (
        pact.upon_receiving("a request for pet 1")
        .given("pet 1 exists")
        .with_request("GET", "/api/v3/pet/1")
        .will_respond_with(200)
        .with_header("Content-Type", "application/json")
        .with_body(
            {
                "id": match.integer(1),
                "name": match.string("Cat 1"),
                "status": match.regex("available", regex="available|pending|sold"),
                "photoUrls": match.each_like(match.string("url1")),
                "category": match.like({"id": match.integer(2), "name": match.string("Cats")}),
                "tags": match.each_like({"id": match.integer(1), "name": match.string("tag1")}),
            }
        )
    )

    with pact.serve() as srv:
        pet = PetClient(str(srv.url)).get_pet(1)  # REAL client code
        assert pet["id"] == 1, pet
        assert pet["status"] == "available", pet
        print("Python consumer test PASSED against mock:", pet)

    PACTS_DIR.mkdir(parents=True, exist_ok=True)
    pact.write_file(PACTS_DIR, overwrite=True)
    print("pact written to", PACTS_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
