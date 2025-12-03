import logging
from typing import Any, Dict, Optional, List

logger = logging.getLogger(__name__)


class BaseAgent:
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        config: Dict[str, Any],
        enable_kg: bool = False,
        enable_memory: bool = True,
        enable_learning: bool = False,
    ) -> None:
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config
        self.enable_kg = enable_kg
        self.enable_memory = enable_memory
        self.enable_learning = enable_learning

    async def search_memory(
        self,
        query: str,
        limit: int = 3,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Busca memória relacionada para o agente.

        Implementação padrão:
        - Se existir `self.vector_store` com método `get_user_context`,
          retorna o contexto desse user_id (ignorando `query` por enquanto).
        - Caso contrário, retorna lista vazia.
        """
        if not self.enable_memory:
            logger.debug(f"[{self.agent_id}] Memory disabled, skipping search_memory")
            return []

        if not user_id:
            logger.debug(f"[{self.agent_id}] search_memory called without user_id")
            return []

        try:
            if hasattr(self, "vector_store") and hasattr(self.vector_store, "get_user_context"):
                logger.debug(
                    f"[{self.agent_id}] search_memory using vector_store.get_user_context "
                    f"(user_id={user_id}, limit={limit})"
                )
                context = await self.vector_store.get_user_context(
                    user_id=user_id,
                    k=limit,
                )
                return context or []
            else:
                logger.debug(
                    f"[{self.agent_id}] vector_store or get_user_context not available, "
                    "search_memory will be a no-op"
                )
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error in search_memory: {e}")

        return []

    async def store_interaction(
        self,
        user_id: str,
        interaction_type: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
    ) -> None:
        """
        Armazena metadados da interação do agente.

        Implementação padrão:
        - Apenas registra em log estruturado.
        - Você pode sobrescrever em subclasses ou plugar DB aqui depois.
        """
        try:
            logger.debug(
                f"[{self.agent_id}] store_interaction: "
                f"user_id={user_id}, type={interaction_type}, "
                f"input_keys={list(input_data.keys())}, "
                f"output_keys={list(output_data.keys())}"
            )
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error in store_interaction: {e}")
        return
