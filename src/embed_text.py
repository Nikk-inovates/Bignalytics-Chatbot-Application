import os
import faiss
import pickle
import logging
import numpy as np
from typing import List, Tuple
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="🔹 [%(levelname)s] %(asctime)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Load model name from env or default
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


def split_text(
    text: str,
    strategy: str = "medium"  # 'small', 'medium', or 'large'
) -> List[str]:
    """
    Splits input text into chunks based on strategy.

    Args:
        text (str): The text to split.
        strategy (str): One of 'small', 'medium', or 'large'.

    Returns:
        List[str]: List of text chunks.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Text must be a non-empty string.")

    # Strategy configuration (based on token estimates)
    strategy_config = {
        "small": {"chunk_size": 500, "overlap": 100},   # 400–600 tokens
        "medium": {"chunk_size": 900, "overlap": 150},  # 800–1000 tokens
        "large": {"chunk_size": 1100, "overlap": 150},  # 1000–1200 tokens
    }

    if strategy not in strategy_config:
        raise ValueError("Strategy must be one of 'small', 'medium', or 'large'.")

    config = strategy_config[strategy]
    chunk_size = config["chunk_size"]
    overlap = config["overlap"]

    text = text.strip()
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap

    if not chunks:
        raise RuntimeError("Chunking failed. No valid text chunks were created.")

    logging.info(f"🔹 Created {len(chunks)} '{strategy}' chunks with size={chunk_size} and overlap={overlap}")
    return chunks


def embed_chunks(
    chunks: List[str],
    model_name: str = MODEL_NAME
) -> Tuple[SentenceTransformer, faiss.IndexFlatL2, np.ndarray, List[str]]:
    """
    Embeds chunks using a SentenceTransformer model and builds a FAISS index.

    Args:
        chunks (List[str]): The text chunks to embed.
        model_name (str): The model name to use for embeddings.

    Returns:
        Tuple containing:
            - SentenceTransformer: The embedding model
            - faiss.IndexFlatL2: The FAISS index
            - np.ndarray: The embeddings
            - List[str]: The original chunks
    """
    if not chunks or not all(isinstance(chunk, str) for chunk in chunks):
        raise ValueError("Chunks must be a non-empty list of strings.")

    try:
        logging.info(f"🚀 Loading embedding model: {model_name}")
        model = SentenceTransformer(model_name)
        embeddings = model.encode(chunks, show_progress_bar=True)
        embeddings = np.array(embeddings).astype("float32")

        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)

        logging.info("✅ Embedding and FAISS index creation successful.")
        return model, index, embeddings, chunks

    except Exception as e:
        logging.error(f"❌ Embedding failed: {e}")
        raise RuntimeError(f"Embedding failed: {e}")


def save_faiss_index(
    index: faiss.IndexFlatL2,
    chunks: List[str],
    path: str = "embeddings/faiss_index.faiss"
) -> None:
    """
    Saves the FAISS index and corresponding chunks to disk.

    Args:
        index (faiss.IndexFlatL2): The FAISS index to save.
        chunks (List[str]): The chunks associated with the index.
        path (str): File path to save the index.
    """
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        faiss.write_index(index, path)

        chunks_path = os.path.splitext(path)[0] + "_chunks.pkl"
        with open(chunks_path, "wb") as f:
            pickle.dump(chunks, f)

        logging.info("✅ FAISS index and chunks saved successfully.")

    except Exception as e:
        logging.error(f"❌ Error saving FAISS index or chunks: {e}")
        raise IOError(f"Error saving FAISS index or chunks: {e}")


def load_faiss_index(
    path: str = "embeddings/faiss_index.faiss"
) -> Tuple[faiss.IndexFlatL2, List[str]]:
    """
    Loads the FAISS index and corresponding chunks from disk.

    Args:
        path (str): File path to load the FAISS index from.

    Returns:
        Tuple containing:
            - faiss.IndexFlatL2: The loaded FAISS index
            - List[str]: The loaded text chunks
    """
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"FAISS index file not found at: {path}")

        index = faiss.read_index(path)

        chunks_path = os.path.splitext(path)[0] + "_chunks.pkl"
        if not os.path.exists(chunks_path):
            raise FileNotFoundError(f"Chunks file not found at: {chunks_path}")

        with open(chunks_path, "rb") as f:
            chunks = pickle.load(f)

        if not chunks:
            raise ValueError("Loaded chunks are empty.")

        logging.info("✅ FAISS index and chunks loaded successfully.")
        return index, chunks

    except Exception as e:
        logging.error(f"❌ Failed to load FAISS index or chunks: {e}")
        raise RuntimeError(f"Failed to load FAISS index or chunks: {e}")
