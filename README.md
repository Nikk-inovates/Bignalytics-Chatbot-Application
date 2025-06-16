# Bignalytics Coaching Institute Chatbot

A production-grade conversational AI chatbot built for Bignalytics Coaching Institute. This system integrates FastAPI, Sentence Transformers, FAISS, and OpenRouter's DeepSeek API to deliver semantically aware, generative responses using a manually curated PDF dataset. A Streamlit frontend enables seamless user interaction.

---

## 📌 Table of Contents

* [Features](#features)
* [Tech Stack](#tech-stack)
* [Folder Structure & Explanation](#folder-structure--explanation)
* [Installation & Setup](#installation--setup)
* [Usage](#usage)
* [API & Feedback](#api--feedback)
* [Security & Environment Variables](#security--environment-variables)
* [Contributing](#contributing)
* [License](#license)
* [Acknowledgements](#acknowledgements)

---

## 🚀 Features

* **Conversational AI:** Understands user intent and returns intelligent responses.
* **Semantic Search:** Uses FAISS and Sentence Transformers to match user queries with indexed PDF chunks.
* **Generative Completion:** Integrated with OpenRouter’s DeepSeek API for contextually relevant answer generation.
* **Feedback Logging:** Captures user feedback and chat history to JSONL/JSON logs.
* **PDF Ingestion:** Manually curated course materials (PDF) ingested and chunked with preprocessing.
* **Streamlit UI:** Simple frontend to interact, visualize answers, and submit feedback.
* **Modular Architecture:** Code structured for clarity, scalability, and reusability.
* **API-Ready:** RESTful endpoints exposed for frontend integration, logging, and file uploads.

---

## 🛠️ Tech Stack

### Backend

* **FastAPI** – API service and routing
* **Python** – Core application logic
* **Sentence Transformers** – Embedding generator
* **FAISS** – Vector similarity search
* **PyMuPDF** – PDF parser

### Frontend

* **Streamlit** – Minimal, fast deployment UI

### Integrations

* **OpenRouter** – Hosts DeepSeek API for LLM inference
* **Asyncpg + PostgreSQL** – Optional DB integration for logging

### Others

* **dotenv** – Secret/environment management
* **httpx/requests** – API calls

---

## 🗂️ Folder Structure & Explanation

```
MY CHATBOT BIGNALYTICS/
│
├── __pycache__/                  # Python cache files
├── data/                         # Source PDF documents
│   └── knowledge.pdf             # Primary PDF knowledge base
├── embeddings/                   # FAISS index + chunk store
│   ├── faiss_index.faiss
│   └── faiss_index_chunks.pkl
├── logs/                         # Chat and feedback logs
│   ├── chat_history.json
│   └── feedback_logs.jsonl
├── src/                          # Source code (modular)
│   ├── chatbot.py                # Chat flow, LLM calling
│   ├── embed_text.py             # Embedding logic
│   ├── load_pdf.py               # PDF parsing
│   └── retriever.py              # FAISS semantic search
├── ui/                           # Streamlit frontend
│   └── streamlit_app.py          # UI entrypoint
├── .env                          # Secret keys and paths
├── main.py                       # FastAPI entrypoint
├── requirements.txt              # Python dependencies
└── package.json (optional)       # Frontend dependency config
```

### Key Files

* `main.py`: FastAPI backend server
* `streamlit_app.py`: Streamlit UI entrypoint
* `chatbot.py`: Core orchestrator for answering queries using retrieval + generation
* `load_pdf.py`: Parses PDF into clean chunks
* `embed_text.py`: Converts text into vectors for FAISS
* `retriever.py`: Handles similarity search

---

## ⚙️ Installation & Setup

### Prerequisites

* Python 3.8+
* Git
* Node.js (if frontend or tooling needed)

### Steps

```bash
# 1. Clone repo
$ git clone https://github.com/yourusername/bignalytics-chatbot.git
$ cd bignalytics-chatbot

# 2. Setup virtual env
$ python -m venv venv
$ source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
$ pip install -r requirements.txt

# 4. (Optional) Install frontend packages
$ npm install

# 5. Configure .env
$ touch .env
# Add keys manually as shown below

# 6. Start backend server
$ uvicorn main:app --reload

# 7. Launch UI in another terminal
$ streamlit run ui/streamlit_app.py
```

---

## 💡 Usage

* Open `http://localhost:8000` to check API status
* Open `http://localhost:8501` for the Streamlit chatbot UI
* Ask queries related to your uploaded knowledge base (PDF)
* Responses will be dynamically generated using context-aware search and LLM
* Feedback and chat history saved in `/logs/`

---

## 📬 API & Feedback

### Endpoints

* **POST /chat**: Submit a question and receive LLM response
* **POST /upload**: Upload or update PDF knowledge base
* **POST /feedback**: Submit thumbs up/down and comments
* **GET /history**: View previous chat logs

All endpoints use JSON payloads and return standardized JSON responses.

---

## 🔐 Security & Environment Variables

Environment configuration is managed via `.env` file. Sample variables:

```ini
OPENROUTER_API_KEY=your_openrouter_key_here
DATABASE_URL=postgresql://username:password@host:5432/dbname
SSL_CERT_PATH=/path/to/your/fullchain.pem
```

Make sure to keep `.env` private and never commit it to GitHub.

---

## 🤝 Contributing

Pull requests are welcome. For significant changes, open an issue first to propose your idea or feature.

---

## 📄 License

MIT License – see [LICENSE](./LICENSE) for full details.

---

## 🙏 Acknowledgements

* Bignalytics Coaching Institute
* FastAPI | Streamlit
* Sentence Transformers | FAISS
* OpenRouter & DeepSeek
* PyMuPDF

---

🔍 Built with precision to deliver real-time knowledge to Bignalytics learners.
