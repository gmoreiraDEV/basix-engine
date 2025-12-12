import pytest

from agents.resolvers.service import resolve_service


def test_resolve_service_prefers_haircut_over_other_categories():
    services_list = [
        {"id": 1, "nome": "Depilação perna", "categoria": "Depilação"},
        {"id": 2, "nome": "Corte Masculino", "categoria": "Cabelo", "duracaoEmMinutos": 40},
    ]

    resolved = resolve_service("quero cortar meu cabelo", professional_id=None, services_list=services_list)

    assert resolved
    assert resolved["id"] == 2
    assert "corte" in resolved["nome"].lower()
