from httpx import Client, AsyncClient

# The first call may cold-load the embedding model, so allow a generous
# budget instead of httpx's 5s default.
_EMBED_TIMEOUT = 120.0


class EmbeddingModel:

    def __init__(self, base_url: str, model_name: str, api_key: str | None):
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key

    def embed(self, text: str):
        with Client(timeout=_EMBED_TIMEOUT) as aclient:
            response = aclient.post(
                self.base_url,
                json={"model": self.model_name, "input": text},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]

    async def async_embed(self, text: str):
        async with AsyncClient(timeout=_EMBED_TIMEOUT) as aclient:
            response = await aclient.post(
                self.base_url,
                json={"model": self.model_name, "input": text},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
