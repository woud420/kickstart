ENV ?= dev
{% if uses_kubernetes %}
KUSTOMIZE ?= kubectl kustomize
{% endif %}
TERRAFORM ?= terraform
{% if uses_bun_turbo %}
BUN ?= bun
{% endif %}
{% include "_shared/make_logging.mk.tpl" %}

.PHONY: install dev test typecheck check build compose-up compose-down tf-init tf-plan tf-validate docs-check child-validation-note{% if uses_kubernetes %} k8s-render{% endif %}{% if uses_cloudflare_workers %} cf-worker-notes{% endif %}

install:
	@$(call log,Showing system install note)
	@echo "System roots are composition scaffolds. Run child component install commands from child .kickstart/scaffold.json manifests."

dev:
	@$(call log,Showing system dev note)
	@echo "Start leaf projects from their own directories. This root does not run mixed-language services."

test: docs-check child-validation-note

typecheck: docs-check

check: docs-check child-validation-note

build:
	@$(call log,Showing system build note)
	@echo "Build leaf projects from their own directories. This root only owns shared scaffold files."

child-validation-note:
	@$(call log,Showing child validation note)
	@echo "Child validation is manifest-driven: apps/*, services/*, libs/*, and tools/* each own make install/test/check."

compose-up:
	@$(call log,Starting compose stack)
	@docker compose -f infra/docker/docker-compose.yml up --build

compose-down:
	@$(call log,Stopping compose stack)
	@docker compose -f infra/docker/docker-compose.yml down

{% if uses_kubernetes %}
k8s-render:
	@$(call log,Rendering Kubernetes manifests)
	@$(KUSTOMIZE) infra/k8s/overlays/$(ENV)
{% endif %}

{% if uses_cloudflare_workers %}
cf-worker-notes:
	@$(call log,Checking Cloudflare Worker notes)
	@test -f infra/cloudflare/workers/README.md
	@test -f infra/cloudflare/workers/wrangler.example.toml
{% endif %}

tf-init:
	@$(call log,Initializing Terraform)
	@cd infra/terraform/env/$(ENV) && $(TERRAFORM) init

tf-plan:
	@$(call log,Planning Terraform)
	@cd infra/terraform/env/$(ENV) && $(TERRAFORM) plan -var-file=terraform.tfvars.example

tf-validate:
	@$(call log,Validating Terraform)
	@cd infra/terraform/env/$(ENV) && $(TERRAFORM) validate

docs-check:
	@$(call log,Checking system docs)
	@test -f AGENTS.md
	@test -f .kickstart/scaffold.json
	@test -f docs/architecture/README.md
	@test -f docs/contracts/README.md
	@test -f docs/operations/README.md
	@test -f docs/decisions/0001-stack-profile.md
	@test -f docs/agents/recommended-agents.md
	@test -f docs/knowledge/README.md
{% if uses_cloudflare_workers %}
	@test -f infra/cloudflare/workers/README.md
{% endif %}
	@test -f knowledge/README.md
{% if uses_bun_turbo %}
	@test -f package.json
	@test -f turbo.json
{% endif %}
