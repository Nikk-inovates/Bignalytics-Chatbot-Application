import os
import json
import faiss
import numpy as np
import logging
from datetime import datetime
from typing import List, Optional, Union
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import asyncio
import asyncpg
import httpx

# --- Load environment variables ---
load_dotenv()

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Constants ---
MODEL_NAME = "deepseek/deepseek-chat-v3-0324:free"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
    "Content-Type": "application/json",
}
DEBUG = False

# --- Database pool ---
db_pool = None

async def get_db_pool():
    """Initializes and returns a singleton connection pool."""
    global db_pool
    if db_pool is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise EnvironmentError("❌ DATABASE_URL not found in .env")
        db_pool = await asyncpg.create_pool(dsn=database_url)
    return db_pool

def setup_deepseek() -> str:
    """Returns the model name for DeepSeek."""
    return MODEL_NAME

async def ask_question(model_name: str, context_chunks: List[str], user_question: str) -> str:
    """Asks a question to the DeepSeek model using OpenRouter API."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return "❌ OPENROUTER_API_KEY not found in environment."

    if not context_chunks:
        return "⚠️ No context available to answer the question."

    context = "\n\n".join(context_chunks)

    prompt = f"""You are a professional, helpful assistant. Format your responses as:
1. Introduction or overview.
2. Bullet points with suitable headings.
3. Additional information if relevant.

Context:
{context}

Question:
{user_question}"""

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that answers based on given context."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(OPENROUTER_API_URL, headers=HEADERS, json=payload)

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            logger.error(f"❌ DeepSeek API error {response.status_code}: {response.text}")
            return f"❌ API Error {response.status_code}: {response.text}"

    except Exception as e:
        logger.exception("❌ Exception while querying DeepSeek API")
        return f"❌ Exception occurred: {e}"

def search_chunks(embedding_model: SentenceTransformer, index: faiss.Index, chunks: List[str], query: str, top_k: int = 3) -> List[str]:
    """Searches for top-k relevant chunks using FAISS."""
    if not query.strip() or not chunks:
        return []

    try:
        query_embedding = embedding_model.encode([query])
        query_embedding = np.array(query_embedding).astype("float32")
        D, I = index.search(query_embedding, top_k)
        top_chunks = [chunks[i] for i in I[0] if i < len(chunks)]
        return top_chunks
    except faiss.FaissException as fe:
        logger.error(f"❌ FAISS search error: {fe}")
        return []
    except Exception as e:
        logger.exception("❌ Unexpected error during FAISS search")
        return []

async def log_chat_to_db(question: str, answer: str):
    """Logs a chat interaction to the database."""
    try:
        pool = await get_db_pool()
        timestamp = datetime.utcnow()
        query = """
            INSERT INTO chat_logs (question, answer, timestamp)
            VALUES ($1, $2, $3)
        """
        await pool.execute(query, question.strip(), answer.strip(), timestamp)
        logger.info("✅ Chat log saved to chat_logs")
    except Exception as e:
        logger.exception("❌ Failed to save chat log")
        raise

async def log_feedback_to_db(question: Union[str, dict], answer: Union[str, dict], rating: str, comment: Optional[str]):
    """Logs user feedback to the database."""
    try:
        allowed_ratings = ("up", "down")
        if rating not in allowed_ratings:
            raise ValueError(f"Invalid rating: {rating}. Must be one of {allowed_ratings}.")

        if isinstance(question, dict):
            question = json.dumps(question)
        if isinstance(answer, dict):
            answer = json.dumps(answer)

        pool = await get_db_pool()
        timestamp = datetime.utcnow()
        query = """
            INSERT INTO feedback_logs (question, answer, rating, comment, timestamp)
            VALUES ($1, $2, $3, $4, $5)
        """
        await pool.execute(query, question.strip(), answer.strip(), rating, comment or "", timestamp)
        logger.info("✅ Feedback saved to feedback_logs")
    except Exception as e:
        logger.exception("❌ Failed to save feedback")
        raise

async def get_chat_history(limit: int = 50) -> List[dict]:
    """Fetches recent chat history from the database."""
    try:
        pool = await get_db_pool()
        query = """
            SELECT question, answer, timestamp
            FROM chat_logs
            ORDER BY timestamp DESC
            LIMIT $1
        """
        rows = await pool.fetch(query, limit)
        return [dict(row) for row in rows]
    except Exception as e:
        logger.exception("❌ Failed to fetch chat history")
        return []

def save_chat_sync(question: str, answer: str):
    """Synchronous wrapper to log chat (not ideal inside FastAPI loop)."""
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(log_chat_to_db(question, answer))
    except Exception as e:
        logger.exception("❌ Sync chat save failed")

def save_feedback_sync(question: str, answer: str, rating: str, comment: Optional[str]):
    """Synchronous wrapper to log feedback."""
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(log_feedback_to_db(question, answer, rating, comment))
    except Exception as e:
        logger.exception("❌ Sync feedback save failed")
