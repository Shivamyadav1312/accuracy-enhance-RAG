# 📚 Code Documentation — Accuracy Enhance RAG System

Complete reference for every folder and file in the project.

---

## 🗂️ Project Overview

A **Domain-Specialized RAG (Retrieval-Augmented Generation) System** for **Travel** and **Real Estate** intelligence. It combines:

- **FastAPI** backend for document ingestion + LLM querying
- **Streamlit** frontends (3 variants) for user interaction
- **Pinecone** vector database for semantic search
- **Together AI / Groq** for LLM inference
- **OCR** support for scanned PDFs

---

## 📁 Root Directory Structure

```
accuracy enhance/
├── 🔧 Configuration files       (.env, .gitignore, requirements.txt, start.sh)
├── 🚀 Backend apps              (app.py, app2.py)
├── 🎨 Streamlit UIs             (streamlit_ui.py, streamlit_ui_with_upload.py, streamlit_dual_answer_ui.py)
├── 📥 Ingestion scripts         (ingest_*.py, bulk_ingest_documents.py)
├── 🔍 Query / Test scripts      (interactive_query.py, dual_answer_query.py, test_*.py)
├── 🛠️ Utility scripts           (check_*.py, retry_failed_ingestion.py, expand_real_estate.py)
├── 📊 Data folders              (data/, downloaded_docs/, real_estate_expanded/)
├── 📄 Documentation (.md)       (15+ guides)
└── 📕 Reference PDFs            (3 industry reports)
```

---

## ⚙️ Configuration Files

### `.env`
Environment variables for API keys and runtime config.
| Variable | Purpose |
|---|---|
| `PINECONE_API_KEY` | Pinecone vector DB authentication |
| `PINECONE_ENV` | Pinecone region (e.g., `us-west1-gcp`) |
| `GROQ_API_KEY` | Groq LLM API key |
| `TOGETHER_API_KEY` | Together AI LLM API key |
| `SERPER_API_KEY` | Web search API |
| `API_BASE_URL` | Backend URL (local or Render) |

### `.gitignore`
Excludes `.env`, `__pycache__/`, virtual envs, logs, and large data files from Git.

### `requirements.txt`
Python dependencies grouped by purpose:
- **Web**: `fastapi`, `uvicorn`, `flask`, `flask-cors`, `python-multipart`
- **Frontend**: `streamlit`, `requests`
- **AI/ML**: `together`, `sentence-transformers`, `langchain`, `langchain-text-splitters`
- **Vector DB**: `pinecone>=5.0.0`
- **Document Processing**: `PyPDF2`, `python-docx`, `pytesseract`, `pdf2image`, `Pillow`
- **Utilities**: `python-dotenv`, `pydantic`, `numpy`, `httpx`

### `start.sh`
Shell script for Render deployment that resolves the `$PORT` env variable and launches the FastAPI server.

### `.streamlit/config.toml`
Streamlit server config (headless mode, port 10000, CORS disabled) for cloud deployment.

### `.streamlit/secrets.toml`
Secrets used when deploying to Streamlit Community Cloud.

### `.devcontainer/devcontainer.json`
VS Code dev container config for reproducible development environments.

---

## 🚀 Backend Application Files

### `app.py` (29.6 KB) — Legacy Flask Backend
Earlier version of the API server using **Flask + Flask-CORS**. Provides basic ingestion and query endpoints. Superseded by `app2.py`.

### `app2.py` (47.5 KB) — **Main FastAPI Backend** ⭐
The production backend. Key responsibilities:
- **Lazy-loaded ML models** (sentence-transformer `paraphrase-MiniLM-L3-v2`)
- **Document ingestion**: PDF / DOCX / TXT / image with OCR fallback (Poppler + pytesseract)
- **Vector storage**: Pinecone index `documents-index`
- **Dual-answer mode**: combines document-grounded answers with general LLM knowledge
- **Domain detection**: Travel vs Real Estate classification with namespacing
- **Endpoints**:
  - `POST /upload` — upload documents
  - `POST /query` — query with optional dual-answer
  - `GET  /health` — service health
  - `GET  /documents` — list ingested files
- **Render-ready**: reads `PORT` env var and binds to `0.0.0.0`
- **Prompt safety**: truncates prompts at 120,000 chars to prevent Together AI 400 errors
- **Memory tuning**: `MAX_TOKENS = 2048` to fit Render's 512 MB free tier

---

## 🎨 Streamlit Frontend Files

