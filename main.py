from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from datetime import datetime
import os
import shutil
import logging
import re
import textwrap
import asyncio

from src.load_pdf import load_pdf_text
from src.embed_text import split_text, embed_chunks, save_faiss_index, load_faiss_index
from src.chatbot import (
    ask_question as ask_llm_question,
    search_chunks,
    log_chat_to_db,
    log_feedback_to_db,
    get_chat_history
)

load_dotenv()

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FastAPI App Initialization ---
app = FastAPI()

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

# --- Constants ---
PDF_DIR = "data"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
LLM_MODEL_NAME = "deepseek/deepseek-chat-v3-0324:free"
FAISS_INDEX_PATH = "embeddings/faiss_index.faiss"
CHUNKS_SAVE_PATH = "embeddings/chunks.pkl"
PDF_PATH = os.path.join(PDF_DIR, "knowledge.pdf")

# --- Directory Setup ---
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs("embeddings", exist_ok=True)

embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
faiss_index = None
chunk_list = None

# --- Serve Static Frontend ---
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/dist"))
if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")
    app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIST, "static")), name="static")

# --- Text Cleaning + Formatting ---
def clean_text(text: str) -> str:
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)
    text = re.sub(r"#+\s*(.*)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"(?m)^\s*-\s+", "• ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def format_bullet_hanging_indent(text: str, max_width=70) -> str:
    lines = []
    for paragraph in text.split('\n'):
        if paragraph.startswith("• "):
            bullet = "• "
            indent = " " * (len(bullet) + 1)
            formatted = textwrap.fill(
                paragraph[len(bullet):],
                width=max_width,
                initial_indent=bullet,
                subsequent_indent=indent
            )
            lines.append(formatted)
        else:
            lines.append(paragraph)
    return "\n".join(lines)

# --- Startup: Load or Create FAISS Index ---
@app.on_event("startup")
def startup_event():
    global faiss_index, chunk_list
    try:
        if not os.path.exists(FAISS_INDEX_PATH):
            logger.info("FAISS index not found. Creating from local PDF...")
            text = load_pdf_text(PDF_PATH)
            chunks = split_text(text)
            _, index, _, chunk_list_local = embed_chunks(chunks, EMBEDDING_MODEL_NAME)
            save_faiss_index(index, chunk_list_local)
            faiss_index, chunk_list = index, chunk_list_local
            logger.info("✅ FAISS index created.")
        else:
            logger.info("Loading existing FAISS index and chunks...")
            faiss_index, chunk_list = load_faiss_index()
    except Exception as e:
        logger.error(f"Startup FAISS error: {e}")

@app.get("/")
def root():
    return {"message": "🚀 PDF Chatbot API is live!"}

# --- Upload PDF & Rebuild FAISS Index ---
@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(PDF_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        text = load_pdf_text(file_path)
        chunks = split_text(text)
        _, index, _, chunk_list_local = embed_chunks(chunks, EMBEDDING_MODEL_NAME)
        save_faiss_index(index, chunk_list_local)

        global faiss_index, chunk_list
        faiss_index, chunk_list = index, chunk_list_local

        return {"message": "✅ PDF uploaded and processed."}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"❌ Upload failed: {str(e)}"})

# --- Ask Question via /ask-question/ (Form format) ---
@app.post("/ask-question/")
async def ask_question_api(question: str = Form(...)):
    try:
        if not faiss_index or not chunk_list:
            return JSONResponse(status_code=400, content={"error": "❌ FAISS index not loaded."})

        top_chunks = search_chunks(embedding_model, faiss_index, chunk_list, question)

        prompt_instructions = (
            "Respond clearly and professionally in fluent, natural English. "
            "Use sentence case, bullet points, and proper structure. "
            "Avoid markdown or informal expressions."
        )

        context_text = "\n\n".join(top_chunks)
        full_prompt = f"{prompt_instructions}\n\nContext:\n{context_text}\n\nQuestion:\n{question}"

        raw_response = ask_llm_question(LLM_MODEL_NAME, top_chunks, full_prompt)
        clean_response = format_bullet_hanging_indent(clean_text(raw_response))

        asyncio.create_task(log_chat_to_db(question, clean_response))
        return {"answer": clean_response}
    except Exception as e:
        logger.error(f"Ask error: {e}")
        return JSONResponse(status_code=500, content={"error": f"❌ Ask failed: {str(e)}"})

# --- Ask Question via /chat (JSON format) ---
@app.post("/chat")
async def chat_api(request: Request):
    try:
        data = await request.json()
        question = data.get("question", "").strip()

        if not question:
            return JSONResponse(status_code=400, content={"error": "❌ Question missing."})
        if not faiss_index or not chunk_list:
            return JSONResponse(status_code=400, content={"error": "❌ FAISS index not loaded."})

        top_chunks = search_chunks(embedding_model, faiss_index, chunk_list, question)

        prompt_instructions = (
            "Respond clearly and professionally in fluent, natural English. "
            "Use sentence case, bullet points, and proper structure. "
            "Avoid markdown or informal expressions."
        )

        context_text = "\n\n".join(top_chunks)
        full_prompt = f"{prompt_instructions}\n\nContext:\n{context_text}\n\nQuestion:\n{question}"

        raw_response = ask_llm_question(LLM_MODEL_NAME, top_chunks, full_prompt)
        clean_response = format_bullet_hanging_indent(clean_text(raw_response))

        asyncio.create_task(log_chat_to_db(question, clean_response))
        return {"answer": clean_response}
    except Exception as e:
        logger.error(f"/chat error: {e}")
        return JSONResponse(status_code=500, content={"error": f"❌ Chat failed: {str(e)}"})

# --- Save Feedback ---
@app.post("/log-feedback/")
async def log_feedback_api(request: Request):
    try:
        feedback = await request.json()
        feedback["timestamp"] = datetime.utcnow().isoformat()

        asyncio.create_task(log_feedback_to_db(
            feedback.get("question", ""),
            feedback.get("answer", ""),
            feedback.get("rating", ""),
            feedback.get("comment", "")
        ))

        return {"message": "✅ Feedback saved."}
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        return JSONResponse(status_code=500, content={"error": f"❌ Feedback failed: {str(e)}"})

# --- Get Chat History ---
@app.get("/history")
async def chat_history():
    try:
        history = await get_chat_history()
        return history
    except Exception as e:
        logger.error(f"History error: {e}")
        return JSONResponse(status_code=500, content={"error": "❌ Failed to fetch history."})

# --- Serve React Index Page ---
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return JSONResponse(status_code=404, content={"error": "Frontend not found."})
