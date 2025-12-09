"""
💇‍♀️ SVIM Agent - Maria (Recepcionista / Atendimento)

Localização: svim/agents/main.py

Responsabilidades:
- Atender clientes da SVIM (ex: SVIM Pamplona) de forma educada e acolhedora
- Ajudar em agendamentos, reagendamentos e cancelamentos
- Esclarecer dúvidas sobre serviços, horários e políticas básicas
- Registrar informações importantes do cliente e manter contexto

Arquitetura:
- Baseado em BaseAgent (mesma base do ConversationAgent)
- Usa LangGraph (StateGraph) para orquestrar o fluxo interno
- Usa LLMClient para chamadas ao LLM com fallback
- Usa SVIMVectorStore para manter memória de conversas recentes
"""

import os
import json
import logging
from typing import TypedDict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from sqlalchemy.orm import Session
from qdrant_client import QdrantClient
from agents.infra import (
    create_qdrant_client,
    ensure_qdrant_collection,
    log_svim_interaction,
)

from agents.llm_client import LLMClient
from agents.vector_store import SVIMVectorStore
from agents.base_agent import BaseAgent
from agents.tools.index import TOOLS

# Prompts da SVIM
from agents.prompts import SVIMPrompts

logger = logging.getLogger(__name__)


# ==================== Tipos e Estado ====================

class SVIMIntent(Enum):
    """Tipos básicos de intenção para o agente da SVIM."""
    SCHEDULE = "schedule"       # Agendar
    RESCHEDULE = "reschedule"   # Reagendar
    CANCEL = "cancel"           # Cancelar
    INFO = "info"               # Dúvidas sobre serviços / horários / políticas
    SMALLTALK = "smalltalk"     # Conversa leve / saudação
    FAREWELL = "farewell"       # Despedida
    UNKNOWN = "unknown"         # Não identificado


class SVIMState(TypedDict):
    """
    Estado da conversa da SVIM dentro do LangGraph.
    """
    messages: List[Dict[str, Any]]
    user_id: str
    session_id: str
    intent: SVIMIntent
    customer_profile: Dict[str, Any]
    appointment_context: Dict[str, Any]
    policies_context: Dict[str, Any]
    needs_handoff: bool
    finish_session: bool


# ==================== Agente Principal ====================

