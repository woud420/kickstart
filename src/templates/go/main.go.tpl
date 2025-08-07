package main

import (
	"log"
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
)

type HealthResponse struct {
	Status  string `json:"status"`
	Service string `json:"service"`
	Version string `json:"version"`
}

type RootResponse struct {
	Message string `json:"message"`
}

func main() {
	// Load .env file if it exists
	_ = godotenv.Load()

	// Get configuration from environment
	host := getEnv("HOST", "0.0.0.0")
	port := getEnv("PORT", "8000")
	ginMode := getEnv("GIN_MODE", "debug")

	gin.SetMode(ginMode)
	router := gin.Default()

	// Routes
	router.GET("/", rootHandler)
	router.GET("/health", healthHandler)

	// Start server
	address := host + ":" + port
	log.Printf("Starting {{SERVICE_NAME}} server on %s", address)
	
	if err := router.Run(address); err != nil {
		log.Fatal("Failed to start server:", err)
	}
}

func rootHandler(c *gin.Context) {
	c.JSON(http.StatusOK, RootResponse{
		Message: "{{SERVICE_NAME}} is running",
	})
}

func healthHandler(c *gin.Context) {
	c.JSON(http.StatusOK, HealthResponse{
		Status:  "healthy",
		Service: "{{SERVICE_NAME}}",
		Version: "0.1.0",
	})
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
