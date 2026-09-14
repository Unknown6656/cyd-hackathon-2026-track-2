from openai import AsyncOpenAI

class EmbeddingModel:

    def __init__(self, base_url: str, model_name: str, api_key: str | None):
        self.model_name = model_name
        self.client = AsyncOpenAI(
             base_url=base_url,
             api_key=api_key,
        )

    async def embed(self, text: str):
        embeddings = await self.client.embeddings.create(
            model=self.model_name,
            input=text,
        )

        return embeddings.data[0].embedding