class SVIMAgent(BaseAgent):
    """
    Maria - Agente de Atendimento SVIM

    Características:
    - Focado em atendimento de salão/spa/barbearia
    - Entende intenções básicas (agendar, remarcar, cancelar, dúvidas)
    - Usa prompts especializados da SVIM
    - Mantém memória de conversas para contexto
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, db_session: Optional[Session] = None):
        # Config padrão
        config = config or {}
        config.setdefault("qdrant_url", os.getenv("QDRANT_URL", "http://localhost:6333"))
        config.setdefault("qdrant_api_key", os.getenv("QDRANT_API_KEY", None))
        config.setdefault("qdrant_collection_name", "svim_conversations")
        config.setdefault("qdrant_vector_size", 1536)


        # Inicializa EnhancedAgentBase
        super().__init__(
            agent_id="svim_agent",
            agent_type="svim_reception",
            config=config,
            enable_kg=False,
            enable_memory=True,
            enable_learning=False
        )

        self.config = config
        self.db_session = db_session

        # LLM híbrido com fallback
        self.llm_client = LLMClient()

        # Vector store para memória (conversas SVIM)
        self.qdrant_client: QdrantClient = create_qdrant_client(config)
        ensure_qdrant_collection(
            self.qdrant_client,
            collection_name=config["qdrant_collection_name"],
            vector_size=config["qdrant_vector_size"],
        )   

        self.vector_store = SVIMVectorStore(
            client=self.qdrant_client,
            collection=self.config["qdrant_collection_name"]
        )

        # Prompts da SVIM
        self.prompts = SVIMPrompts()

        # Gestão de contexto
        self.max_context_messages = config.get("max_context_messages", 10)
        self.cache_ttl = config.get("cache_ttl", 300)

        # Tools
        self.tools = TOOLS

        # Workflow LangGraph
        try:
            self.workflow = self._build_workflow()
            logger.info("SVIMAgent initialized with LangGraph workflow")
        except Exception as e:
            logger.error(f"Failed to initialize SVIMAgent workflow: {e}")
            self.workflow = None

    # ==================== Workflow LangGraph ====================

    def _build_workflow(self) -> StateGraph:
        """
        Workflow simples para o agente SVIM:

        1. load_context       -> Carrega contexto/memória do cliente
        2. detect_intent      -> Detecta intenção básica (agendar, info, etc.)
        3. generate_response  -> Gera resposta usando prompts específicos
        4. save_memory        -> Salva conversa em memória vetorial
        """
        workflow = StateGraph(SVIMState)

        workflow.add_node("load_context", self._load_context)
        workflow.add_node("detect_intent", self._detect_intent)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("save_memory", self._save_memory)

        workflow.set_entry_point("load_context")
        workflow.add_edge("load_context", "detect_intent")
        workflow.add_edge("detect_intent", "generate_response")
        workflow.add_edge("generate_response", "save_memory")
        workflow.add_edge("save_memory", END)

        return workflow.compile(checkpointer=MemorySaver())

    # ==================== Nodes do Workflow ====================

    async def _load_context(self, state: SVIMState) -> SVIMState:
        """
        Carrega contexto recente de conversas com esse cliente.
        Pode ser usado no prompt como 'context' da SVIM.
        """
        try:
            user_context = await self.vector_store.get_user_context(
                user_id=state["user_id"],
                k=self.max_context_messages,
            )

            # Monta um texto simples de contexto
            history_text = self._format_messages(user_context)
            state["appointment_context"]["history"] = history_text

            logger.info(f"[SVIM] Context loaded for user {state['user_id']}: {len(user_context)} messages")
        except Exception as e:
            logger.error(f"[SVIM] Error loading context: {e}")

        return state

    async def _detect_intent(self, state: SVIMState) -> SVIMState:
        """
        Detecta a intenção básica do cliente com heurísticas simples.
        (Se quiser, depois dá pra trocar por uma chamada LLM só de classificação.)
        """
        try:
            last_message = ""
            for msg in reversed(state["messages"]):
                if msg.get("role") == "user":
                    last_message = msg.get("content", "")
                    break

            text = last_message.lower()

            intent = SVIMIntent.UNKNOWN

            # Heurísticas básicas em PT-BR
            if any(word in text for word in ["agendar", "marcar", "horário", "horario", "quero marcar", "cortar", "fazer"]):
                intent = SVIMIntent.SCHEDULE
            elif any(word in text for word in ["remarcar", "mudar horário", "mudar horario", "reagendar"]):
                intent = SVIMIntent.RESCHEDULE
            elif any(word in text for word in ["cancelar", "desmarcar"]):
                intent = SVIMIntent.CANCEL
            elif any(word in text for word in ["que horas", "funciona", "horário de atendimento", "horario de atendimento", "abre", "fecha", "preço", "preco", "valor", "serviço", "servico"]):
                intent = SVIMIntent.INFO
            elif any(word in text for word in ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "tudo bem"]):
                intent = SVIMIntent.SMALLTALK
            elif any(word in text for word in ["adeus", "tchau", "tchau tchau", "ate logo", "ate mais", "ate breve", "obrigado", "obrigada", "pode encerrar", "pode finalizar", "só isso", "valeu", "tudo certo", "perfeito",]):
                intent = SVIMIntent.FAREWELL

            state["intent"] = intent
            logger.info(f"[SVIM] Detected intent for user {state['user_id']}: {intent.value}")
        except Exception as e:
            logger.error(f"[SVIM] Error detecting intent: {e}")
            state["intent"] = SVIMIntent.UNKNOWN

        return state

    async def _generate_response(self, state: SVIMState) -> SVIMState:
        """
        Gera resposta da Maria usando os prompts da SVIM.
        Suporta chamadas de ferramentas (tools).
        """
        try:
            history = state["appointment_context"].get("history", "")
            customer_name = state["customer_profile"].get("name") or "cliente"
            base_context = f"Histórico recente:\n{history}\n\nCliente: {customer_name}"

            # Escolher prompt conforme intenção
            if state["intent"] in [SVIMIntent.SCHEDULE, SVIMIntent.RESCHEDULE, SVIMIntent.CANCEL]:
                system_prompt = self.prompts.get_scheduling_prompt(base_context)
            elif state["intent"] == SVIMIntent.INFO:
                policies = state["policies_context"].get("policies_text", "")
                system_prompt = self.prompts.get_policy_prompt(
                    f"{base_context}\n\nPolíticas:\n{policies}"
                )
            else:
                system_prompt = self.prompts.get_base_conversation_prompt(base_context)

            recent_messages = state["messages"][-6:]

            # === 1. Chamada ao modelo com tools habilitadas ===
            response = await self.llm_client.chat_completion(
                messages=recent_messages,
                system_prompt=system_prompt,
                tools=self.tools,
                temperature=0.3,
                max_tokens=500,
            )

            # === 2. Caso seja texto simples ===
            if isinstance(response, str):
                state["messages"].append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().isoformat(),
                })
                return state

            # === 3. Caso seja tool call ===
            if "tool" in response:
                tool_name = response["tool"]["name"]
                tool_args = response["tool"]["arguments"]

                tool_data = next((t for t in self.tools if t["name"] == tool_name), None)
                if not tool_data:
                    raise ValueError(f"Tool '{tool_name}' não encontrada")
                
                tool_fn = tool_data["py_fn"]

                tool_result = await tool_fn.ainvoke(tool_args)

                # Inserir chamada na conversa
                state["messages"].append({
                    "role": "assistant",
                    "tool_name": tool_name,
                    "tool_arguments": tool_args,
                    "content": None,
                })

                # Inserir resultado da tool
                state["messages"].append({
                    "role": "tool",
                    "tool_name": tool_name,
                    "content": json.dumps(tool_result),
                })

                # === 4. Segunda chamada para resposta final ===
                final_response = await self.llm_client.chat_completion(
                    messages=state["messages"],
                    system_prompt=system_prompt,
                    temperature=0.3,
                )

                state["messages"].append({
                    "role": "assistant",
                    "content": final_response,
                    "timestamp": datetime.now().isoformat(),
                })

            last_user_msg = next(
                m["content"] for m in reversed(state["messages"]) if m["role"] == "user"
            ).lower()

            state["finish_session"] = any(tok in last_user_msg for tok in SVIMIntent.FAREWELL.value)

            return state

        except Exception as e:
            logger.error(f"[SVIM] Error generating response (tools): {e}")
            state["messages"].append({
                "role": "assistant",
                "content": "Tive um erro ao processar sua solicitação. Pode tentar novamente?",
            })
            return state

    async def _save_memory(self, state: SVIMState) -> SVIMState:
        """
        Salva parte da conversa em memória vetorial.
        """
        try:
            await self.vector_store.add_conversation(
                user_id=state["user_id"],
                session_id=state["session_id"],
                messages=state["messages"][-2:],
                metadata={
                    "intent": state["intent"].value,
                    "finish_session": state["finish_session"],
                },
            )
            logger.info(f"[SVIM] Conversation saved to memory for user {state['user_id']}")
        except Exception as e:
            logger.error(f"[SVIM] Error saving conversation to memory: {e}")

        return state

    # ==================== Helpers ====================

    def _format_messages(self, messages: List[Dict[str, Any]]) -> str:
        """
        Formata lista de mensagens em texto simples para contexto.
        Espera estrutura compatível com o armazenamento do vector_store.
        """
        if not messages:
            return ""

        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

    # ==================== API Pública ====================
    async def process_message(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        customer_profile: Optional[Dict[str, Any]] = None,
        policies_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Processa uma mensagem do cliente.

        Args:
            user_id: identificador do cliente (pode ser ID interno, telefone, etc.)
            message: texto enviado pelo cliente
            session_id: ID da sessão (whatsapp/atendimento)
            customer_profile: dados básicos do cliente (nome, telefone, etc.)
            policies_context: políticas dinâmicas (pode vir de banco / painel SVIM)

        Returns:
            Dict com resposta da Maria e metadados.
        """
        try:
            if self.workflow is None:
                logger.error("[SVIM] Workflow not initialized")
                return {
                    "success": False,
                    "error": "Workflow not initialized",
                    "response": "Estou passando por uma instabilidade no momento. Pode tentar novamente em instantes?",
                }

            state: SVIMState = {
                "messages": [
                    {
                        "role": "user",
                        "content": message,
                        "timestamp": datetime.now().isoformat(),
                    }
                ],
                "user_id": user_id,
                "session_id": session_id or f"svim_session_{user_id}_{int(datetime.now().timestamp())}",
                "intent": SVIMIntent.UNKNOWN,
                "customer_profile": customer_profile or {},
                "appointment_context": {},
                "policies_context": policies_context or {},
                "needs_handoff": False,
                "finish_session": False,
            }

            config = {"configurable": {"thread_id": state["session_id"]}}

            # Chama o workflow do LangGraph
            workflow_result = await self.workflow.ainvoke(state, config=config)

            result = workflow_result.get("state", workflow_result)

            assistant_message = next(
                (msg for msg in reversed(result["messages"]) if msg.get("role") == "assistant"),
                None,
            )

            return {
                "success": True,
                "response": assistant_message["content"] if assistant_message else "",
                "metadata": {
                    "session_id": result["session_id"],
                    "intent": result["intent"].value,
                    "needs_handoff": result["needs_handoff"],
                    "finish_session": result["finish_session"],
                },
            }

        except Exception as e:
            logger.error(f"[SVIM] Error processing message: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Tive um erro aqui do meu lado, mas quero te ajudar. Pode tentar novamente por favor?",
            }


    async def process(self, input_data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Método compatível com EnhancedAgentBase (mesmo estilo do ConversationAgent).

        input_data esperado:
        {
            "message": str,
            "session_id": Optional[str],
            "customer_profile": Optional[Dict[str, Any]],
            "policies_context": Optional[Dict[str, Any]]
        }
        """
        message = input_data.get("message", "")
        session_id = input_data.get("session_id")
        customer_profile = input_data.get("customer_profile", {})
        policies_context = input_data.get("policies_context", {})

        # Opcional: buscar conversas semelhantes via memória
        await self.search_memory(
            query=f"svim conversation about: {message[:100]}",
            limit=3,
            user_id=user_id,
        )

        result = await self.process_message(
            user_id=user_id or "unknown_user",
            message=message,
            session_id=session_id,
            customer_profile=customer_profile,
            policies_context=policies_context,
        )

        # Armazenar interação na KG/memória do EnhancedAgentBase (se/quando você quiser usar)
        await self.store_interaction(
            user_id=user_id or "unknown_user",
            interaction_type="svim_conversation",
            input_data=input_data,
            output_data=result,
        )

        # Log estruturado em Postgres (opcional)
        if self.db_session is not None:
            try:
                log_svim_interaction(
                    self.db_session,
                    user_id=user_id,
                    session_id=result["metadata"]["session_id"] if result.get("metadata") else None,
                    intent=result["metadata"]["intent"] if result.get("metadata") else None,
                    request=input_data,
                    response=result,
                )
            except Exception as e:
                logger.error(f"[SVIM] Failed to log interaction in Postgres: {e}")

        return result


# ==================== Factory Function ====================

def create_svim_agent(
    config: Optional[Dict[str, Any]] = None,
    db_session: Optional[Session] = None,
) -> SVIMAgent:
    """
    Factory para criar a instância do agente SVIM.
    """
    default_config = {
        "max_context_messages": 10,
        "fallback_threshold": 3,
        "circuit_breaker_timeout": 60,
        "cache_ttl": 300,
    }

    if config:
        default_config.update(config)

    return SVIMAgent(default_config, db_session=db_session)
