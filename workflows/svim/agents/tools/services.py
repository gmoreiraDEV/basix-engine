from langchain.tools import tool
import requests
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
def listar_servicos(nome: str | None, categoria: str | None, somenteVisiveisCliente: bool | None) -> dict | str:
    """
    Tool: Listar Servicos
    Descrição: Lista os serviços usando a API Trinks.

    Args:
        nome (str | None): O nome do serviço.
        categoria (str | None): A categoria do serviço.
        somenteVisiveisCliente (bool | None): Um booleano indicando se o serviço deve ser visível para o cliente.

    Returns:
        dict: Um dicionário contendo os detalhes dos serviços se bem-sucedido,
              ou uma mensagem de erro se a listagem falhar.
    """

    params = {
        "page": 1,
        "pageSize": 50
    }

    if nome is not None:
        params["nome"] = nome

    if categoria is not None:
        params["categoria"] = categoria

    if somenteVisiveisCliente is not None:
        params["somenteVisiveisCliente"] = True

    try:
        response = requests.get(f"{URL_BASE}/servicos", headers, params)
        response.raise_for_status() 
        print("Servicos listados com sucesso:", response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao tentar listar servicos: {e}")
        return {"error": str(e)}

   
