REPO_NAME := $(shell basename ${PWD})

IMAGE := $(REPO_NAME)
TAG := local-dev

ENVRC_VARS := $(shell awk -F'[ =]' '/^export / {print $$2}' .envrc | xargs -I{} echo '-e {}')

build:
	docker build --tag $(IMAGE):$(TAG) container

run: build
	docker run \
		-it \
		--rm \
		$(ENVRC_VARS) \
		-v ${PWD}:/src \
		$(IMAGE):$(TAG)

black:
	docker run \
		-it \
		--rm \
		-v ${PWD}:/src \
		python:3.11-slim \
		bash -c "pip install black && black /src/container/"