### `streamlit_ui.py` (20.8 KB)
Original Streamlit UI — query-only interface (no upload). Connects to backend via `API_BASE_URL`.

### `streamlit_ui_with_upload.py` (36.2 KB) — **Main UI** ⭐
Full-featured UI:
- File upload (PDF / DOCX / TXT / images)
- Session-based document tracking (`st.session_state.uploaded_docs`)
- Dual-answer toggle (document-specific + general knowledge)
- Domain selector (Travel / Real Estate / Auto)
- Live status indicator for backend health
- Reads `API_BASE_URL` from environment

### `streamlit_dual_answer_ui.py` (11.9 KB)
Lightweight UI focused exclusively on the **dual-answer** workflow — side-by-side comparison of document context vs general LLM knowledge.

---

## 📥 Document Ingestion Scripts

### `auto_document_downloader.py` (16.1 KB)
Automates web scraping & download of domain-specific reports (real estate, travel) from public sources.

### `domain_document_collector.py` (8.9 KB)
Categorizes downloaded documents into domain folders (`market_intelligence`, `economic_factors`, `destinations`, etc.).

### `bulk_ingest_documents.py` (11.2 KB)
Bulk-uploads all files in a directory to the Pinecone index. Walks `downloaded_docs/` recursively.

### `ingest_travel_pdfs.py` (2.3 KB)
Ingests the three reference travel PDFs at the project root.

### `ingest_csv_reports.py` (5.0 KB)
Parses CSV reports from `travel_real_estate_reports_sources.csv` and ingests row content.

### `ingest_travel_queries_csv.py` (7.7 KB)
Ingests `travel_queries_global_5000.csv` (5000 sample travel queries) for query-pattern training data.

### `upload_travel_reports.py` (6.0 KB)
Uploads pre-processed travel reports to Pinecone with metadata enrichment.

### `expand_real_estate.py` (17.0 KB)
Expands the real-estate dataset by pulling Zillow / FRED / metro reports into `real_estate_expanded/`.

### `retry_failed_ingestion.py` (3.0 KB)
Reads `domain_ingestion_errors_*.txt` and retries failed documents.

---

## 🔍 Query & Testing Scripts

### `interactive_query.py` (6.8 KB)
CLI prompt-loop for querying the Pinecone index without the Streamlit UI.

### `dual_answer_query.py` (8.4 KB)
CLI tool that demonstrates dual-answer mode (document-grounded + general knowledge).

### `enhanced_rag_with_queries.py` (12.7 KB)
Enhanced RAG pipeline combining retrieval + query rewriting + reranking.

### `test_dual_answer.py` (4.4 KB)
Unit/integration tests for the dual-answer feature.

### `check_documents.py` (6.6 KB)
Verifies which documents are indexed in Pinecone.

### `check_pinecone_data.py` (3.4 KB)
Inspects raw vectors and metadata stored in Pinecone.

### `check_and_cleanup_docs.py` (4.7 KB)
Identifies orphaned / duplicate vectors and cleans them up.

### `check_ui_query.py` (2.6 KB)
End-to-end test: simulates a UI query against the running backend.

---

## 📊 Data Folders

### `data/`
Curated source data organized by domain.
| Subfolder | Contents |
|---|---|
| `real-estate/real_estate_price_trends_100docs/` | 43 docs on price trends |
| `real-estate/real_estate_price_trends_docs/` | 6 baseline docs |
| `tour/` | (placeholder, currently empty) |
| `travel/tourism_stats/` | Tourism statistics |

### `downloaded_docs/`
Auto-downloaded reports categorized by domain & topic.
| Path | Contents |
|---|---|
| `real_estate/economic_factors/` | 7 economic-indicator reports |
| `real_estate/market_intelligence/` | 2 market-intelligence reports |
| `real_estate/price_prediction/` | 4 price-prediction reports |
| `travel/destinations/` | 82 destination guides |
| `travel/transportation/` | 3 transportation reports |

### `real_estate_expanded/`
Extended real-estate dataset.
| Subfolder | Contents |
|---|---|
| `city_data/` | NYC & Chicago property sales |
| `fred_indicators/` | 20 FRED economic indicators (CPI, GDP, MORTGAGE30US, UNRATE, etc.) |
| `hud_data/` | HUD housing data (placeholder) |
| `metro_reports/` | 30 US metro-area reports |
| `zillow_data/` | 13 Zillow datasets (ZHVI, ZORI, inventory, listings, sale prices) |

