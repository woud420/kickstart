package api_test

import (
	"testing"

	"{{ package_name }}/src/api"
)

func TestHealth(t *testing.T) {
	response := api.Health()
	if response.Message != "Hello World" {
		t.Fatalf("expected Hello World, got %q", response.Message)
	}
}
