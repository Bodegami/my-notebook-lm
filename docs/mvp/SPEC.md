# Technical Specification — Local RAG Library with Docker

**Version:** 2.0
**Date:** 2026-03-16
**Status:** Final

---

## 1. Project Overview

A local document intelligence system for **ingesting, indexing, and conversationally querying digital books**, running entirely via Docker with no dependency on cloud APIs. The user uploads books in various digital formats and chats with an AI agent that answers based solely on the content of those books, always citing the exact source (book title + page number or section) for every claim.

### 1.1 Core Principles

- **Data sovereignty**: no document, message, or metadata leaves the local environment.
- **Offline operation**: fully functional without internet after initial installation (model download).
- **Traceability**: every agent assertion must link to a real text excerpt from the source document, including book title and page number. Summaries must cite all contributing books.
- **Portability**: a single `docker-compose up` command brings up the entire environment.
- **Ephemeral by design**: the system is meant to be used in focused study sessions. Each session starts fresh via `docker-compose down -v && docker-compose up -d`.

### 1.2 Hardware Profile

The specification is designed and optimized for the following hardware:

| Resource | Available |
|----------|-----------|
| RAM | 16 GB |
| GPU | NVIDIA with 2 GB vRAM |
| Storage | Local disk (SSD recommended) |

> **Implication**: With only 2 GB of vRAM, the LLM will run primarily on CPU using system RAM. This is functional but slower. Model selection and Ollama configuration are optimized for this constraint (see Section 6.3).

---

## 2. Business Requirements

| ID | Requirement | Description |
|----|-------------|-------------|
| RN-01 | Total privacy | No document, message, or query leaves the local environment |
| RN-02 | Cloud independence | Fully functional without internet (open-source models via Ollama) |
| RN-03 | Traceability | Every response must cite source book and page/section; summaries cite all contributing books |
| RN-04 | Study productivity | Fast retrieval of specific information across multiple books |
| RN-05 | Portability | Works on hardware with limited vRAM; automatic CPU fallback |
| RN-06 | Session isolation | Each study session starts completely fresh with a clean knowledge base |

---

## 3. Functional Requirements

### RF-01 — Document Ingestion

- Upload of multiple files simultaneously via drag-and-drop or file picker
- **Supported formats**: PDF (`.pdf`), EPUB (`.epub`), Word (`.doc`, `.docx`), Markdown (`.md`), Plain text (`.txt`)
- Content extraction preserving heading structure and paragraph breaks
- Metadata extraction and storage per document:
  - Original filename
  - File format
  - Upload timestamp
  - Page count (PDF/EPUB) or character count (TXT/MD)
  - Processing status: `pending` → `extracting` → `chunking` → `embedding` → `indexed` | `error`
- Visual progress feedback per file showing the current processing step
- Processing is fully asynchronous and does not block the chat interface

### RF-02 — RAG Processing Pipeline

After upload, the backend automatically executes the following pipeline per document:

1. **Extract**: parse raw text from the source format, preserving page/section metadata
2. **Split**: divide text into child chunks (~300 tokens, ~50 token overlap) and parent chunks (~1000 tokens)
3. **Embed**: generate vector embeddings for each child chunk via `nomic-embed-text`
4. **Index**: store child chunk vectors + parent chunk text + metadata (filename, page number, chunk position) in Qdrant
5. **Register**: save document metadata record in SQLite

### RF-03 — Chat with In-Session Memory

- Multi-turn conversation: the agent maintains the full message history for the duration of the browser session
- History is stored **in memory only** (Python process). Closing or refreshing the browser tab starts a completely new session with no history
- Each browser session generates a unique `session_id` (UUID) on first load; this ID is passed with every chat request
- Trivial messages ("Hello", "Thanks", "OK") are handled without querying the vector database
- Questions about book content trigger the full RAG pipeline

### RF-04 — Retrieval with Source Attribution

**Citation rules (mandatory):**
- Every factual claim in a response must include an inline citation badge (e.g., `[1]`)
- Each citation must identify: **book filename** + **page number** (PDFs/EPUBs) or **section heading** (MD/TXT/DOCX)
- When the response synthesizes information from multiple sources, all contributing books must be listed
- A collapsible "Sources Consulted" block appears at the end of every RAG-generated response, listing each source with the extracted text snippet

**Citation display (on click/hover):**
- Clicking a citation badge opens a side panel or popover showing:
  - Book title (filename)
  - Page number or section
  - The verbatim text excerpt used (the parent chunk)

