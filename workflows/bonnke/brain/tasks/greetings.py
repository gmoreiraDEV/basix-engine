from langgraph.graph import StateGraph, END
from datetime import datetime, UTC
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
import psycopg
import os
from dotenv import load_dotenv
import uuid
import json

# ========== CONFIG ==========
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

llm = ChatOpenAI(
    model="gpt-4.1",
    temperature=0.5,
    api_key=OPENAI_API_KEY
)

# ========== ESTADO DO AGENTE ==========

class BonnkeState(BaseModel):
    user_message: str
    session_id: str | None = None
    phone: str | None = None
    job_id: str | None = None
    state: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    welcome_message: str | None = None


# ========== HELPERS ==========

def save_initial_state(state: BonnkeState):
    """Salva o estado inicial no Postgres."""
    try:
        conn = psycopg.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        print(cur.fetchone())
        
        json_state = json.dumps({"region": state.state}) if state.state else None

        cur.execute("""
            INSERT INTO conversations (
                id, session_id, initial_message, phone, job_id, state, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, (
            str(uuid.uuid4()),
            state.session_id,
            state.user_message,
            state.phone,
            state.job_id,
            json_state
        ))

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Erro ao salvar estado:", e)


# ========== NÓ 1 – Criar estado inicial ==========

def create_initial_state(state: BonnkeState):
    if not state.session_id:
        state.session_id = f"bonnke_{uuid.uuid4()}"
    # Aqui você pode extrair telefone, job… se quiser
    save_initial_state(state)
    return state


# ========== NÓ 2 – Criar mensagem de boas-vindas (persona João) ==========

def generate_welcome_message(state: BonnkeState):

    system_prompt = """
Você é João, atendente da Bonnke Profissional.
Sua missão é fazer o atendimento inicial do cliente.

Regras:
- Sempre responder como um atendente humano, educado e objetivo.
- Nunca gere informação falsa.
- Pergunte pelo número do job ou endereço se o cliente não enviou ainda.
- Nunca informe valores.
- Não use emojis.
- Tom amigável, masculino, direto.

Sempre mantenha humanidade e clareza.
"""

    msg = state.user_message

    ai_response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": msg}
    ])

    state.welcome_message = ai_response.content
    return state


# ========== CONFIGURA O WORKFLOW DO LANGGRAPH ==========

workflow = StateGraph(BonnkeState)

workflow.add_node("create_initial_state", create_initial_state)
workflow.add_node("generate_welcome_message", generate_welcome_message)

workflow.set_entry_point("create_initial_state")
workflow.add_edge("create_initial_state", "generate_welcome_message")
workflow.add_edge("generate_welcome_message", END)

agent = workflow.compile()


# ========== FUNÇÃO PARA O KESTRA CHAMAR ==========

def run(user_message: str, phone: str | None = None, job_id: str | None = None, state_region: str | None = None):
    initial_state = BonnkeState(
        user_message=user_message,
        phone=phone,
        job_id=job_id,
        state=state_region
    )
    final_state = agent.invoke(initial_state)
    return {
        "session_id": final_state["session_id"],
        "welcome_message": final_state["welcome_message"]
    }

if __name__ == "__main__":
    # chame a função passando os parâmetros que ela espera
    resp = run(
        user_message="Olá, tudo bem?",
        phone="5511947315901",
        job_id="1234",
        state_region="São Paulo"
    )
    print(resp)
