from qdrant_client import QdrantClient, models
from qdrant_client.models import QueryResponse, VectorParams, PointStruct

import uuid
import logging


class VectorDB:

    def __init__(self, base_url: str, api_key: str):
        self.client = QdrantClient(
            url=base_url, 
            api_key=api_key
        )
        self.log = logging.getLogger(__name__)

    def create_collection(self, collection_name: str, vector_size: int) -> None:
        if self._collection_exists(collection_name):
            self.log.debug(f"Collection {collection_name} already exists.")
            return
        self.client.create_collection(
            collection_name, 
            vectors_config=VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            )
        )
        self.log.info(f"Collection {collection_name} with vector dim {vector_size} created.")

    def delete_collection(self, collection_name: str) -> None:
        if not self._collection_exists(collection_name):
            raise RuntimeError("Collection does not exist")
        self.client.delete_collection(collection_name)

    def add_vector(self, vector: list[float], payload: dict | None, collection_name: str) -> None:
        point_structs = [
            PointStruct(
                id = uuid.uuid4(),
                vector = vector,
                payload = payload,
            )
        ]
        
        self.client.upsert(
            collection_name=collection_name,
            points=point_structs,
        )

    def search(self, search_vector: list[float], collection_name: str, limit: int = 1) -> QueryResponse:
        if not self._collection_exists(collection_name):
            raise RuntimeError("Collection does not exist!")

        search_results = self.client.query_points(
            collection_name=collection_name,
            query=search_vector,
            limit=limit,
        )
        return search_results

    def _collection_exists(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name)
        