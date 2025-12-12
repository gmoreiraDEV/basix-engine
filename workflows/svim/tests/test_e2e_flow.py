import asyncio

import pytest

from agents.maria import SVIMAgent, SVIMIntent
from agents.resolvers.customer import resolve_cliente_id
from agents.tools import index as tools_index


@pytest.mark.asyncio
async def test_full_flow_injects_cliente_and_resolves_service(monkeypatch):
    # Fixtures
    professionals = [{"id": 664608, "nome": "Beatrice Zuppo Pardini"}]
    services = [
        {"id": 10, "nome": "Depilação", "categoria": "Depilação"},
        {
            "id": 20,
            "nome": "Corte Feminino",
            "categoria": "Cabelo",
            "duracaoEmMinutos": 50,
            "valor": 150,
            "profissionalId": 664608,
        },
    ]

    async def fake_listar_profissionais_tool(page: int = 1, pageSize: int = 50):
        return {"data": professionals}

    async def fake_listar_servicos_profissional_tool(profissionalId: int, page: int = 1, pageSize: int = 50):
        assert profissionalId == 664608
        return {"data": services}

    captured_payload = {}

    async def fake_criar_agendamento_tool(args, state):
        cliente_id = resolve_cliente_id(state)
        captured_payload["args"] = args
        captured_payload["clienteId"] = cliente_id
        return {"ok": True, "clienteId": cliente_id, "args": args}

    # Patch tools in registry
    for tool in tools_index.TOOLS:
        if tool["name"] == "listar_profissionais":
            tool["py_fn"] = fake_listar_profissionais_tool
        if tool["name"] == "listar_servicos_profissional":
            tool["py_fn"] = fake_listar_servicos_profissional_tool
        if tool["name"] == "criar_agendamento":
            tool["py_fn"] = fake_criar_agendamento_tool

    call_counter = {"count": 0}

    async def fake_chat_completion(messages, system_prompt="", tools=None, **kwargs):
        call_counter["count"] += 1
        if tools is None:
            return {"intent": "schedule"}

        # First scheduling call triggers criar_agendamento
        if call_counter["count"] == 2:
            return {
                "tool": {
                    "id": "call-1",
                    "name": "criar_agendamento",
                    "arguments": {"confirmado": True, "dataHoraInicio": "2025-01-06T18:00:00"},
                }
            }
        return "Agendamento criado"

    monkeypatch.setenv("URL_BASE", "http://testserver")
    monkeypatch.setenv("X_API_TOKEN", "token")
    monkeypatch.setenv("ESTABELECIMENTO_ID", "1")

    class DummyCollections:
        collections = []

    class DummyQdrant:
        def get_collections(self):
            return DummyCollections()

        def upsert(self, *args, **kwargs):
            return None

        def scroll(self, *args, **kwargs):
            return [], None

        def create_collection(self, *args, **kwargs):
            return None

        def create_payload_index(self, *args, **kwargs):
            return None

    monkeypatch.setattr("agents.maria.create_qdrant_client", lambda config=None: DummyQdrant())
    monkeypatch.setattr("agents.maria.ensure_qdrant_collection", lambda *args, **kwargs: None)

    agent = SVIMAgent()
    monkeypatch.setattr(agent.llm_client, "chat_completion", fake_chat_completion)

    state = {
        "messages": [
            {"role": "user", "content": "oi, quero cortar meu cabelo"},
            {"role": "assistant", "content": "claro"},
            {"role": "user", "content": "pode ser com a Beatrice"},
            {"role": "assistant", "content": "ok"},
            {"role": "user", "content": "segunda às 18h"},
            {"role": "assistant", "content": "perfeito"},
            {"role": "user", "content": "pode confirmar"},
        ],
        "user_id": "9999",
        "session_id": "sess-1",
        "intent": SVIMIntent.SCHEDULE,
        "customer_profile": {"id": 555, "name": "Cliente"},
        "appointment_context": {},
        "policies_context": {},
        "needs_handoff": False,
        "finish_session": False,
        "system_prompt": "",
        "tool_attempts": {},
    }

    result_state = await agent._generate_response(state)

    assert captured_payload.get("clienteId") == 555
    args = captured_payload.get("args") or {}
    assert args.get("servicoId") == 20
    assert args.get("profissionalId") == 664608
    assert args.get("dataHoraInicio") == "2025-01-06T18:00:00"
    assert result_state["appointment_context"]["appointment_draft"]["serviceId"] == 20
    assert result_state["appointment_context"]["appointment_draft"]["professionalId"] == 664608
