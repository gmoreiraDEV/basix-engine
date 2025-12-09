from langchain.tools import tool
import requests
import os
from dotenv import load_dotenv

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
def listar_profissionais(page: int = 1, pageSize: int = 50) -> dict:
    """
    Tool: Listar Profissionais
    Descrição: Lista os profissionais do estabelecimento.

    Args:
        page (int): Número da página (default 1).
        pageSize (int): Tamanho da página (default 50).

    Returns:
        dict: Resposta JSON da API Trinks, ou {"error": "..."} em caso de erro.
    """
    params = {
        "page": page,
        "pageSize": pageSize,
    }

    print("listar_profissionais", params)

    try:
        response = requests.get(
            f"{URL_BASE}/profissionais",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


@tool
def listar_servicos_profissional(
    profissionalId: int,
    page: int = 1,
    pageSize: int = 50,
) -> dict:
    """
    Tool: Listar Serviços de um Profissional
    Descrição: Lista os serviços de um profissional específico.

    Args:
        profissionalId (int): ID do profissional.
        page (int): Número da página (default 1).
        pageSize (int): Tamanho da página (default 50).

    Returns:
        dict: Resposta JSON da API Trinks, ou {"error": "..."} em caso de erro.
    """
    params = {
        "page": page,
        "pageSize": pageSize,
    }

    print("listar_servicos_profissional", params)

    try:
        response = requests.get(
            f"{URL_BASE}/profissionais/{profissionalId}/servicos",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
