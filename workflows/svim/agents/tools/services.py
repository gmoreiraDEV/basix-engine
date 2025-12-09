from langchain.tools import tool
import requests
import os
from dotenv import load_dotenv
from typing import Any

load_dotenv()
X_API_TOKEN = os.getenv("X_API_TOKEN")
ESTABELECIMENTO_ID = os.getenv("ESTABELECIMENTO_ID")
URL_BASE = os.getenv("URL_BASE")

headers = {
    "X-Api-Key": X_API_TOKEN,
    "Accept": "application/json",
    "Content-Type": "application/json",
    "estabelecimentoId": ESTABELECIMENTO_ID,
}


@tool
def listar_servicos(
    nome: str | None = None,
    categoria: str | None = None,
    somenteVisiveisCliente: bool | None = None,
) -> dict:
    """
    Tool: Listar Serviços
    Descrição: Lista serviços disponíveis na API Trinks.

    Args:
        nome (str | None): Filtro pelo nome do serviço.
        categoria (str | None): Categoria do serviço.
        somenteVisiveisCliente (bool | None): Se True, só serviços visíveis ao cliente.

    Returns:
        dict: JSON com serviços ou {"error": "..."}.
    """
    params: dict[str, Any] = {
        "page": 1,
        "pageSize": 50,
    }

    print("listar_servicos", params)

    if nome is not None:
        params["nome"] = nome

    if categoria is not None:
        params["categoria"] = categoria

    if somenteVisiveisCliente is not None:
        params["somenteVisiveisCliente"] = bool(somenteVisiveisCliente)

    try:
        response = requests.get(
            f"{URL_BASE}/servicos",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
