import os
from typing import Any, Dict, List
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
    ) -> str:
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
