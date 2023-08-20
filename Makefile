REPO_NAME := $(shell basename ${PWD})

IMAGE := $(REPO_NAME)
TAG := local-dev

DOCKER_IMAGE ?= $(IMAGE):$(TAG)

ENVRC_VARS := $(shell awk -F'[ =]' '/^export / {print $$2}' .envrc | xargs -I{} echo '-e {}')

build:
	docker buildx build --tag $(DOCKER_IMAGE) container

run:
	docker run \
		-it \
		--rm \
		$(ENVRC_VARS) \
		-v ${PWD}:/src \
		$(DOCKER_IMAGE)

black:
	docker run \
		-it \
		--rm \
		-v ${PWD}:/src \
		python:3.11-slim \
		bash -c "pip install black && black /src/container/"
