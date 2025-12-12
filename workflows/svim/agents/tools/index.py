from .professionals import listar_profissionais_tool, listar_servicos_profissional_tool
from .services import listar_servicos_tool
from .schedule import criar_agendamento_tool, listar_agendamentos_tool

TOOLS = [
    {
        "name": "listar_profissionais",
        "description": "Lista os profissionais do estabelecimento SVIM/Trinks.",
        "parameters": {
            "type": "object",
            "properties": {
                "page": {
                    "type": "integer",
                    "description": "Número da página (1 em diante).",
                    "default": 1,
                },
                "pageSize": {
                    "type": "integer",
                    "description": "Quantidade de registros por página.",
                    "default": 50,
                },
            },
            "required": [],
        },
        "py_fn": listar_profissionais_tool,
    },
    {
        "name": "listar_servicos_profissional",
        "description": "Lista os serviços de um profissional específico.",
        "parameters": {
            "type": "object",
            "properties": {
                "profissionalId": {
                    "type": "integer",
                    "description": "ID do profissional no Trinks.",
                },
                "page": {
                    "type": "integer",
                    "description": "Número da página (1 em diante).",
                    "default": 1,
                },
                "pageSize": {
                    "type": "integer",
                    "description": "Quantidade de registros por página.",
                    "default": 50,
                },
            },
            "required": ["profissionalId"],
        },
        "py_fn": listar_servicos_profissional_tool,
    },
    {
        "name": "listar_servicos",
        "description": "Lista serviços disponíveis para agendamento.",
        "parameters": {
            "type": "object",
            "properties": {
                "nome": {
                    "type": ["string", "null"],
                    "description": "Filtro pelo nome do serviço.",
                },
                "categoria": {
                    "type": ["string", "null"],
                    "description": "Categoria do serviço (ex: cabelo, unha).",
                },
                "somenteVisiveisCliente": {
                    "type": ["boolean", "null"],
                    "description": "Se True, apenas serviços visíveis aos clientes.",
                },
            },
            "required": [],
        },
        "py_fn": listar_servicos_tool,
    },
    {
        "name": "criar_agendamento",
        "description": "Cria um agendamento real no Trinks.",
        "parameters": {
            "type": "object",
            "properties": {
                "servicoId": {"type": "integer", "description": "ID do serviço."},
                "profissionalId": {"type": "integer", "description": "ID do profissional."},
                "dataHoraInicio": {
                    "type": "string",
                    "description": "Data/hora início no formato ISO (ex: 2025-12-10T15:00:00).",
                },
                "duracaoEmMinutos": {
                    "type": "integer",
                    "description": "Duração do atendimento em minutos.",
                },
                "valor": {
                    "type": "integer",
                    "description": "Valor do serviço (unidade interna do sistema).",
                },
                "observacoes": {
                    "type": "string",
                    "description": "Observações adicionais para o agendamento.",
                },
                "confirmado": {
                    "type": "boolean",
                    "description": "Se o agendamento já deve ser criado como confirmado.",
                },
            },
            "required": [
                "servicoId",
                "profissionalId",
                "dataHoraInicio",
                "duracaoEmMinutos",
                "valor",
                "observacoes",
                "confirmado",
            ],
        },
        "py_fn": criar_agendamento_tool,
    },
    {
        "name": "listar_agendamentos",
        "description": "Lista agendamentos em um intervalo de datas.",
        "parameters": {
            "type": "object",
            "properties": {
                "dataInicio": {
                    "type": "string",
                    "description": "Data de início (YYYY-MM-DD).",
                },
                "dataFim": {
                    "type": "string",
                    "description": "Data de fim (YYYY-MM-DD).",
                },
                "clienteId": {
                    "type": ["integer", "null"],
                    "description": "ID do cliente, se quiser filtrar por cliente.",
                },
            },
            "required": ["dataInicio", "dataFim"],
        },
        "py_fn": listar_agendamentos_tool,
    },
]