### RF-05 — Knowledge Base Management

- List all indexed documents (filename, format icon, upload time, status badge)
- Remove a single document (deletes its vectors from Qdrant and its SQLite record)
- "Clear All" button to wipe the entire knowledge base (all Qdrant vectors + all SQLite records; uploaded files are also deleted)
- Visual indicator (spinner) on documents still being processed
- Error state with message if processing fails (e.g., corrupted file, unsupported encoding)

### RF-06 — Response Streaming

- Responses streamed token-by-token via **Server-Sent Events (SSE)**
- Animated agent status indicator during processing steps: `Searching documents...` → `Analyzing excerpts...` → `Generating response...`
- "Stop" button to interrupt an in-progress response
- Ollama model warm-up status shown on first load (models may take 10–30s to load into RAM)

---

## 4. Non-Functional Requirements

| Category | Requirement | Target |
|----------|-------------|--------|
| Performance | Vector search latency | < 100ms for a base of up to 50 books (~500k chunks) |
| Performance | LLM first-token latency | < 30s on CPU-only (16GB RAM, quantized model) |
| Availability | Container resilience | All services with `restart: unless-stopped` |
| Security | Network isolation | Inter-container communication on internal Docker network only; only ports 3000 (UI) and 8000 (API) exposed to host |
| Portability | GPU/CPU fallback | Ollama automatically uses CPU when vRAM is insufficient |
| Persistence | Data survival | Volumes persist data across `docker-compose restart`; cleared only with `docker-compose down -v` |
| Usability | Responsive layout | Functional on screens ≥ 1280px wide |
| Usability | Model status feedback | Clear visual indicator when Ollama models are loading, ready, or unavailable |

---

## 5. System Architecture

### 5.1 Container Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                       Docker Internal Network                     │
│                                                                  │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐   ┌──────────┐  │
│  │ frontend │────▶│ backend  │────▶│  qdrant  │   │  ollama  │  │
│  │ Next.js  │     │ FastAPI  │────▶│ (vectors)│   │  (LLM +  │  │
│  │          │     │ LangGraph│     │          │   │  embed)  │  │
│  │ :3000    │     │ :8000    │     │ :6333    │   │ :11434   │  │
│  └──────────┘     └──────────┘     └──────────┘   └──────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
       ▲                   ▲
   Host :3000          Host :8000
   (browser)         (debug only)
```

### 5.2 Docker Services

| Service | Base Image | Role | Host Port |
|---------|-----------|------|-----------|
| `frontend` | `node:20-alpine` | Next.js web interface | 3000 |
| `backend` | `python:3.11-slim` | FastAPI + LangGraph agent | 8000 |
| `qdrant` | `qdrant/qdrant:latest` | Vector database | Internal only (6333) |
| `ollama` | `ollama/ollama:latest` | LLM inference + embeddings | Internal only (11434) |

### 5.3 Persistent Volumes

| Volume Name | Service | Internal Path | Contents |
|-------------|---------|---------------|----------|
| `ollama_data` | ollama | `/root/.ollama` | Downloaded models (LLM + embedding) |
| `qdrant_data` | qdrant | `/qdrant/storage` | Vector collections and indexes |
| `backend_uploads` | backend | `/app/uploads` | Original uploaded book files |
| `backend_db` | backend | `/app/data/db.sqlite` | Document metadata (SQLite) |

> **Session reset workflow**: To start a completely fresh study session, run:
> ```bash
> docker-compose down -v   # removes all volumes (vectors, uploads, metadata)
> docker-compose up -d     # starts fresh environment
> ```

### 5.4 Environment Configuration (`.env`)

```env
# Ollama
OLLAMA_HOST=http://ollama:11434
LLM_MODEL=phi3.5:mini-instruct
EMBED_MODEL=nomic-embed-text
OLLAMA_NUM_GPU=1          # Set to 0 to force CPU-only

# Qdrant
QDRANT_HOST=http://qdrant:6333
QDRANT_COLLECTION=books

