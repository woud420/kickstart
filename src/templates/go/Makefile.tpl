.PHONY: install dev test typecheck check build clean
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

typecheck: test

check: test

build: install
	@$(call log,Building Go binary)
	@go build -o bin/{{service_name}} ./src

clean:
	@$(call log,Removing Go build artifacts)
	@rm -rf bin/
