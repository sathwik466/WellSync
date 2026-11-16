import json
import logging
import os
import re

from config import Config

logger = logging.getLogger(__name__)

# Check if FAISS and numpy are available
try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None
    np = None

# Check embedding service availability
try:
    from services.embedding_service import SENTENCE_TRANSFORMERS_AVAILABLE, encode_texts
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    encode_texts = None


class FaissService:
    def __init__(self):
        self.index_path = os.path.join(Config.FAISS_INDEX_PATH, "index.faiss")
        self.chunks_path = os.path.join(Config.FAISS_INDEX_PATH, "chunks.pkl")
        self.meta_path = os.path.join(Config.FAISS_INDEX_PATH, "meta.json")
        self.index = None
        self.chunks: list[str] = []
        self.dimension = 384  # all-MiniLM-L6-v2 output dimension

    def _load_knowledge_base(self) -> list[str]:
        if not os.path.exists(Config.KNOWLEDGE_BASE_PATH):
            return []

        with open(Config.KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        chunks: list[str] = []
        raw_sections = content.split("## Section:")
        for section in raw_sections:
            section = section.strip()
            if not section:
                continue
            lines = section.split("\n", 1)
            title = lines[0].strip().lstrip("#").strip()
            body = lines[1].strip() if len(lines) > 1 else ""

            if not body:
                if title:
                    chunks.append(title)
                continue

            # Split body into natural thematic paragraphs
            paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
            for p in paragraphs:
                chunk_text = f"Topic: {title}\n\n{p}"
                chunks.append(chunk_text)

        if not chunks:
            chunks = [c.strip() for c in content.split("\n\n") if c.strip()]

        return chunks

    def _get_kb_mtime(self) -> float:
        if os.path.exists(Config.KNOWLEDGE_BASE_PATH):
            return os.path.getmtime(Config.KNOWLEDGE_BASE_PATH)
        return 0.0

    def build_index(self):
        self.chunks = self._load_knowledge_base()

        if not FAISS_AVAILABLE or not SENTENCE_TRANSFORMERS_AVAILABLE or encode_texts is None:
            logger.info("FAISS or SentenceTransformers not available. Operating in contextual text search mode.")
            return

        os.makedirs(Config.FAISS_INDEX_PATH, exist_ok=True)

        if not self.chunks:
            self.index = faiss.IndexFlatL2(self.dimension)
            return

        try:
            import pickle
            logger.info(f"Building FAISS vector index with {len(self.chunks)} chunks...")
            embeddings = encode_texts(self.chunks)
            vectors = np.array(embeddings, dtype=np.float32)

            self.index = faiss.IndexFlatL2(self.dimension)
            self.index.add(vectors)

            faiss.write_index(self.index, self.index_path)
            with open(self.chunks_path, "wb") as f:
                pickle.dump(self.chunks, f)

            with open(self.meta_path, "w", encoding="utf-8") as f:
                json.dump({"kb_mtime": self._get_kb_mtime(), "chunk_count": len(self.chunks)}, f)

            logger.info("FAISS index successfully built.")
        except Exception as e:
            logger.warning(f"Could not build FAISS index ({e}). Falling back to text retrieval.")

    def load_index(self):
        self.chunks = self._load_knowledge_base()

        if not FAISS_AVAILABLE or not SENTENCE_TRANSFORMERS_AVAILABLE:
            return

        index_exists = (
            os.path.exists(self.index_path)
            and os.path.exists(self.chunks_path)
            and os.path.exists(self.meta_path)
        )

        if index_exists:
            try:
                import pickle
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                saved_mtime = meta.get("kb_mtime", 0)
                current_mtime = self._get_kb_mtime()

                if abs(current_mtime - saved_mtime) < 1.0:
                    self.index = faiss.read_index(self.index_path)
                    with open(self.chunks_path, "rb") as f:
                        self.chunks = pickle.load(f)
                    return
                else:
                    logger.info("Knowledge base modified. Rebuilding FAISS index...")
            except Exception as e:
                logger.warning(f"Error reading FAISS cache ({e}). Rebuilding...")

        self.build_index()

    def search(self, query: str, top_k: int = 4) -> list[str]:
        if not self.chunks:
            self.load_index()

        if not self.chunks:
            return []

        # 1. Use FAISS vector search if available and loaded
        if FAISS_AVAILABLE and self.index is not None and self.index.ntotal > 0:
            try:
                from services.embedding_service import encode_text
                query_vector = np.array([encode_text(query)], dtype=np.float32)
                distances, indices = self.index.search(query_vector, min(top_k, len(self.chunks)))
                results = []
                for idx in indices[0]:
                    if 0 <= idx < len(self.chunks):
                        results.append(self.chunks[idx])
                if results:
                    return results
            except Exception as e:
                logger.warning(f"FAISS search failed: {e}. Falling back to lexical retrieval.")

        # 2. Resilient contextual lexical search (title boost + keyword overlap)
        return self._lexical_search(query, top_k)

    def _lexical_search(self, query: str, top_k: int = 4) -> list[str]:
        words = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
        if not words:
            return self.chunks[:top_k]

        scored_chunks = []
        for chunk in self.chunks:
            chunk_lower = chunk.lower()
            score = 0
            # Higher score for words appearing in Topic / title line
            first_line = chunk_lower.split("\n", 1)[0]
            for w in words:
                if w in first_line:
                    score += 5
                elif w in chunk_lower:
                    score += 1 + chunk_lower.count(w) * 0.5

            if score > 0:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        results = [chunk for _, chunk in scored_chunks[:top_k]]
        return results if results else self.chunks[:top_k]


faiss_service = FaissService()
