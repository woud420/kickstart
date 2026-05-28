DOCKER_IMAGE ?= {{ service_name }}:local

docker-build:
	@$(call log,Building Docker image $(DOCKER_IMAGE))
	@docker build -t $(DOCKER_IMAGE) .
