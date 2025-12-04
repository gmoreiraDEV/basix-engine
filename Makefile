# Nome e tag da imagem
IMAGE_NAME ?= gmoreiradev/svim-agent
IMAGE_TAG ?= latest

# Caminho do Dockerfile (a partir da raiz)
DOCKERFILE ?= workflows/svim/Dockerfile

# Contexto de build = raiz do repo
CONTEXT ?= .

.PHONY: build push build-push

build:
	docker build -f $(DOCKERFILE) -t $(IMAGE_NAME):$(IMAGE_TAG) $(CONTEXT)

push:
	docker push $(IMAGE_NAME):$(IMAGE_TAG)

build-push: build push
