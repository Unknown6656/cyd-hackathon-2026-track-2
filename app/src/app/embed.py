from httpx import AsyncClient

class EmbeddingModel:

    def __init__(self, base_url: str, model_name: str, api_key: str | None):
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key

    async def embed(self, text: str):
        async with AsyncClient() as aclient:
            response = await aclient.post(
                self.base_url,
                json={"model": self.model_name, "input": text},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
