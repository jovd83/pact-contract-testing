package com.example;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

/** Real Java client for the Petstore API; exercised by the consumer Pact test. */
public class PetClient {
    private final String baseUrl;
    private final HttpClient http = HttpClient.newHttpClient();
    private final ObjectMapper mapper = new ObjectMapper();

    public PetClient(String baseUrl) {
        this.baseUrl = baseUrl;
    }

    public Pet getPet(int id) throws Exception {
        HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + "/api/v3/pet/" + id))
                .header("Accept", "application/json")
                .GET().build();
        HttpResponse<String> res = http.send(req, HttpResponse.BodyHandlers.ofString());
        if (res.statusCode() == 404) return null;
        if (res.statusCode() != 200) throw new RuntimeException("unexpected status " + res.statusCode());
        JsonNode n = mapper.readTree(res.body());
        // The client reads exactly these fields — the contract should cover them.
        return new Pet(n.get("id").asInt(), n.get("name").asText(), n.get("status").asText());
    }
}
