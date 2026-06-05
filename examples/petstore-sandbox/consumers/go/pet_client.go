package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

// Pet is the minimal view this consumer reads.
type Pet struct {
	ID     int    `json:"id"`
	Name   string `json:"name"`
	Status string `json:"status"`
}

// PetClient is the real Go client exercised by the consumer Pact test.
type PetClient struct{ BaseURL string }

func NewPetClient(baseURL string) *PetClient { return &PetClient{BaseURL: baseURL} }

func (c *PetClient) GetPet(id int) (*Pet, error) {
	req, _ := http.NewRequest("GET", fmt.Sprintf("%s/api/v3/pet/%d", c.BaseURL, id), nil)
	req.Header.Set("Accept", "application/json")
	res, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()
	if res.StatusCode == 404 {
		return nil, nil
	}
	body, _ := io.ReadAll(res.Body)
	var p Pet
	if err := json.Unmarshal(body, &p); err != nil {
		return nil, err
	}
	return &p, nil
}
