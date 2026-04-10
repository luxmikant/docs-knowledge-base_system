"""Embedding service for semantic search using sentence-transformers and FAISS."""

import hashlib
import os
import pickle
import re
from pathlib import Path

import numpy as np
from django.conf import settings

try:
    import faiss  # type: ignore

    FAISS_AVAILABLE = True
except Exception:
    faiss = None
    FAISS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None


class NumpyIndexFlatIP:
    """Minimal FAISS-like inner-product index fallback powered by NumPy."""

    def __init__(self, dimension):
        self.dimension = dimension
        self.vectors = np.empty((0, dimension), dtype=np.float32)

    @property
    def ntotal(self):
        return self.vectors.shape[0]

    def add(self, vectors):
        vectors = np.asarray(vectors, dtype=np.float32)
        if vectors.ndim != 2 or vectors.shape[1] != self.dimension:
            raise ValueError('Invalid vector shape for index add operation.')
        self.vectors = np.vstack([self.vectors, vectors])

    def search(self, query_vectors, k):
        query_vectors = np.asarray(query_vectors, dtype=np.float32)
        if self.ntotal == 0:
            return np.zeros((query_vectors.shape[0], 0), dtype=np.float32), np.zeros((query_vectors.shape[0], 0), dtype=np.int64)

        similarities = np.matmul(query_vectors, self.vectors.T)
        k = min(k, self.ntotal)
        sorted_indices = np.argsort(-similarities, axis=1)[:, :k]
        sorted_scores = np.take_along_axis(similarities, sorted_indices, axis=1)
        return sorted_scores.astype(np.float32), sorted_indices.astype(np.int64)


class EmbeddingService:
    """Service for generating and managing document embeddings."""

    def __init__(self):
        self.dimension = 384
        self.index = self._new_index()
        self.doc_id_map = {}
        self.model = None
        self.using_fallback = False
        self.load_index()
        self._initialize_model()

    def _new_index(self):
        return faiss.IndexFlatIP(self.dimension) if FAISS_AVAILABLE else NumpyIndexFlatIP(self.dimension)

    def _initialize_model(self):
        """Initialize sentence-transformer model with graceful fallback."""
        if os.getenv('DISABLE_TRANSFORMER_MODEL', 'False').lower() == 'true':
            self.model = None
            self.using_fallback = True
            return

        if SentenceTransformer is None:
            self.model = None
            self.using_fallback = True
            return

        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception:
            # Keep semantic search available even when model download/init fails.
            self.model = None
            self.using_fallback = True

    @staticmethod
    def _normalize_text(text):
        if not text:
            return ''
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _fallback_embedding(self, text):
        """Generate deterministic normalized embedding without external model access."""
        vector = np.zeros(self.dimension, dtype=np.float32)
        tokens = re.findall(r'\w+', text.lower())

        if not tokens:
            vector[0] = 1.0
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode('utf-8')).digest()
            index = int.from_bytes(digest[:4], byteorder='big') % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = np.linalg.norm(vector)
        if norm == 0:
            vector[0] = 1.0
            return vector
        return (vector / norm).astype(np.float32)

    def generate_embedding(self, text):
        """Generate a 384-dimensional normalized embedding for text."""
        normalized_text = self._normalize_text(text)
        if not normalized_text:
            normalized_text = 'empty'

        if self.model is not None:
            embedding = self.model.encode(normalized_text, normalize_embeddings=True)
            return np.asarray(embedding, dtype=np.float32)

        return self._fallback_embedding(normalized_text)

    def add_document(self, doc_id, text):
        """Add a document embedding to the FAISS index."""
        embedding = self.generate_embedding(text)
        self.index.add(np.asarray([embedding], dtype=np.float32))
        idx = self.index.ntotal - 1
        self.doc_id_map[idx] = doc_id
        self.save_index()

    def reset_index(self):
        """Reset in-memory index and mapping."""
        self.index = self._new_index()
        self.doc_id_map = {}

    def rebuild_index(self, doc_id_and_text):
        """Rebuild index from a sequence of (doc_id, text) tuples."""
        self.reset_index()

        if not doc_id_and_text:
            self.save_index()
            return

        embeddings = []
        document_ids = []
        for doc_id, text in doc_id_and_text:
            embeddings.append(self.generate_embedding(text or ''))
            document_ids.append(doc_id)

        self.index.add(np.asarray(embeddings, dtype=np.float32))
        self.doc_id_map = {idx: doc_id for idx, doc_id in enumerate(document_ids)}
        self.save_index()

    def search(self, query, top_k=5):
        """Search for semantically similar documents."""
        if self.index.ntotal == 0:
            return []

        top_k = max(1, int(top_k))
        query_embedding = self.generate_embedding(query)
        search_k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(np.asarray([query_embedding], dtype=np.float32), search_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx in self.doc_id_map:
                results.append(
                    {
                        'doc_id': self.doc_id_map[idx],
                        'score': float(score),
                    }
                )
        return results

    def save_index(self):
        """Persist FAISS index and vector mapping to disk."""
        index_dir = Path(settings.FAISS_INDEX_PATH)
        os.makedirs(index_dir, exist_ok=True)

        if FAISS_AVAILABLE:
            faiss.write_index(self.index, str(index_dir / 'faiss_index.bin'))
        else:
            with open(index_dir / 'numpy_index.pkl', 'wb') as index_file:
                pickle.dump(self.index.vectors, index_file)

        with open(index_dir / 'doc_id_map.pkl', 'wb') as map_file:
            pickle.dump(self.doc_id_map, map_file)

    def load_index(self):
        """Load FAISS index and vector mapping from disk if available."""
        index_dir = Path(settings.FAISS_INDEX_PATH)
        index_path = index_dir / 'faiss_index.bin'
        numpy_index_path = index_dir / 'numpy_index.pkl'
        map_path = index_dir / 'doc_id_map.pkl'

        if os.path.exists(map_path):
            with open(map_path, 'rb') as map_file:
                self.doc_id_map = pickle.load(map_file)

        if FAISS_AVAILABLE and os.path.exists(index_path):
            self.index = faiss.read_index(str(index_path))
        elif (not FAISS_AVAILABLE) and os.path.exists(numpy_index_path):
            with open(numpy_index_path, 'rb') as index_file:
                vectors = pickle.load(index_file)
            fallback_index = NumpyIndexFlatIP(self.dimension)
            if vectors is not None and len(vectors) > 0:
                fallback_index.add(vectors)
            self.index = fallback_index


# Global instance
embedding_service = EmbeddingService()
