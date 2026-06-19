# Lexora: Privacy-First Offline AI Document Assistant

Lexora is a completely offline, single-user, ChatGPT-like AI document assistant. It operates entirely on your local machine with zero external API dependencies, ensuring absolute privacy for your personal files and conversations.

---

## 🚀 Key Features

*   **100% Local & Private**: No cloud connections, no internet dependency, and no data tracking.
*   **ChatGPT-like Chat UI**: Slate-themed design featuring markdown support, real-time typing streaming, copy-to-clipboard buttons, and abort controls.
*   **Semantic RAG (Retrieval-Augmented Generation)**: Upload documents and query them locally using semantic vector searches.
*   **Multi-Format Ingestion**: Offline text extraction support for **PDFs** (via PyMuPDF), **Word Documents** (via python-docx), **CSV Sheets** (via pandas), and **Text Files**.
*   **Performance Optimization**: Specifically optimized for standard systems (e.g. 16GB RAM + Intel Core i7 12th Gen) by restricting thread counts to prevent P-core/E-core thrashing.

---

## 🛠️ Technology Stack

*   **Frontend**: Next.js 15, TypeScript, Tailwind CSS, Lucide Icons.
*   **Backend**: FastAPI (Python 3.10+).
*   **Embeddings Model**: `bge-m3` (BAAI) running locally in Ollama.
*   **Language Model**: `qwen3:4b` running locally in Ollama.
*   **Vector Search Index**: FAISS (L2 Euclidean distance mapper wrapped in custom IndexIDMap for vector deletion safety).

---

## 📋 Prerequisites

Before running Lexora, ensure you have the following installed locally:

1.  **Python 3.10+**
2.  **Node.js 18+ & npm**
3.  **Ollama**: Download and install it from [Ollama.com](https://ollama.com).
4.  **Local Models**: Pull the required LLM and embedding models in your command prompt/terminal:
    ```bash
    ollama pull qwen3:4b
    ollama pull bge-m3
    ```

---

## ⚙️ Local Installation & Setup

### 1. Backend Server Setup
Navigate into the `backend/` directory, create a virtual environment, install requirements, and run uvicorn:

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# (On Windows PowerShell):
.venv\Scripts\Activate.ps1
# (On Linux/macOS):
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the uvicorn server
uvicorn app.main:app --reload --port 8000
```
The backend API will start running at `http://127.0.0.1:8000`. You can test sanity by checking the health endpoint: `http://127.0.0.1:8000/health`.

---

### 2. Frontend Next.js Setup
Open a new terminal window, navigate into the `frontend/` directory, install packages, and launch development server:

```bash
cd frontend

# Install package dependencies
npm install

# Start the Next.js development server
npm run dev
```
Open `http://localhost:3000` in your web browser.

---

## 📂 Project Architecture

```
Lexora/
├── backend/
│   ├── app/
│   │   ├── api/                   # Routing and Controllers
│   │   │   ├── endpoints/         # Chat and Document routes
│   │   │   └── router.py          # Combined router map
│   │   ├── core/                  # Configuration Settings
│   │   │   └── config.py          # Port bindings and storage definitions
│   │   ├── loaders/               # PDF, DOCX, TXT, CSV extractors
│   │   ├── services/              # Business logic (recursive chunker)
│   │   ├── embeddings/            # Ollama embedding wrapper
│   │   │   └── bge.py             # bge-m3 vectorizer
│   │   ├── vectorstore/           # FAISS Index managers
│   │   │   └── faiss.py           # Local search database
│   │   ├── schemas/               # Request/Response validation definitions
│   │   └── main.py                # FastAPI bootstrapper
│   └── requirements.txt           # Python packages listing
├── frontend/
│   ├── app/                       # Next.js App router
│   ├── components/                # Reusable React components (Markdown parser)
│   ├── hooks/                     # Custom react hooks
│   ├── lib/                       # API fetching helpers
│   └── package.json               # Node build scripts
└── storage/                       # Local database directories (Git-ignored)
    ├── documents/                 # Raw uploaded document storage
    ├── faiss/                     # FAISS serialized vector binaries
    └── metadata/                  # Mappings relating vectors back to text chunks
```

---

## 🔒 Privacy & Data Policies
Lexora processes files strictly inside your computer. Chunks are stored in the local `storage/metadata` folder, vectors reside in `storage/faiss`, and inference is run on your CPU/GPU via your local Ollama daemon. No information is transmitted to the internet.
