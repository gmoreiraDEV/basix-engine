from .schedule import criar_agendamento
from .professionals import listar_profissionais, listar_servicos_profissional
from .services import listar_servicos

TOOLS = [criar_agendamento, listar_profissionais, listar_servicos_profissional, listar_servicos]