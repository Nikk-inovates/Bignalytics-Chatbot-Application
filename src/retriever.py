import numpy as np
import logging
from typing import List
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="🔍 [%(levelname)s] %(asctime)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def get_top_chunks(
    query: str,
    model: SentenceTransformer,
    vectors: np.ndarray,
    chunks: List[str],
    top_k: int = 3
) -> List[str]:
    """
    Retrieve top-k most relevant text chunks to a query based on cosine similarity.

    Args:
        query (str): User's question or prompt.
        model (SentenceTransformer): Pretrained embedding model.
        vectors (np.ndarray): Precomputed embeddings for chunks.
        chunks (List[str]): Text chunks.
        top_k (int, optional): Number of top results to return. Defaults to 3.

    Returns:
        List[str]: List of most relevant text chunks.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("❌ Invalid or empty query provided.")

    if not isinstance(chunks, list) or not chunks:
        raise ValueError("❌ Text chunks must be a non-empty list.")

    if not isinstance(vectors, np.ndarray) or len(vectors) != len(chunks):
        raise ValueError("❌ Embedding vectors and chunks mismatch or invalid format.")

    if not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("❌ top_k must be a positive integer.")

    try:
        logging.info(f"🔎 Computing embeddings for query: {query}")
        query_vector = model.encode([query])
        similarity_scores = cosine_similarity(query_vector, vectors).flatten()

        if np.isnan(similarity_scores).any():
            raise ValueError("❌ Similarity scores contain NaN. Check input vectors.")

        top_indices = similarity_scores.argsort()[::-1][:top_k]
        top_chunks = [chunks[i] for i in top_indices]

        logging.info(f"✅ Retrieved top-{top_k} relevant chunks.")
        return top_chunks

    except Exception as e:
        logging.error(f"❌ Failed to compute similarity: {e}")
        raise RuntimeError(f"Similarity computation failed: {e}")
