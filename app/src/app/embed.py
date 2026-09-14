from httpx import AsyncClient

class EmbeddingModel:

    def __init__(self, base_url: str, model_name: str, api_key: str | None):
        self.model_name = model_name
        self.client = AsyncClient(
            host=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def embed(self, text: str):
        async with AsyncClient() as aclient:
            response = await aclient.post(
                "http://localhost:11434/v1/embeddings",
                json={"model": self.model_name, "input": text},
                headers={"Authorization": "Bearer ollama"}
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
