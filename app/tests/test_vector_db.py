import uuid

import pytest

from app.config import settings
from app.vector_db import VectorDB

VECTOR_SIZE = settings.vector_size


def make_vector(dim: int = 0, fill: float = 1.0) -> list[float]:
    vector = [0.0] * VECTOR_SIZE
    vector[dim] = fill
    return vector


@pytest.fixture()
def db() -> VectorDB:
    return VectorDB(settings.qdrant_url, None)


@pytest.fixture()
def collection(db: VectorDB) -> str:
    name = f"pytest-{uuid.uuid4().hex[:12]}"
    db.create_collection(name, VECTOR_SIZE)
    yield name
    if db.client.collection_exists(name):
        db.delete_collection(name)


def test_create_collection_creates_when_missing(db: VectorDB, collection: str) -> None:
    assert db.client.collection_exists(collection)


def test_create_collection_is_idempotent(db: VectorDB, collection: str) -> None:
    db.create_collection(collection, VECTOR_SIZE)


def test_delete_collection_removes_existing(db: VectorDB, collection: str) -> None:
    db.delete_collection(collection)

    assert not db.client.collection_exists(collection)


def test_add_and_search_returns_inserted_vector(db: VectorDB, collection: str) -> None:
    vector = make_vector(dim=0)

    db.add_vector(vector, {"text": "hello"}, collection)

    result = db.search(vector, collection, limit=1)

    assert len(result.points) == 1
    point = result.points[0]
    assert point.payload == {"text": "hello"}
    assert point.score == pytest.approx(1.0)


def test_filter_for_category_returns_matching_record(db: VectorDB, collection: str) -> None:
    db.add_vector(make_vector(dim=0), {"category": "fruit", "name": "apple"}, collection)
    db.add_vector(make_vector(dim=1), {"category": "vegetable", "name": "carrot"}, collection)

    result = db.filter_for_category("category", "fruit", collection)

    assert len(result) == 1
    assert result[0].payload == {"category": "fruit", "name": "apple"}
    assert result[0].vector == make_vector(dim=0)


def test_filter_for_category_returns_empty_when_no_match(db: VectorDB, collection: str) -> None:
    db.add_vector(make_vector(dim=0), {"category": "fruit", "name": "apple"}, collection)

    assert db.filter_for_category("category", "drink", collection) == []


def test_search_ranks_closest_vector_first(db: VectorDB, collection: str) -> None:
    vector_a = make_vector(dim=0)
    vector_b = make_vector(dim=1)

    db.add_vector(vector_a, {"which": "a"}, collection)
    db.add_vector(vector_b, {"which": "b"}, collection)

    result = db.search(vector_b, collection, limit=2)

    assert [point.payload["which"] for point in result.points] == ["b", "a"]
