import requests
from rich import print
from langchain.tools import tool
import os
from dotenv import load_dotenv

load_dotenv()
X_API_TOKEN = os.getenv("X_API_TOKEN")
ESTABELECIMENTO_ID = os.getenv("ESTABELECIMENTO_ID")
URL_BASE = os.getenv("URL_BASE")

headers = {
    'X-Api-Key': X_API_TOKEN,
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'estabelecimentoId': ESTABELECIMENTO_ID
}


@tool
def criar_agendamento(servicoId: int, clienteId: int, profissionalId: int, dataHoraInicio: str, duracaoEmMinutos: int, valor: int, observacoes: str, confirmado: bool) -> dict | str:
    """
    Tool: Agendamento
    Descrição: Agenda um horário usando a API Trinks.

    Args:
        servicoId (int): O ID do serviço.
        clienteId (int): O ID do cliente.
        profissionalId (int): O ID do profissional.
        dataHoraInicio (str): A data e hora de início do agendamento (ex: "AAAA-MM-DDTHH:MM:SS").
        duracaoEmMinutos (int): A duração do agendamento em minutos.
        valor (int): O valor do agendamento.
        observacoes (str): Quaisquer observações ou notas para o agendamento.
        confirmado (bool): Um booleano indicando se o agendamento está confirmado.

    Returns:
        dict: Um dicionário contendo os detalhes do agendamento se bem-sucedido,
              ou uma mensagem de erro se o agendamento falhar.
    """


    payload = {
        "servicoId": servicoId, 
        "clienteId": clienteId, 
        "profissionalId": profissionalId, 
        "dataHoraInicio": dataHoraInicio, 
        "duracaoEmMinutos": duracaoEmMinutos, 
        "valor": valor,
        "observacoes": observacoes, 
        "confirmado": confirmado 
    }

    try:
        response = requests.post(f"{URL_BASE}/agendamentos", headers, json=payload)
        response.raise_for_status() 
        print("Agendamento realizado com sucesso:", response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao tentar realizar agendamento: {e}")
        return {"error": str(e)}


@tool
def listar_agendamentos(dataInicio: str, dataFim: str, clienteId: int = None) -> dict | str:
    """
    Tool: Listar Agendamentos
    Descrição: Lista os agendamentos usando a API Trinks.

    Args:
        dataInicio (str): A data de início para filtrar agendamentos (ex: "AAAA-MM-DD").
        dataFim (str): A data de fim para filtrar agendamentos (ex: "AAAA-MM-DD").
        clienteId (int, optional): O ID do cliente para filtrar agendamentos.

    Returns:
        dict: Um dicionário contendo os detalhes dos agendamentos se bem-sucedido,
              ou uma mensagem de erro se a listagem falhar.
    """

    params = {
        "page": 1,
        "pageSize": 50,
        "dataInicio": dataInicio,
        "dataFim": dataFim
    }
    if clienteId is not None:
        params["clienteId"] = clienteId

    try:
        response = requests.get(f"{URL_BASE}/agendamentos", headers, params)
        response.raise_for_status() 
        print("Agendamentos listados com sucesso:", response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao tentar listar agendamentos: {e}")
        return {"error": str(e)}

        
