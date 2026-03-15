from typing import List, Union

from loguru import logger
from sentence_transformers import SentenceTransformer
from settings import EMBEDDING_MODEL


class EmbeddingService:
    """Generates text embeddings using a sentence-transformers model."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        logger.info(f"Loading embedding model: {model_name}")
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        logger.info(f"Embedding model loaded (dimension: {self.get_dimension()})")

    def encode(
        self, text: Union[str, List[str]]
    ) -> Union[List[float], List[List[float]]]:
        """Encode one or more texts into embedding vectors."""
        embeddings = self.model.encode(text)
        if isinstance(text, str):
            return embeddings.tolist()
        return [emb.tolist() for emb in embeddings]

    def get_dimension(self) -> int:
        """Return the embedding vector dimension."""
        return self.model.get_sentence_embedding_dimension()
