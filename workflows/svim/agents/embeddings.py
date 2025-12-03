import os
from openai import OpenAI

class EmbeddingClient:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def embed(self, text: str) -> list:
        """
        Retorna o vetor de embedding do OpenAI (text-embedding-3-small).
        """
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
