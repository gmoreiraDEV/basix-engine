import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

from agents.embeddings import EmbeddingClient

class SVIMVectorStore:
    def __init__(self, client: QdrantClient, collection: str):
        self.client = client
        self.collection = collection
        self.embedder = EmbeddingClient()  # usa text-embedding-3-small, por exemplo

    async def add_conversation(
        self,
        user_id: str,
        session_id: str,
        messages: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        # junta conteúdo das mensagens para gerar o embedding
        text = "\n".join(
            f"{m.get('role','user')}: {m.get('content','')}" for m in messages
        )
        vector = await self.embedder.embed(text)

        enriched_metadata = metadata or {}
        enriched_metadata.setdefault("timestamp", datetime.now().isoformat())

        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "user_id": user_id,
                "session_id": session_id,
                "messages": messages,
                "metadata": enriched_metadata,
            },
        )

        self.client.upsert(collection_name=self.collection, points=[point])

    async def get_user_context(self, user_id: str, k: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna até k blocos de mensagens anteriores desse user_id.
        Aqui eu uso filtro por payload user_id em vez de busca semântica.
        """
        result, _ = self.client.scroll(
            collection_name=self.collection,
            scroll_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ),
            limit=k,
        )

        context_messages: List[Dict[str, Any]] = []
        for point in result:
            msgs = point.payload.get("messages") or []
            context_messages.extend(msgs)

        return context_messages[-k:]  # só os k mais recentes

    async def get_latest_metadata(self, user_id: str) -> Dict[str, Any]:
        """
        Retorna o metadata mais recente salvo para esse usuário.

        Útil para restaurar `appointment_context` (ex.: appointment_draft) em cenários
        one-shot onde o backend ainda não persistiu manualmente.
        """
        result, _ = self.client.scroll(
            collection_name=self.collection,
            scroll_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ),
            limit=50,
        )

        latest = {}
        latest_ts = None
        for point in result:
            metadata = point.payload.get("metadata") or {}
            ts_raw = metadata.get("timestamp")
            ts = None
            try:
                ts = datetime.fromisoformat(ts_raw) if ts_raw else None
            except Exception:
                ts = None

            if ts is not None and (latest_ts is None or ts > latest_ts):
                latest_ts = ts
                latest = metadata

        return latest


def embed_text(text: str) -> List[float]:
    """
    Fallback de embedding determinístico para cenários sem dependência externa.

    Utiliza um hash simples para produzir um vetor estável de 6 dimensões.
    """

    digest = hashlib.sha256(text.encode("utf-8")).digest()
    # Converte os primeiros bytes em floats simples entre 0 e 1
    vector = [int.from_bytes(digest[i : i + 4], "big") / 2**32 for i in range(0, 24, 4)]
    return vector
