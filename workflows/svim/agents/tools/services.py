from typing import Any, Dict

from agents.http_client import get_http_client


async def listar_servicos_tool(
    nome: str | None = None,
    categoria: str | None = None,
    somenteVisiveisCliente: bool | None = None,
) -> dict:
    params: Dict[str, Any] = {
        "page": 1,
        "pageSize": 50,
    }

    if nome is not None:
        params["nome"] = nome

    if categoria is not None:
        params["categoria"] = categoria

    if somenteVisiveisCliente is not None:
        params["somenteVisiveisCliente"] = bool(somenteVisiveisCliente)

    client = get_http_client()
    return client.get("/servicos", params=params)
