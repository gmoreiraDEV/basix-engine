from langchain.tools import tool
from typing import Any, Dict

from agents.http_client import get_http_client


async def listar_profissionais_tool(page: int = 1, pageSize: int = 50) -> dict:
    params = {
        "page": page,
        "pageSize": pageSize,
    }
    client = get_http_client()
    return client.get("/profissionais", params=params)


async def listar_servicos_profissional_tool(
    profissionalId: int,
    page: int = 1,
    pageSize: int = 50,
) -> dict:
    params = {
        "page": page,
        "pageSize": pageSize,
    }
    client = get_http_client()
    return client.get(f"/profissionais/{profissionalId}/servicos", params=params)
