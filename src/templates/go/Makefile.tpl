.PHONY: dev test build clean

dev:
	go run ./src/main.go

test:
	go test ./...

build:
	go build -o bin/{{service_name}} ./src

clean:
	rm -rf bin/ 