# Backend
UPLOAD_DIR=/app/uploads
DB_PATH=/app/data/db.sqlite
MAX_UPLOAD_SIZE_MB=200
CHUNK_SIZE=300
CHUNK_OVERLAP=50
PARENT_CHUNK_SIZE=1000
TOP_K_RESULTS=6
```

---

## 6. Technology Stack

### 6.1 Backend

| Technology | Min Version | Role |
|------------|-------------|------|
| Python | 3.11 | Primary language |
| FastAPI | 0.110+ | Async web framework; SSE streaming |
| LangChain | 0.2+ | RAG components (loaders, splitters, retrievers) |
| LangGraph | 0.1+ | Agent state-graph orchestration |
| Qdrant Client | 1.9+ | Vector database integration |
| FastEmbed | 0.2+ | CPU-optimized embedding generation (no PyTorch) |
| Pydantic v2 | 2.0+ | Data validation and API schemas |
| SQLModel | 0.0.18+ | Document metadata persistence (SQLite) |
| python-multipart | — | Multipart file upload support |
| pypdf | 3.0+ | PDF text extraction with page metadata |
| ebooklib | 0.18+ | EPUB parsing |
| beautifulsoup4 | 4.0+ | HTML content extraction from EPUB internals |
| python-docx | 1.0+ | `.docx` and `.doc` text extraction |

**Not needed** (simplified by requirements):
- No auth library (single-user, no authentication)
- No chat history database (in-memory only per session)
- No WebSocket library (SSE is sufficient for one-way streaming)

### 6.2 Frontend

| Technology | Min Version | Role |
|------------|-------------|------|
| Next.js | 14+ (App Router) | React framework with native SSE/streaming support |
| TypeScript | 5+ | Static typing |
| shadcn/ui | — | UI component library (source-owned) |
| Tailwind CSS | 3+ | Utility-first styling |
| Radix UI | — | Accessible primitives (WAI-ARIA) for dialogs, popovers, tabs |
| Framer Motion | 10+ | Animations: streaming text, skeleton loaders, transitions |
| React Hook Form + Zod | — | Upload form with client-side validation |

**Language**: English (UI copy, labels, placeholders, error messages)

### 6.3 AI Models (via Ollama)

| Type | Selected Model | RAM Usage | Notes |
|------|---------------|-----------|-------|
| LLM (chat) | `phi3.5:mini-instruct` | ~2.5 GB RAM | 3.8B params, Q4 quantized; strong reasoning, fast on CPU |
| Embeddings | `nomic-embed-text` | ~300 MB RAM | 768-dim vectors; excellent for English text; CPU-efficient |

**GPU configuration note**: With 2 GB vRAM, Ollama will attempt to offload as many model layers as possible to GPU and process the remainder on CPU RAM. This is handled automatically. The `phi3.5:mini-instruct` model may partially benefit from GPU offloading.

> **Alternative if phi3.5 is too slow**: `llama3.2:1b-instruct-q4_0` (~900 MB RAM, much faster, lower quality)

**Model pull on first startup** (requires internet):
```bash
# Handled automatically by an init container or startup script
ollama pull phi3.5:mini-instruct
ollama pull nomic-embed-text
```

---

## 7. Agent Architecture (Backend)

### 7.1 Orchestration: LangGraph + ReAct Pattern

The agent is a **stateful graph** built with LangGraph. Each node is a discrete function; edges define conditional transitions based on the node's output.

```
[User Message]
      │
      ▼
[Node: Classifier]
  ├── trivial/greeting ─────────────────────────────▶ [Node: Direct Reply] ──▶ [Stream Output]
  └── document question ──▶ [Node: Query Rewriter]
                                      │
                                      ▼
                              [Node: Hybrid Retriever]
                              (dense + sparse search)
                                      │
                                      ▼
                              [Node: Context Evaluator]
                              ├── sufficient ──▶ [Node: Generator] ──▶ [Stream Output]
                              └── insufficient ──▶ [Node: Query Rewriter]
                                                   (max 2 retry attempts)
```

**State object** passed between nodes:
```python
class AgentState(TypedDict):
    session_id: str
    messages: list[BaseMessage]      # in-memory chat history
    current_query: str
    rewritten_query: str | None
    retrieved_chunks: list[Document]
    retry_count: int
