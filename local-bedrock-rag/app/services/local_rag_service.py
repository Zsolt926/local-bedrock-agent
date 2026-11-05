import hashlib
from pathlib import Path
import httpx
from app.core.config import get_settings
from app.infrastructure.local_vector_store import LocalVectorStore


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = end - overlap
    return chunks


class LocalRagService:
    def __init__(self):
        self.settings = get_settings()
        self.store = LocalVectorStore()

    def _embed(self, texts: list[str]) -> list[list[float]]:
        response = httpx.post(
            f"{self.settings.ollama_base_url.rstrip('/')}/api/embed",
            json={"model": self.settings.ollama_embed_model, "input": texts},
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["embeddings"]

    def index_directory(self, directory: str) -> dict:
        root = Path(directory)
        if not root.exists():
            raise FileNotFoundError(root)
        ids, docs, metadatas = [], [], []
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
                continue
            text = path.read_text(encoding="utf-8")
            for index, chunk in enumerate(
                chunk_text(text, self.settings.chunk_size, self.settings.chunk_overlap)
            ):
                stable_id = hashlib.sha256(
                    f"{path.resolve()}:{index}:{chunk}".encode()
                ).hexdigest()
                ids.append(stable_id)
                docs.append(chunk)
                metadatas.append({
                    "source": str(path),
                    "filename": path.name,
                    "chunk_index": index,
                })
        embeddings = self._embed(docs) if docs else []
        self.store.upsert(ids, docs, embeddings, metadatas)
        return {"indexed_chunks": len(ids), "collection_count": self.store.count()}

    def search(self, query: str) -> list[dict]:
        embedding = self._embed([query])[0]
        return self.store.query(embedding, self.settings.top_k)
