import os
import shutil
import tempfile
import logging
import re
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

from src.load_pdf import load_pdf_text
from src.embed_text import split_text, embed_chunks, save_faiss_index, load_faiss_index
from src.chatbot import ask_question, search_chunks, log_chat_to_db, log_feedback_to_db, get_chat_history

# Load environment variables
load_dotenv()

# Logging config
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# App settings
class Settings(BaseModel):
    PDF_PATH: str = "data/knowledge.pdf"
    EMBEDDING_MODEL: str = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek/deepseek-chat-v3-0324:free")
    FAISS_PATH: str = "embeddings/faiss_index.faiss"
    CHUNKS_PATH: str = "embeddings/chunks.pkl"

settings = Settings()

# Markdown cleaner
def strip_markdown(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"__([^_]*)__", r"\1", text)
    text = re.sub(r"_([^_]*)_", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

# FastAPI app
app = FastAPI(
    title="Chatbot API",
    description="FastAPI backend for PDF Q&A with embeddings + LLM",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://preview--perfect-ui-for-chatbot.lovable.app",
        "http://localhost:8080",
        "https://bignalytics-chatbot.me"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1024)

class ChatResponse(BaseModel):
    answer: str

class FeedbackRequest(BaseModel):
    question: str
    answer: str
    rating: int = Field(..., ge=1, le=5)
    comment: str = ""

# Model resource loader
class ModelResources:
    def __init__(self):
        self.embedding_model = None
        self.faiss_index = None
        self.chunk_list = None

    def load_all(self):
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        if not os.path.exists(settings.FAISS_PATH):
            text = load_pdf_text(settings.PDF_PATH)
            chunks = split_text(text)
            _, index, _, chunks_out = embed_chunks(chunks, settings.EMBEDDING_MODEL)
            save_faiss_index(index, chunks_out)
            self.faiss_index, self.chunk_list = index, chunks_out
        else:
            self.faiss_index, self.chunk_list = load_faiss_index()

resources = ModelResources()

@app.on_event("startup")
def on_startup():
    try:
        resources.load_all()
        logging.info("✅ Embedding model and FAISS index loaded.")
    except Exception as e:
        logging.critical(f"Startup failed: {e}")
        raise

def get_resources():
    return resources

# --- Chat Endpoint ---
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, res: ModelResources = Depends(get_resources)):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")

    top_chunks = search_chunks(res.embedding_model, res.faiss_index, res.chunk_list, question)
    if not top_chunks:
        raise HTTPException(status_code=404, detail="No relevant context found.")

    context = "\n\n".join(top_chunks)
    prompt = f"Context:\n{context}\n\nQuestion:\n{question}"

    try:
        answer = await ask_question(settings.LLM_MODEL, top_chunks, prompt)
        clean_answer = strip_markdown(answer)
    except Exception as e:
        logging.error(f"LLM error: {e}")
        raise HTTPException(status_code=500, detail="LLM generation failed.")

    try:
        import asyncio
        asyncio.create_task(log_chat_to_db(question, clean_answer))
    except Exception as e:
        logging.warning(f"Chat log failed: {e}")

    return ChatResponse(answer=clean_answer)

# --- Upload PDF Endpoint ---
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), res: ModelResources = Depends(get_resources)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        text = load_pdf_text(tmp_path)
        chunks = split_text(text)
        _, index, _, chunks_out = embed_chunks(chunks, settings.EMBEDDING_MODEL)
        save_faiss_index(index, chunks_out)
        res.faiss_index, res.chunk_list = index, chunks_out
    except Exception as e:
        logging.error(f"Upload/embedding failed: {e}")
        raise HTTPException(status_code=500, detail="PDF processing failed.")
    finally:
        os.unlink(tmp_path)

    return {"message": "PDF uploaded and indexed."}

# --- Feedback Endpoint ---
@app.post("/feedback")
async def feedback(req: FeedbackRequest):
    data = req.dict()
    data["timestamp"] = datetime.utcnow().isoformat()
    try:
        import asyncio
        asyncio.create_task(
            log_feedback_to_db(
                data["question"],
                data["answer"],
                data["rating"],
                data["comment"]
            )
        )
    except Exception as e:
        logging.warning(f"Feedback logging failed: {e}")
    return {"message": "Feedback recorded."}

# --- Chat History Endpoint ---
@app.get("/history")
async def history():
    try:
        return await get_chat_history()
    except Exception as e:
        logging.error(f"History fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch history.")

# --- Root & Health Check ---
@app.get("/")
def root():
    return {"message": "Chatbot API is running."}

@app.get("/health")
def health():
    return {"status": "ok"}
