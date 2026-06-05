package com.example;

import au.com.dius.pact.consumer.MockServer;
import au.com.dius.pact.consumer.dsl.PactDslWithProvider;
import au.com.dius.pact.consumer.junit5.PactConsumerTestExt;
import au.com.dius.pact.consumer.junit5.PactTestFor;
import au.com.dius.pact.core.model.PactSpecVersion;
import au.com.dius.pact.core.model.RequestResponsePact;
import au.com.dius.pact.core.model.annotations.Pact;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;

import java.util.Map;

import static au.com.dius.pact.consumer.dsl.LambdaDsl.newJsonBody;
import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * ITERATION 1 (Java consumer): run the real PetClient against the Pact MOCK
 * provider and record a pact file (target/pacts/JavaPetClient-PetstoreProvider.json).
 */
@ExtendWith(PactConsumerTestExt.class)
@PactTestFor(providerName = "PetstoreProvider", pactVersion = PactSpecVersion.V3)
class PetClientPactTest {

    @Pact(consumer = "JavaPetClient")
    RequestResponsePact getPet(PactDslWithProvider builder) {
        return builder
                .given("pet 1 exists")
                .uponReceiving("a request for pet 1")
                .path("/api/v3/pet/1").method("GET")
                .headers("Accept", "application/json")
                .willRespondWith()
                .status(200)
                .headers(Map.of("Content-Type", "application/json"))
                // Best practice: only assert the fields THIS client reads (id, name, status).
                // Asserting photoUrls/category/tags here would over-specify the contract.
                .body(newJsonBody(o -> {
                    o.integerType("id", 1);
                    o.stringType("name", "Cat 1");
                    o.stringMatcher("status", "available|pending|sold", "available");
                }).build())
                .toPact();
    }

    @Test
    @PactTestFor(pactMethod = "getPet")
    void getsPet1(MockServer mock) throws Exception {
        Pet pet = new PetClient(mock.getUrl()).getPet(1); // REAL client code
        assertEquals(1, pet.id());
        assertEquals("available", pet.status());
    }
}
