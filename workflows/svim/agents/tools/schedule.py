import requests
from langchain.tools import tool
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
def criar_agendamento(
    servicoId: int,
    clienteId: int,
    profissionalId: int,
    dataHoraInicio: str,
    duracaoEmMinutos: int,
    valor: int,
    observacoes: str,
    confirmado: bool,
) -> dict:
    """
    Tool: Agendamento
    Descrição: Cria um agendamento na API Trinks.

    Args:
        servicoId (int): ID do serviço.
        clienteId (int): ID do cliente.
        profissionalId (int): ID do profissional.
        dataHoraInicio (str): Data/hora no formato ISO (ex: "2025-12-10T15:00:00").
        duracaoEmMinutos (int): Duração do atendimento em minutos.
        valor (int): Valor em centavos ou unidades usadas pelo sistema.
        observacoes (str): Observações adicionais.
        confirmado (bool): Se o agendamento já deve ficar confirmado.

    Returns:
        dict: JSON do agendamento criado ou {"error": "..."}.
    """
    payload = {
        "servicoId": servicoId,
        "clienteId": clienteId,
        "profissionalId": profissionalId,
        "dataHoraInicio": dataHoraInicio,
        "duracaoEmMinutos": duracaoEmMinutos,
        "valor": valor,
        "observacoes": observacoes,
        "confirmado": confirmado,
    }

    try:
        response = requests.post(
            f"{URL_BASE}/agendamentos",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


@tool
def listar_agendamentos(
    dataInicio: str,
    dataFim: str,
    clienteId: int | None = None,
) -> dict:
    """
    Tool: Listar Agendamentos
    Descrição: Lista agendamentos em um intervalo de datas.

    Args:
        dataInicio (str): Data de início (ex: "2025-12-01").
        dataFim (str): Data de fim (ex: "2025-12-31").
        clienteId (int | None): ID do cliente (opcional).

    Returns:
        dict: JSON com a lista de agendamentos ou {"error": "..."}.
    """
    params: dict[str, Any] = {
        "page": 1,
        "pageSize": 50,
        "dataInicio": dataInicio,
        "dataFim": dataFim,
    }
    if clienteId is not None:
        params["clienteId"] = clienteId

    try:
        response = requests.get(
            f"{URL_BASE}/agendamentos",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
