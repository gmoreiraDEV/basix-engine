import time
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

from agents.vector_store import embed_text


class CatalogSync:
    """Mantém cache local/vetorizado de profissionais e serviços."""

    def __init__(self, client: QdrantClient, ttl_seconds: int = 6 * 3600):
        self.client = client
        self.ttl_seconds = ttl_seconds
        self._last_sync: Dict[str, float] = {}

    def _should_sync(self, key: str) -> bool:
        last = self._last_sync.get(key, 0)
        return (time.time() - last) > self.ttl_seconds

    def sync_professionals_catalog(self, professionals: List[Dict[str, Any]]) -> None:
        if not self._should_sync("professionals"):
            return

        points = []
        for prof in professionals:
            text = " ".join(
                filter(
                    None,
                    [
                        prof.get("nome"),
                        prof.get("apelido"),
                        " ".join(prof.get("tags", [])),
                    ],
                )
            )
            points.append(
                rest.PointStruct(
                    id=str(prof.get("id")),
                    vector=embed_text(text),
                    payload={"professionalId": prof.get("id"), "nome": prof.get("nome")},
                )
            )
        if points:
            self.client.upsert(collection_name="professionals_catalog", points=points)
        self._last_sync["professionals"] = time.time()

    def sync_services_catalog(
        self, professional_id: int, services: List[Dict[str, Any]]
    ) -> None:
        key = f"services_{professional_id}"
        if not self._should_sync(key):
            return

        points = []
        for svc in services:
            text = " ".join(
                filter(
                    None,
                    [
                        svc.get("nome"),
                        svc.get("descricao"),
                        svc.get("categoria"),
                        " ".join(svc.get("tags", [])),
                    ],
                )
            )
            points.append(
                rest.PointStruct(
                    id=f"{professional_id}_{svc.get('id')}",
                    vector=embed_text(text),
                    payload={
                        "serviceId": svc.get("id"),
                        "nome": svc.get("nome"),
                        "categoria": svc.get("categoria"),
                        "professionalId": professional_id,
                    },
                )
            )
        if points:
            self.client.upsert(collection_name="services_catalog", points=points)
        self._last_sync[key] = time.time()
