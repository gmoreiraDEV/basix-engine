import asyncio
import json
import sys
from typing import Any, Dict

from agents.maria import create_svim_agent
from agents.infra import create_session_factory


async def run_once(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executa o SVIMAgent uma única vez com o payload informado.
    """
    message = payload["message"]
    user_id = payload.get("user_id", "anonymous")
    session_id = payload.get("session_id")
    customer_profile = payload.get("customer_profile", {})
    appointment_context = payload.get("appointment_context", {})
    policies_context = payload.get("policies_context", {})

    # cria sessão de DB (usa DATABASE_URL do ambiente)
    SessionFactory = create_session_factory()
    db_session = SessionFactory()

    try:
        agent = create_svim_agent(db_session=db_session)

        result = await agent.process(
            {
                "message": message,
                "session_id": session_id,
                "customer_profile": customer_profile,
                "appointment_context": appointment_context,
                "policies_context": policies_context,
            },
            user_id=user_id,
        )

        return result
    finally:
        db_session.close()


async def main():
    # lê JSON da stdin (enviado pelo Kestra)
    raw = sys.stdin.read()
    if not raw.strip():
        raise ValueError("Nenhum payload JSON recebido na stdin")

    payload = json.loads(raw)

    result = await run_once(payload)

    # devolve resultado em JSON (stdout)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
