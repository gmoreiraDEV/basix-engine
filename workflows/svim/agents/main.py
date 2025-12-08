import os
import json
import asyncio
import traceback
from typing import Any, Dict
from kestra import Kestra

from agents.maria import create_svim_agent
from agents.infra import create_session_factory

from dotenv import load_dotenv
load_dotenv()


def _load_json_env(name: str) -> Dict[str, Any]:
    raw = os.environ.get(name)
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


async def run_once() -> Dict[str, Any]:
    message = os.environ.get("SVIM_MESSAGE", "").strip()
    user_id = os.environ.get("SVIM_USER_ID", "anonymous")
    session_id = os.environ.get("SVIM_SESSION_ID") or None

    customer_profile = _load_json_env("SVIM_CUSTOMER_PROFILE")
    policies_context = _load_json_env("SVIM_POLICIES_CONTEXT")

    if not message:
        raise ValueError("SVIM_MESSAGE não foi definido nas variáveis de ambiente")

    SessionFactory = create_session_factory()
    db_session = SessionFactory()

    try:
        agent = create_svim_agent(db_session=db_session)

        result = await agent.process(
            {
                "message": message,
                "session_id": session_id,
                "customer_profile": customer_profile,
                "policies_context": policies_context,
            },
            user_id=user_id,
        )

        return result
    finally:
        db_session.close()

def main():
    try:
        result = asyncio.run(run_once())
        Kestra.outputs(result)
        print(json.dumps(result, ensure_ascii=False))

    except Exception as e:
        print("PYTHON_CRASH:", e)
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()