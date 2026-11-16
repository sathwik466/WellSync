import logging

from config import Config

logger = logging.getLogger(__name__)

_model = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None


def get_embedding_model():
    global _model
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        return None
    if _model is None:
        _model = SentenceTransformer(Config.EMBEDDING_MODEL)
    return _model


def encode_text(text: str) -> list[float]:
    model = get_embedding_model()
    if model is not None:
        return model.encode(text).tolist()
    # 384-dim dummy vector if sentence-transformers is not installed
    return [0.0] * 384


def encode_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    if model is not None:
        return model.encode(texts).tolist()
    return [[0.0] * 384 for _ in texts]
