package main

import (
	"fmt"
	"testing"

	"github.com/pact-foundation/pact-go/v2/consumer"
	"github.com/pact-foundation/pact-go/v2/matchers"
	"github.com/stretchr/testify/assert"
)

// ITERATION 1 (Go consumer): run the real client against the Pact MOCK provider
// and record a pact file into /work/pacts.
func TestGetPet1(t *testing.T) {
	mockProvider, err := consumer.NewV4Pact(consumer.MockHTTPProviderConfig{
		Consumer: "GoPetClient",
		Provider: "PetstoreProvider",
		PactDir:  "/work/pacts",
	})
	assert.NoError(t, err)

	err = mockProvider.
		AddInteraction().
		Given("pet 1 exists").
		UponReceiving("a request for pet 1").
		WithRequest("GET", "/api/v3/pet/1", func(b *consumer.V4RequestBuilder) {
			b.Header("Accept", matchers.S("application/json"))
		}).
		WillRespondWith(200, func(b *consumer.V4ResponseBuilder) {
			b.Header("Content-Type", matchers.S("application/json"))
			b.JSONBody(matchers.Map{
				"id":        matchers.Integer(1),
				"name":      matchers.Like("Cat 1"),
				"status":    matchers.Regex("available", "available|pending|sold"),
				"photoUrls": matchers.EachLike(matchers.Like("url1"), 1),
				"category":  matchers.Like(matchers.Map{"id": matchers.Integer(2), "name": matchers.Like("Cats")}),
				"tags":      matchers.EachLike(matchers.Map{"id": matchers.Integer(1), "name": matchers.Like("tag1")}, 1),
			})
		}).
		ExecuteTest(t, func(c consumer.MockServerConfig) error {
			pet, err := NewPetClient(fmt.Sprintf("http://%s:%d", c.Host, c.Port)).GetPet(1) // REAL client
			assert.NoError(t, err)
			assert.Equal(t, 1, pet.ID)
			assert.Equal(t, "available", pet.Status)
			return nil
		})
	assert.NoError(t, err)
}