```

### 7.2 Retrieval Strategy: Hybrid Search

Two complementary search methods are combined for every query:

| Method | Mechanism | Strength |
|--------|-----------|----------|
| **Dense search** | Cosine similarity between query embedding and chunk embeddings | Semantic meaning, paraphrased concepts |
| **Sparse search** | BM25 keyword matching | Exact terms, book titles, author names, technical jargon |

Results from both methods are merged and the top-K (default: 6) most relevant parent chunks are sent to the LLM.

### 7.3 Chunking Strategy

| Chunk Type | Size | Purpose |
|------------|------|---------|
| Child chunk | ~300 tokens, 50 overlap | Used for precise vector search |
| Parent chunk | ~1000 tokens | Provided to the LLM as context (more coherent excerpt) |

Metadata stored per chunk:
- `source_filename`: original book file name
- `page_number`: page number (PDF/EPUB) or `null` (TXT/MD/DOCX without page breaks)
- `section_heading`: nearest heading above the chunk (when available)
- `chunk_index`: position within the document

### 7.4 Citation Format Rules

The LLM is instructed via system prompt to follow these citation rules:

1. **Direct answer from a single source**: `"...the author argues that X [1]."` → Sources: `[1] Clean Code (Martin) — p. 47`
2. **Synthesis from multiple sources**: `"Different authors approach this differently [1][2][3]."` → All sources listed
3. **Summary request**: Response begins with a "Based on the following books:" header listing all consulted titles
4. **No relevant content found**: Agent explicitly states it could not find information on the topic in the current knowledge base, rather than hallucinating

### 7.5 API Endpoints (FastAPI)

| Method | Route | Description | Response |
|--------|-------|-------------|----------|
| `POST` | `/api/documents/upload` | Upload one or more files | `{ document_id, filename, status }` |
| `GET` | `/api/documents` | List all indexed documents | Array of document records |
| `GET` | `/api/documents/{id}` | Get single document status | Document record |
| `DELETE` | `/api/documents/{id}` | Delete document + its vectors | `204 No Content` |
| `DELETE` | `/api/documents` | Clear entire knowledge base | `204 No Content` |
| `POST` | `/api/chat/stream` | Send message, receive SSE stream | SSE: tokens + citations |
| `GET` | `/api/health` | System and model status | `{ ollama, qdrant, models_loaded }` |

**SSE stream format** for `/api/chat/stream`:
```
data: {"type": "status", "text": "Searching documents..."}
data: {"type": "token", "text": "The "}
data: {"type": "token", "text": "answer "}
data: {"type": "citation", "id": 1, "source": "CleanCode.pdf", "page": 47, "excerpt": "..."}
data: {"type": "done", "sources": [...]}
```

---

## 8. User Interface (Frontend)

### 8.1 Layout

Two-column layout with persistent left sidebar:

```
┌──────────────────────────────────────────────────────────────┐
│  📚 Local Book Library                     [● Models Ready]  │
├────────────────────┬─────────────────────────────────────────┤
│                    │                                         │
│  YOUR BOOKS        │  CHAT                                   │
│  ──────────────    │  ──────────────────────────────────     │
│  📄 CleanCode.pdf  │  You: What does Martin say about        │
│     indexed  [✕]   │       functions?                        │
│                    │                                         │
│  📘 DDIA.epub      │  Agent: Martin argues that functions    │
│     indexed  [✕]   │  should do one thing only [1]. He       │
│                    │  also recommends keeping them           │
│  📝 notes.md       │  short [2].                             │
│     indexed  [✕]   │                                         │
│                    │  ▼ Sources Consulted (2)                │
│  ─────────────     │  ┌──────────────────────────────────┐   │
│  [+ Upload Books]  │  │ [1] CleanCode.pdf — p. 35        │   │
│                    │  │ "Functions should do one thing…" │   │
│  [🗑 Clear All]    │  │ [2] CleanCode.pdf — p. 38        │   │
│                    │  │ "The first rule of functions…"   │   │
│                    │  └──────────────────────────────────┘   │
│                    │                                         │
│                    │  [Ask about your books...] [▶ Send]     │
└────────────────────┴─────────────────────────────────────────┘
```

### 8.2 Key Components

| Component | Behavior |
|-----------|----------|
| `DocumentSidebar` | Lists all indexed books with status badge and delete button; shows spinner during processing |
| `UploadZone` | Drag-and-drop area; accepts PDF, EPUB, DOC, DOCX, MD, TXT; shows per-file progress with current step label |
| `ChatThread` | Scrollable message history; renders Markdown; clears on page refresh |
| `MessageBubble` | User or agent message bubble; agent bubbles support inline citation badges `[1]` |
| `CitationBadge` | Clickable `[n]` badge; opens `SourcePopover` on click |
| `SourcePopover` | Shows: book filename, page number or section, verbatim text excerpt |
| `SourcesPanel` | Collapsible section at the bottom of each agent response listing all consulted sources |
| `AgentStatusBar` | Animated label showing current agent step during generation ("Searching...", "Analyzing 4 excerpts...") |
| `ModelStatusIndicator` | Header badge: "Models Loading" (yellow) / "Ready" (green) / "Unavailable" (red) |
| `StopButton` | Visible during streaming; cancels the SSE connection and stops generation |

### 8.3 Interface States

| State | Description |
|-------|-------------|
| **Empty library** | Welcome screen with upload instructions; chat input disabled |
| **Uploading** | Progress bar per file with step label; chat remains usable for already-indexed books |
| **Processing** | Spinner next to document name; document excluded from search until `indexed` |
| **Ready** | Chat input active; all indexed documents available for search |
| **Agent thinking** | `AgentStatusBar` animated; `StopButton` visible |
| **Streaming response** | Tokens appear progressively; citation badges appear as sources are identified |
| **Model loading** | Yellow indicator in header; chat input disabled with tooltip "Models are loading, please wait" |
| **Model unavailable** | Red indicator; error banner with troubleshooting hint |

### 8.4 Session Behavior

- `session_id` (UUID v4) is generated **client-side** on page load and stored in `sessionStorage`
- The ID is sent as a header (`X-Session-ID`) with every chat request
- The backend stores the message history in an in-memory dictionary keyed by `session_id`
- Closing the tab, refreshing, or navigating away discards the session; next load generates a new ID and starts fresh
- No chat history is written to disk

---

## 9. Document Processing Detail

### 9.1 Format-Specific Extraction

| Format | Library | Page Metadata | Notes |
|--------|---------|---------------|-------|
| `.pdf` | `pypdf` | Page number per chunk | Extracts text layer; scanned PDFs without OCR will produce empty/garbled text |
| `.epub` | `ebooklib` + `bs4` | Chapter/section heading | HTML content extracted and cleaned; images ignored |
| `.docx` | `python-docx` | Section heading (if present) | Paragraph-level extraction |
| `.doc` | `python-docx` (via conversion) | Section heading | Requires `antiword` or `libreoffice` in container for legacy `.doc` |
| `.md` | Built-in | Heading hierarchy | Headings parsed as section metadata |
| `.txt` | Built-in | None | No structural metadata; chunked by character count |

> **Note on scanned PDFs**: If a PDF was created by scanning physical pages (no text layer), the extracted text will be empty or garbage characters. The system will report an error and the document will not be indexed. OCR support (e.g., `tesseract`) is **out of scope** for v1.

### 9.2 Metadata Schema (SQLite, via SQLModel)

```python
class Document(SQLModel, table=True):
    id: str                  # UUID
    filename: str
    file_format: str         # pdf | epub | docx | doc | md | txt
    upload_time: datetime
    status: str              # pending | extracting | chunking | embedding | indexed | error
    error_message: str | None
    page_count: int | None
    chunk_count: int | None
    qdrant_ids: str          # JSON array of Qdrant point IDs
