.PHONY: install dev test typecheck check build lint fmt clean
{% include "_shared/make_logging.mk.tpl" %}

install:
	@$(call log,Downloading Go modules)
	@go mod download

dev: install
	@$(call log,Running Go service)
	@go run ./src/main.go

test: install
	@$(call log,Running Go tests)
	@go test ./...

typecheck: install
	@$(call log,Running go vet)
	@go vet ./...

fmt:
	@$(call log,Formatting Go sources)
	@gofmt -w .

lint: install
	@$(call log,Checking Go formatting)
	@unformatted=$$(gofmt -l .); if [ -n "$$unformatted" ]; then echo "Files need gofmt:"; echo "$$unformatted"; exit 1; fi
	@$(call log,Running go vet)
	@go vet ./...

check: lint typecheck test

build: install
	@$(call log,Building Go binary)
	@go build -o bin/{{service_name}} ./src

clean:
	@$(call log,Removing Go build artifacts)
	@rm -rf bin/
