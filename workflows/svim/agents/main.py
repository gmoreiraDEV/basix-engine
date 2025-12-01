import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from tools.index import tools

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=1,
    api_key=OPENAI_API_KEY,
)


system_prompt = """
Você é uma recepcionista na SVIM PAMPLONA, seu objetivo é captar informações do cliente e criar uma agendamento de horário para ele.
Use a ferramenta create_schedule para criar a agenda assim que conseguir todos os dados.
Você é uma mulher simpática e proativa então sempre tenha essa personalidade.
"""


agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
)


def main():
    print("Agente LangGraph + OPENAI + Tools iniciado. Digite 'sair' para encerrar.\n")

    while True:
        user_input = input("Você: ").strip()
        if not user_input:
            continue

        if user_input.lower() in {"sair", "exit", "quit"}:
            print("Encerrando...")
            break

        result = agent.invoke(
            {"messages": [HumanMessage(content=user_input)]}
        )

        ai_message = result["messages"][-1]
        print(f"Agente: {ai_message.content}\n")


if __name__ == "__main__":
    main()
