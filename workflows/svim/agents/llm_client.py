import os
import json
from typing import Any, Dict, List, Optional, Union
from openai import OpenAI

class LLMClient:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str = "",
        temperature: float = 0.4,
        max_tokens: int = 350,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str | None = None,
    ) -> Any:
        """
        Suporta:
        - Resposta normal (string)
        - Chamada de ferramenta (dict com {tool: {name, arguments}})
        """

        # ============================
        # 🔧 Pré-processamento
        # ============================
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        # Converter tools para formato OpenAI
        tool_defs = None
        if tools:
            tool_defs = []
            for t in tools:
                tool_defs.append({
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["parameters"]
                    }
                })

        # ============================
        # 🚀 Chamada à API
        # ============================
        resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=full_messages,
            tools=tool_defs,
            tool_choice=(tool_choice or "auto") if tool_defs else None,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        msg = resp.choices[0].message

        # ============================
        # 🧠 1. Se é RESPOSTA NORMAL
        # ============================
        if msg.content:
            return msg.content

        # ============================
        # 🔧 2. Se é UMA TOOL CALL
        # ============================
        if msg.tool_calls:
            tc = msg.tool_calls[0]

            return {
                "tool": {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments)
                }
            }

        # ============================
        # 🛑 Nada retornado?
        # ============================
        return "Desculpe, não consegui entender sua solicitação."