```

---

## 10. Operational Workflow

### 10.1 First-Time Setup

```bash
# 1. Clone the repository
git clone <repo-url> && cd <repo-dir>

# 2. Copy environment template
cp .env.example .env

# 3. Start all services (downloads models on first run — requires internet)
docker-compose up -d

# 4. Wait for models to download (~2–4 GB total)
docker-compose logs -f ollama   # watch download progress

# 5. Open browser
open http://localhost:3000
```

### 10.2 Starting a Study Session

```bash
# Start containers (models already downloaded, starts in seconds)
docker-compose up -d

# Open browser → upload books → start chatting
open http://localhost:3000
```

### 10.3 Resetting Between Study Sessions

```bash
# Remove all volumes (books, vectors, metadata) — start completely fresh
docker-compose down -v

# Next session
docker-compose up -d
```

### 10.4 Stopping Without Losing Data

```bash
# Stop containers but keep all volumes (books remain indexed)
docker-compose stop

# Resume later — all books are still available
docker-compose start
```

---

## 11. Out of Scope (v1)

The following features are explicitly excluded from the initial version:

| Feature | Reason |
|---------|--------|
| User authentication | Single-user local system |
| Book collections / categories | Not needed; session is ephemeral by design |
| Chat history persistence across sessions | Not needed; in-memory only by design |
| Full PDF viewer / PDF rendering | Text snippet citation is sufficient |
| OCR for scanned PDFs | Significant complexity; excluded from v1 |
| Multi-user / multi-session concurrency | Single-user by design |
| Cloud deployment | Explicitly out of scope; local-only |
| Fine-tuning models | Out of scope; uses pre-trained models only |
| Web search / external tool use | All answers must come from uploaded books only |
