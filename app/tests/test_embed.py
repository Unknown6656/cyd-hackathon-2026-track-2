import asyncio
import math

from app.config import settings
from app.embed import EmbeddingModel


def make_model() -> EmbeddingModel:
    return EmbeddingModel(
        f"{settings.openai_base_url}/embeddings",
        settings.embedding_model,
        settings.openai_api_key,
    )


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b)


def test_embed_returns_vector() -> None:
    model = make_model()

    embedding = asyncio.run(model.embed("hello world"))

    assert isinstance(embedding, list)
    assert len(embedding) == settings.vector_size
    assert all(isinstance(x, float) for x in embedding)


def test_embed_is_stable_for_same_text() -> None:
    model = make_model()

    first = asyncio.run(model.embed("the quick brown fox"))
    second = asyncio.run(model.embed("the quick brown fox"))

    # The serving stack is not bit-for-bit deterministic, so compare
    # similarity instead of exact equality.
    assert cosine(first, second) > 0.999


def test_embed_differs_for_different_text() -> None:
    model = make_model()

    fox = asyncio.run(model.embed("the quick brown fox"))
    wine = asyncio.run(model.embed("a glass of red wine"))

    assert cosine(fox, wine) < 0.999
