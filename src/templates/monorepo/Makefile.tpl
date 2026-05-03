ENV ?= dev
{% if uses_kubernetes %}
KUSTOMIZE ?= kubectl kustomize
{% endif %}
TERRAFORM ?= terraform
BUN ?= bun

.PHONY: install dev test typecheck check build compose-up compose-down tf-init tf-plan tf-validate docs-check child-validation-note{% if uses_kubernetes %} k8s-render{% endif %}{% if uses_cloudflare_workers %} cf-worker-notes{% endif %}

install:
	@echo "System roots are composition scaffolds. Run child component install commands from child .kickstart/scaffold.json manifests."

dev:
	@echo "Start leaf projects from their own directories. This root does not run mixed-language services."

test: docs-check child-validation-note

typecheck: docs-check

check: docs-check child-validation-note

build:
	@echo "Build leaf projects from their own directories. This root only owns shared scaffold files."

child-validation-note:
	@echo "Child validation is manifest-driven: apps/*, services/*, libs/*, and tools/* each own make install/test/check."

compose-up:
	docker compose -f infra/docker/docker-compose.yml up --build

compose-down:
	docker compose -f infra/docker/docker-compose.yml down

{% if uses_kubernetes %}
k8s-render:
	$(KUSTOMIZE) infra/k8s/overlays/$(ENV)
{% endif %}

{% if uses_cloudflare_workers %}
cf-worker-notes:
	test -f infra/cloudflare/workers/README.md
	test -f infra/cloudflare/workers/wrangler.example.toml
{% endif %}

tf-init:
	cd infra/terraform/env/$(ENV) && $(TERRAFORM) init

tf-plan:
	cd infra/terraform/env/$(ENV) && $(TERRAFORM) plan -var-file=terraform.tfvars.example

tf-validate:
	cd infra/terraform/env/$(ENV) && $(TERRAFORM) validate

docs-check:
	test -f AGENTS.md
	test -f .kickstart/scaffold.json
	test -f docs/architecture/README.md
	test -f docs/contracts/README.md
	test -f docs/operations/README.md
	test -f docs/decisions/0001-stack-profile.md
	test -f docs/agents/recommended-agents.md
	test -f docs/knowledge/README.md
{% if uses_cloudflare_workers %}
	test -f infra/cloudflare/workers/README.md
{% endif %}
	test -f knowledge/README.md
	test -f package.json
	test -f turbo.json
