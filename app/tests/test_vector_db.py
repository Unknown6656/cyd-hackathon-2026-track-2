import logging
from unittest.mock import MagicMock

import pytest

from qdrant_client import models
from qdrant_client.models import QueryResponse, VectorParams

from app.vector_db import VectorDB


def make_db() -> tuple[VectorDB, MagicMock]:
    # Skip __init__ so no real QdrantClient / connection is created.
    db = VectorDB.__new__(VectorDB)
    db.client = MagicMock()
    db.log = logging.getLogger(__name__)
    return db, db.client


def test_create_collection_creates_when_missing() -> None:
    db, client = make_db()
    client.collection_exists.return_value = False

    db.create_collection("col", 128)

    client.create_collection.assert_called_once_with(
        "col",
        vectors_config=VectorParams(size=128, distance=models.Distance.COSINE),
    )


def test_create_collection_is_noop_when_existing() -> None:
    db, client = make_db()
    client.collection_exists.return_value = True

    db.create_collection("col", 128)

    client.create_collection.assert_not_called()


def test_delete_collection_raises_when_missing() -> None:
    db, client = make_db()
    client.collection_exists.return_value = False

    with pytest.raises(RuntimeError, match="Collection does not exist"):
        db.delete_collection("col")

    client.delete_collection.assert_not_called()


def test_delete_collection_deletes_when_existing() -> None:
    db, client = make_db()
    client.collection_exists.return_value = True

    db.delete_collection("col")

    client.delete_collection.assert_called_once_with("col")


def test_add_vector_upserts_single_point() -> None:
    db, client = make_db()

    db.add_vector([0.1, 0.2], {"text": "hello"}, "col")

    client.upsert.assert_called_once()
    _, kwargs = client.upsert.call_args
    assert kwargs["collection_name"] == "col"
    assert len(kwargs["points"]) == 1
    point = kwargs["points"][0]
    assert point.vector == [0.1, 0.2]
    assert point.payload == {"text": "hello"}


def test_search_raises_when_collection_missing() -> None:
    db, client = make_db()
    client.collection_exists.return_value = False

    with pytest.raises(RuntimeError, match="Collection does not exist"):
        db.search([0.1], "col")

    client.query_points.assert_not_called()


def test_search_returns_client_results() -> None:
    db, client = make_db()
    client.collection_exists.return_value = True
    expected: QueryResponse = MagicMock(spec=QueryResponse)
    client.query_points.return_value = expected

    result = db.search([0.1, 0.2], "col", limit=5)

    client.query_points.assert_called_once_with(
        collection_name="col",
        query=[0.1, 0.2],
        limit=5,
    )
    assert result is expected
