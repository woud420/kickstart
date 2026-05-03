package api

type HealthResponse struct {
    Message string `json:"message"`
}

func Health() HealthResponse {
    return HealthResponse{Message: "Hello World"}
}
