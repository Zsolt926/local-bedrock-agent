from pathlib import Path
import chromadb
from app.core.config import get_settings


class LocalVectorStore:
    def __init__(self):
        settings = get_settings()
        Path(settings.chroma_path).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=settings.chroma_path)
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, ids: list[str], documents: list[str], embeddings: list[list[float]],
               metadatas: list[dict]) -> None:
        if not ids:
            return
        self.collection.upsert(
            ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas
        )

    def query(self, embedding: list[float], top_k: int) -> list[dict]:
        result = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        rows = []
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        ids = (result.get("ids") or [[]])[0]
        for doc_id, document, metadata, distance in zip(ids, docs, metas, distances):
            rows.append({
                "id": doc_id,
                "text": document,
                "metadata": metadata or {},
                "distance": distance,
            })
        return rows

    def count(self) -> int:
        return self.collection.count()
