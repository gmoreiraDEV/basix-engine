# Basix Engine

To build and update image on DockerHub, follow this steps
```sh
# Só build
make build
```

```sh
# Build + push
make build-push
```

```sh
# (Opcional) com tag personalizada
make build IMAGE_TAG=v0.1.0
make build-push IMAGE_TAG=v0.1.0
```