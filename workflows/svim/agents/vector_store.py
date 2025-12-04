import uuid
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

        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "user_id": user_id,
                "session_id": session_id,
                "messages": messages,
                "metadata": metadata or {},
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
