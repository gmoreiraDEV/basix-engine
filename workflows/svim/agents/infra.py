# agents/svim/infra.py
import os
import json
from datetime import datetime
from typing import Any, Dict, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session


# ==================== QDRANT ====================
def create_qdrant_client(config: Optional[Dict[str, Any]] = None) -> QdrantClient:
    """
    Cria um cliente Qdrant usando URL e API Key do config ou do ambiente.

    Prioridade:
    1) config["qdrant_url"] / config["qdrant_api_key"]
    2) variáveis de ambiente QDRANT_URL / QDRANT_API_KEY
    """
    config = config or {}

    url = config.get("qdrant_url") or os.getenv("QDRANT_URL")
    api_key = config.get("qdrant_api_key") or os.getenv("QDRANT_API_KEY")

    if not url:
        raise ValueError("Qdrant URL não definida (use config['qdrant_url'] ou QDRANT_URL).")

    client = QdrantClient(
        url=url,
        api_key=api_key,
    )

    return client


def ensure_qdrant_collection(
    client: QdrantClient,
    collection_name: str,
    vector_size: int = 1536,
    distance: Distance = Distance.COSINE,
) -> None:
    """
    Garante que a collection exista no Qdrant.
    Se não existir, cria com vector_size informado.
    """
    collections = client.get_collections()
    existing = {c.name for c in collections.collections}

    if collection_name in existing:
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=distance),
    )


# ==================== POSTGRES / SQLALCHEMY ====================

def create_session_factory(database_url: Optional[str] = None) -> sessionmaker:
    """
    Cria um SessionFactory do SQLAlchemy.

    Usa:
    - database_url passado como argumento, ou
    - env DATABASE_URL
    """
    db_url = database_url or os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL não definido para conexão com Postgres.")

    engine = create_engine(db_url, future=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


# ==================== LOGS DA SVIM ====================

def log_svim_interaction(
    session: Session,
    *,
    user_id: Optional[str],
    session_id: Optional[str],
    intent: Optional[str],
    request: Dict[str, Any],
    response: Dict[str, Any],
) -> None:
    """
    Loga uma interação da SVIM em uma tabela Postgres.

    Tabela sugerida (crie via migration/SQL):
    ------------------------------------------------
    CREATE TABLE IF NOT EXISTS interaction_logs (
        id           BIGSERIAL PRIMARY KEY,
        user_id      TEXT,
        session_id   TEXT,
        intent       TEXT,
        request_json JSONB,
        response_json JSONB,
        created_at   TIMESTAMPTZ DEFAULT NOW()
    );
    ------------------------------------------------
    """
    payload = {
        "user_id": user_id,
        "session_id": session_id,
        "intent": intent,
        "request_json": json.dumps(request),
        "response_json": json.dumps(response),
        "created_at": datetime.now(datetime.timezone.utc).isoformat(),
    }

    session.execute(
        text("""
            INSERT INTO interaction_logs
                (user_id, session_id, intent, request_json, response_json, created_at)
            VALUES
                (:user_id, :session_id, :intent, :request_json, :response_json, NOW())
        """),
        payload,
    )
    session.commit()
