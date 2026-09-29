import numpy as np
from fastembed import TextEmbedding

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

class SessionVectorStore:
    """
    Small in-memory vector store for a public Streamlit demo.
    Every Streamlit session receives its own instance.
    """

    def __init__(self):
        self.embedder = None
        self.chunks = []
        self.matrix = None

    def _get_embedder(self):
        if self.embedder is None:
            self.embedder = TextEmbedding(model_name=_MODEL_NAME)
        return self.embedder

    def add_chunks(self, chunks):
        self.chunks = list(chunks)
        embedder = self._get_embedder()
        vectors = list(embedder.embed([chunk["text"] for chunk in self.chunks]))
        matrix = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        self.matrix = matrix / np.maximum(norms, 1e-12)

    def search(self, query: str, limit: int = 5):
        if self.matrix is None or not self.chunks:
            return []

        embedder = self._get_embedder()
        query_vector = np.asarray(list(embedder.embed([query]))[0], dtype=np.float32)
        query_vector /= max(float(np.linalg.norm(query_vector)), 1e-12)

        scores = self.matrix @ query_vector
        top_indices = np.argsort(scores)[::-1][:limit]

        return [
            {
                "text": self.chunks[i]["text"],
                "score": float(scores[i]),
                "source": self.chunks[i]["source"],
                "chunk_id": self.chunks[i]["id"],
            }
            for i in top_indices
        ]
