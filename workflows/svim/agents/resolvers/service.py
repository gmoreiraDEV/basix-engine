import re
from typing import Any, Dict, List, Optional


EXCLUDED_CATEGORIES = {"depil", "manicure", "podologia", "unha"}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def _intent_from_query(query: str) -> Optional[str]:
    q = _normalize(query)
    corte_tokens = ["corte", "cortar", "cabelo", "haircut", "barba e cabelo"]
    if any(tok in q for tok in corte_tokens):
        return "CORTE"
    return None


def resolve_service(query: str, professional_id: Optional[int], services_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Resolve determinísticamente o serviço a partir de uma lista.

    1) Detecta intenção básica (ex: CORTE)
    2) Filtra serviços por tokens/intent
    3) Exclui categorias incompatíveis
    """

    intent = _intent_from_query(query)
    normalized_query = _normalize(query)

    def is_valid(service: Dict[str, Any]) -> bool:
        name = _normalize(service.get("nome") or service.get("name"))
        categoria = _normalize(service.get("categoria") or "")
        if any(cat in categoria for cat in EXCLUDED_CATEGORIES):
            return False
        if intent == "CORTE":
            return "corte" in name or "cabelo" in name
        return True

    candidates = [s for s in services_list if is_valid(s)]

    if not candidates:
        return None

    # ordena por similaridade simples ao termo "corte" quando aplicável
    if intent == "CORTE":
        candidates.sort(key=lambda s: 0 if "corte" in _normalize(s.get("nome") or s.get("name")) else 1)

    # se profissionalId informado, prioriza serviços vinculados
    if professional_id is not None:
        for svc in candidates:
            if svc.get("profissionalId") == professional_id:
                return svc

    return candidates[0]


def resolve_professional(query: str, professionals_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    normalized_query = _normalize(query)
    if not normalized_query:
        return None

    def normalize_name(prof: Dict[str, Any]) -> str:
        return _normalize(prof.get("nome") or prof.get("name"))

    # match direto
    for prof in professionals_list:
        if normalize_name(prof) in normalized_query or prof.get("apelido") and _normalize(prof.get("apelido")) in normalized_query:
            return prof

    # match parcial por palavras
    for prof in professionals_list:
        name = normalize_name(prof)
        tokens = name.split()
        if any(tok and tok in normalized_query for tok in tokens):
            return prof

    return None
