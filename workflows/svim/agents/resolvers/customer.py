from typing import Any, Dict, Optional, Union


def resolve_cliente_id(state: Dict[str, Any]) -> Optional[Union[int, str]]:
    """Resolve o clienteId a partir do estado compartilhado.

    Prioridade:
    1. customer_profile.id
    2. appointment_context.customerId
    3. user_id (somente se numérico)
    """

    customer_profile = state.get("customer_profile", {}) if state else {}
    appointment_context = state.get("appointment_context", {}) if state else {}

    if customer_profile.get("id") is not None:
        return customer_profile.get("id")

    if appointment_context.get("customerId") is not None:
        return appointment_context.get("customerId")

    user_id = state.get("user_id") if state else None
    if isinstance(user_id, (int, float)):
        return int(user_id)
    if isinstance(user_id, str) and user_id.isdigit():
        return int(user_id)

    return None
