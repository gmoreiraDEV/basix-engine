import requests
from typing import Any, Dict, Optional

from agents.http_client import get_http_client
from agents.resolvers.customer import resolve_cliente_id


async def criar_agendamento_tool(args: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    cliente_id = resolve_cliente_id(state)
    if cliente_id is None:
        return {"error": "CLIENTE_NAO_IDENTIFICADO"}

    required_fields = [
        "servicoId",
        "profissionalId",
        "dataHoraInicio",
        "duracaoEmMinutos",
        "valor",
        "observacoes",
        "confirmado",
    ]
    missing = [field for field in required_fields if field not in args]
    if missing:
        return {"error": "ARGS_INVALIDOS", "missing": missing}

    payload = {
        "servicoId": int(args["servicoId"]),
        "clienteId": cliente_id,
        "profissionalId": int(args["profissionalId"]),
        "dataHoraInicio": args["dataHoraInicio"],
        "duracaoEmMinutos": int(args["duracaoEmMinutos"]),
        "valor": int(args["valor"]),
        "observacoes": args.get("observacoes", ""),
        "confirmado": bool(args.get("confirmado", False)),
    }

    client = get_http_client()
    return client.post("/agendamentos", json=payload)


async def listar_agendamentos_tool(args: Dict[str, Any], state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "page": 1,
        "pageSize": 50,
        "dataInicio": args.get("dataInicio"),
        "dataFim": args.get("dataFim"),
    }
    if args.get("clienteId"):
        params["clienteId"] = args.get("clienteId")

    client = get_http_client()
    return client.get("/agendamentos", params=params)