---

## 📕 Reference PDFs (Root)

| File | Description |
|---|---|
| `The-Travel-Industrys-New-Trip-Final.pdf` | Travel industry trends (1.5 MB) |
| `WEF_Travel_and_Tourism_at_a_Turning_Point_2025.pdf` | WEF 2025 report (18.6 MB) |
| `amadeus-future-traveller-tribes-2030-report.pdf` | Amadeus future-travel report (4.5 MB) |

---

## 📄 CSV Data Files

| File | Description |
|---|---|
| `travel_queries_global_5000.csv` (249 KB) | 5000 global travel query samples |
| `travel_real_estate_reports_sources.csv` (4 KB) | Source URLs for ingestion scripts |
| `test_paris_hotels.txt` | Sample test document |

---

## 📚 Documentation Files (.md)

| File | Purpose |
|---|---|
| `BOSS_REQUIREMENTS_STATUS.md` | Requirements vs delivery status |
| `PROJECT_STATUS_SUMMARY.md` | Overall project health snapshot |
| `FEATURE_SUMMARY.md` | List of implemented features |
| `QUICK_START.md` | Fast onboarding guide |
| `QUICK_START_CSV.md` | CSV ingestion quick-start |
| `NEXT_STEPS.md` | Roadmap / pending work |
| `INGESTION_GUIDE.md` | Document ingestion how-to |
| `INGESTION_SUCCESS_SUMMARY.md` | Ingestion run results |
| `README_INGESTION.md` | Ingestion module README |
| `CSV_INGESTION_README.md` | CSV-specific ingestion docs |
| `DOCUMENT_COLLECTION_STRATEGY.md` | Document sourcing strategy |
| `DOMAIN_CLASSIFIER_IMPLEMENTATION.md` | Domain detection internals |
| `DUAL_ANSWER_GUIDE.md` | Dual-answer feature design |
| `HOW_TO_USE_DUAL_ANSWER.md` | Dual-answer usage tutorial |
| `TEST_QUERIES.md` | Sample queries for testing |

---

## 🧰 Logs & Hidden Folders

| Path | Purpose |
|---|---|
| `domain_ingestion.log` | Runtime ingestion log |
| `domain_ingestion_errors_20251105_150830.txt` | Failed ingestion records |
| `__pycache__/` | Python bytecode cache |
| `.qoder/agents/` & `.qoder/skills/` | Qoder IDE agents/skills config |
| `.qodo/agents/` & `.qodo/workflows/` | Qodo agent workflows |

---

## 🔄 Typical Workflows

### 1️⃣ Run Backend Locally
```powershell
python app2.py
# → http://localhost:8000
```

### 2️⃣ Run UI Locally
```powershell
python -m streamlit run streamlit_ui_with_upload.py
# → http://localhost:8501
```

### 3️⃣ Bulk-Ingest Documents
```powershell
python bulk_ingest_documents.py
```

### 4️⃣ Deploy
- **Backend** → Render (auto via `start.sh` + `$PORT`)
- **Frontend** → Streamlit Community Cloud (uses `.streamlit/config.toml`)

---

## 🧱 Architecture Summary

```
┌─────────────────────┐        ┌────────────────────┐        ┌──────────────────┐
│  Streamlit UI       │  HTTP  │  FastAPI (app2.py) │  REST  │  Pinecone Index  │
│  (upload + query)   │ ─────▶ │  Ingest + Query    │ ─────▶ │  documents-index │
└─────────────────────┘        └────────┬───────────┘        └──────────────────┘
                                        │
                                        │ Embed (paraphrase-MiniLM-L3-v2)
                                        │ LLM (Together AI / Groq)
                                        ▼
                                ┌────────────────────┐
                                │  OCR (Poppler +    │
                                │  pytesseract)      │
                                └────────────────────┘
```

---

## ✅ Key Tech Stack Recap

| Layer | Tech |
|---|---|
| **Backend** | FastAPI + Uvicorn |
| **Frontend** | Streamlit |
| **Vector DB** | Pinecone (`documents-index`) |
| **Embeddings** | `sentence-transformers/paraphrase-MiniLM-L3-v2` |
| **LLM** | Together AI + Groq |
| **OCR** | Poppler + pytesseract + pdf2image |
| **Deployment** | Render (backend) + Streamlit Cloud (UI) |

---

*Generated on March 24, 2026 — covers every file & folder in the workspace.*
