IMAGE_NAME ?= gmoreiradev/svim-agent
IMAGE_TAG ?= latest
DOCKERFILE ?= workflows/svim/Dockerfile
CONTEXT ?= .

build:
	docker buildx build \
		--platform linux/amd64 \
		-f $(DOCKERFILE) \
		-t $(IMAGE_NAME):$(IMAGE_TAG) \
		$(CONTEXT)

push:
	docker buildx build \
		--platform linux/amd64 \
		-f $(DOCKERFILE) \
		-t $(IMAGE_NAME):$(IMAGE_TAG) \
		--push \
		$(CONTEXT)

build-push: push
