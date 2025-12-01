import os
import requests
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional
from langchain.tools import tool

load_dotenv()
X_API_TOKEN = os.getenv("X_API_TOKEN")
ESTABELECIMENTO_ID = os.getenv("ESTABELECIMENTO_ID")
URL_BASE = os.getenv("URL_BASE")


@tool
def create_schedule(
    servicoId: int, 
    clienteId: int, 
    profissionalId: int, 
    dataHoraInicio: datetime, 
    duracaoEmMinutos: int, 
    valor: float, 
    observacoes: Optional[str], 
    confirmado: bool
  ):
  """
  Cria um agendamento no sistema.

  Args:
    servicoId (int): ID do serviço que será executado.
    clienteId (int): ID do cliente que está realizando o agendamento.
    profissionalId (int): ID do profissional responsável pelo atendimento.
    dataHoraInicio (datetime): Data e hora de início do agendamento.
    duracaoEmMinutos (int): Duração total do atendimento em minutos.
    valor (float): Valor cobrado pelo serviço.
    observacoes (str | None): Observações adicionais inseridas pelo cliente ou profissional.
    confirmado (bool): Indica se o agendamento já está confirmado (True) ou pendente (False).

  Returns:
    dict: Dados do agendamento criado ou estrutura definida pelo sistema.
  """
  headers = {
    'X-Api-Key': X_API_TOKEN,
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'estabelecimentoId': ESTABELECIMENTO_ID
  }

  payload = {}
  if servicoId:
    payload.servicoId = servicoId
  if clienteId:
    payload.clienteId = clienteId
  if profissionalId:
    payload.profissionalId = profissionalId
  if dataHoraInicio:
    payload.dataHoraInicio = dataHoraInicio
  if duracaoEmMinutos:
    payload.duracaoEmMinutos = duracaoEmMinutos
  if valor:
    payload.valor = valor
  if observacoes:
    payload.observacoes = observacoes
  if confirmado:
    payload.confirmado = confirmado

  response = requests.post(f"{URL_BASE}/agendamentos", headers, data=payload)

  print(f'> Call schedule', response)
  return response