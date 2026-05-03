.PHONY: install dev test typecheck check build clean

install:
	go mod download

dev: install
	go run ./src/main.go

test: install
	go test ./...

typecheck: test

check: test

build: install
	go build -o bin/{{service_name}} ./src

clean:
	rm -rf bin/ 
