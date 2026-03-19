# Execution Plan — Local RAG Library with Docker

**Version:** 1.0
**Date:** 2026-03-16
**Reference Spec:** `SPEC.md` v2.0
**Execution Model:** Tasks designed to be executed by AI coding agents. Each task is self-contained with explicit inputs, outputs, and dependencies.

---

## How to Read This Document

- **Phase**: logical group of related tasks. Phases are sequential (each phase requires the prior to be complete).
- **Parallel group**: tasks within the same phase with no inter-dependencies. An agent can work on each task in a parallel group simultaneously.
- **Depends on**: task IDs that must be fully completed before this task can start.
- **Complexity**: `Low` (< 1h), `Medium` (1–3h), `High` (3h+) — estimates for an AI agent with full context.
- **Type**: `Setup` | `Coding` | `Integration` | `Testing` | `Documentation`

---

## Project Directory Structure (target)

```
rag-library/
├── docker-compose.yml
├── .env.example
├── .env                          # gitignored
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── config.py             # Settings from env vars (pydantic-settings)
│   │   ├── database.py           # SQLite/SQLModel setup
│   │   ├── models/
│   │   │   └── document.py       # SQLModel Document table
│   │   ├── schemas/
│   │   │   ├── document.py       # Pydantic request/response schemas
│   │   │   └── chat.py           # Chat request/response schemas
│   │   ├── routers/
│   │   │   ├── documents.py      # /api/documents/* endpoints
│   │   │   ├── chat.py           # /api/chat/stream endpoint
│   │   │   └── health.py         # /api/health endpoint
│   │   ├── services/
│   │   │   ├── extractors/
│   │   │   │   ├── base.py       # Abstract extractor interface
│   │   │   │   ├── pdf.py        # pypdf extractor
│   │   │   │   ├── epub.py       # ebooklib + bs4 extractor
│   │   │   │   ├── docx.py       # python-docx extractor
│   │   │   │   ├── markdown.py   # MD/TXT extractor
│   │   │   │   └── factory.py    # ExtractorFactory (format → extractor)
│   │   │   ├── chunker.py        # Child/parent chunk splitting
│   │   │   ├── embedder.py       # FastEmbed wrapper (nomic-embed-text)
│   │   │   ├── vector_store.py   # Qdrant client + index/search operations
│   │   │   ├── ingestion.py      # Full async pipeline orchestration
│   │   │   └── ollama_client.py  # Ollama LLM chat + health check
│   │   └── agent/
│   │       ├── state.py          # AgentState TypedDict
│   │       ├── nodes.py          # All LangGraph node functions
│   │       ├── graph.py          # Graph assembly + compilation
│   │       └── prompts.py        # System prompt + citation instructions
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx        # Root layout
│   │   │   └── page.tsx          # Main page (two-column layout)
│   │   ├── components/
│   │   │   ├── ui/               # shadcn/ui generated components
│   │   │   ├── ModelStatusIndicator.tsx
│   │   │   ├── DocumentSidebar.tsx
│   │   │   ├── UploadZone.tsx
│   │   │   ├── ChatThread.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── CitationBadge.tsx
│   │   │   ├── SourcePopover.tsx
│   │   │   ├── SourcesPanel.tsx
│   │   │   ├── AgentStatusBar.tsx
│   │   │   ├── StopButton.tsx
│   │   │   └── ChatInput.tsx
│   │   ├── hooks/
│   │   │   ├── useSession.ts     # sessionId generation + sessionStorage
│   │   │   ├── useDocuments.ts   # Document list + upload + delete state
│   │   │   └── useChat.ts        # SSE chat logic + streaming state
│   │   ├── lib/
│   │   │   ├── api.ts            # Typed API client (fetch wrapper)
│   │   │   └── utils.ts          # cn() + helpers
│   │   └── types/
│   │       ├── document.ts       # Document types
│   │       └── chat.ts           # Message, Citation, SSE event types
└── tests/
    ├── backend/
    │   ├── unit/
    │   │   ├── test_extractors.py
    │   │   ├── test_chunker.py
    │   │   └── test_schemas.py
    │   └── integration/
    │       ├── test_ingestion_pipeline.py
    │       └── test_chat_endpoint.py
    └── frontend/
        └── components/
            └── MessageBubble.test.tsx
```

---

## Phase 0 — Project Scaffolding

> **Goal**: create the repository skeleton, Docker infrastructure, and configuration files. Nothing should compile or run yet — just the structure.
> **All tasks in this phase are sequential** (each depends on the previous).

---

### T001 — Repository Structure
**Type:** Setup | **Complexity:** Low | **Depends on:** — | **Parallel with:** —

Create the top-level directory tree as defined in "Project Directory Structure" above.
All directories must be created with `.gitkeep` placeholder files where needed.
Create `.gitignore` including: `.env`, `__pycache__`, `node_modules`, `*.pyc`, `.next`, `uploads/`.

**Output files:**
- Full directory tree (empty files/gitkeeps)
- `.gitignore`

---

### T002 — Docker Compose + Networking
**Type:** Setup | **Complexity:** Medium | **Depends on:** T001 | **Parallel with:** —

Create `docker-compose.yml` defining:
- 4 services: `ollama`, `qdrant`, `backend`, `frontend`
- 1 internal bridge network: `rag_network`
- 4 named volumes: `ollama_data`, `qdrant_data`, `backend_uploads`, `backend_db`
- Service dependencies (`backend` depends on `qdrant` and `ollama`; `frontend` depends on `backend`)
- `restart: unless-stopped` on all services
- Port mappings: `3000:3000` (frontend), `8000:8000` (backend); qdrant and ollama on internal network only
- GPU configuration block for `ollama` service (NVIDIA runtime, conditional via profile or comment)
- `env_file: .env` for `backend` and `frontend` services
- `ollama` service must include an entrypoint script that pulls models on startup:
  ```
  ollama serve & sleep 5 && ollama pull ${LLM_MODEL} && ollama pull ${EMBED_MODEL} && wait
  ```

**Output files:**
- `docker-compose.yml`

---

### T003 — Backend Dockerfile
**Type:** Setup | **Complexity:** Low | **Depends on:** T001 | **Parallel with:** T004

Based on `python:3.11-slim`. Must:
- Install system dependencies: `build-essential`, `libpoppler-cpp-dev` (for pypdf), `antiword` (for legacy .doc)
- Copy `requirements.txt` and run `pip install --no-cache-dir`
- Copy `app/` directory
- Expose port 8000
- CMD: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

**Output files:**
- `backend/Dockerfile`
- `backend/requirements.txt` (with all backend dependencies from SPEC Section 6.1, pinned to compatible versions)

---

### T004 — Frontend Dockerfile
**Type:** Setup | **Complexity:** Low | **Depends on:** T001 | **Parallel with:** T003

Multi-stage build based on `node:20-alpine`:
- Stage 1 (`deps`): install dependencies from `package.json`
- Stage 2 (`builder`): build Next.js app (`npm run build`)
- Stage 3 (`runner`): copy built output, expose port 3000, CMD `node server.js`

Also create `frontend/.dockerignore`.

**Output files:**
- `frontend/Dockerfile`
- `frontend/.dockerignore`

---

### T005 — Environment Configuration
**Type:** Setup | **Complexity:** Low | **Depends on:** T002 | **Parallel with:** —

Create `.env.example` with all variables from SPEC Section 5.4 and their default values.
All variables must include a descriptive comment above them.
Create a copy as `.env` (will be gitignored).

Also create `backend/app/config.py` using `pydantic-settings`:
```python
class Settings(BaseSettings):
    ollama_host: str
    llm_model: str
    embed_model: str
    qdrant_host: str
    qdrant_collection: str
    upload_dir: str
    db_path: str
    max_upload_size_mb: int = 200
    chunk_size: int = 300
    chunk_overlap: int = 50
    parent_chunk_size: int = 1000
    top_k_results: int = 6
    model_config = SettingsConfigDict(env_file=".env")
```

**Output files:**
- `.env.example`
- `.env`
- `backend/app/config.py`

---

## Phase 1 — Backend Foundation

> **Goal**: FastAPI app boots, health endpoint responds, database initializes.
> **Parallel group A**: T006, T007, T008 can all be worked on simultaneously.

---

### T006 — FastAPI App Skeleton
**Type:** Coding | **Complexity:** Low | **Depends on:** T005 | **Parallel with:** T007, T008

Create `backend/app/main.py`:
- Initialize FastAPI app with title, version, lifespan context manager
- Register routers: `documents`, `chat`, `health` (all under `/api` prefix)
- Configure CORS: allow `http://localhost:3000`
- Lifespan: on startup, initialize SQLite database, verify Qdrant connection, verify Ollama connectivity
- Global exception handler for unhandled errors (returns `{ "error": "Internal server error" }`)

**Output files:**
- `backend/app/main.py`

---

### T007 — Database Schema (SQLModel)
**Type:** Coding | **Complexity:** Low | **Depends on:** T005 | **Parallel with:** T006, T008

Create `backend/app/models/document.py` with the `Document` SQLModel table as defined in SPEC Section 9.2.
Create `backend/app/database.py`:
- SQLite engine creation using `db_path` from settings
- `create_db_and_tables()` function called at startup
- `get_session()` dependency for use in FastAPI routes

**Output files:**
- `backend/app/models/document.py`
- `backend/app/database.py`

---

### T008 — Pydantic API Schemas
**Type:** Coding | **Complexity:** Low | **Depends on:** T005 | **Parallel with:** T006, T007

Create `backend/app/schemas/document.py`:
- `DocumentResponse`: id, filename, file_format, upload_time, status, error_message, page_count, chunk_count
- `DocumentListResponse`: list of `DocumentResponse`
- `UploadResponse`: document_id, filename, status

Create `backend/app/schemas/chat.py`:
- `ChatRequest`: session_id (str), message (str)
- `Citation`: id (int), source_filename (str), page_number (int | None), section_heading (str | None), excerpt (str)
- `SSEEvent` (for documentation): type (Literal["status","token","citation","done","error"]), text (str | None), citation (Citation | None), sources (list[Citation] | None)

**Output files:**
- `backend/app/schemas/document.py`
- `backend/app/schemas/chat.py`

---

### T009 — Health Endpoint
**Type:** Coding | **Complexity:** Low | **Depends on:** T006, T007 | **Parallel with:** —

Create `backend/app/routers/health.py`:
- `GET /api/health` → checks Qdrant connection (HTTP GET to qdrant health endpoint), checks Ollama connection (HTTP GET to ollama/api/tags), returns:
  ```json
  {
    "status": "ok" | "degraded",
    "qdrant": "connected" | "unreachable",
    "ollama": "connected" | "unreachable",
    "models_loaded": ["phi3.5:mini-instruct", "nomic-embed-text"] | []
  }
  ```
- Uses `httpx.AsyncClient` for async HTTP calls

**Output files:**
- `backend/app/routers/health.py`

---

## Phase 2 — Document Extractors

> **Goal**: extract clean text + page/section metadata from each supported file format.
> **Parallel group B**: T010–T014 are fully independent and can run simultaneously.
> T015 (factory) depends on all of them completing.

---

### T010 — PDF Extractor
**Type:** Coding | **Complexity:** Medium | **Depends on:** T005 | **Parallel with:** T011, T012, T013, T014

Create `backend/app/services/extractors/base.py`:
```python
@dataclass
class ExtractedChunk:
    text: str
    page_number: int | None
    section_heading: str | None
    chunk_index: int

@dataclass
class ExtractionResult:
    chunks: list[ExtractedChunk]
    page_count: int | None
    metadata: dict

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str) -> ExtractionResult: ...
    @abstractmethod
    def supports(self, file_extension: str) -> bool: ...
```

Create `backend/app/services/extractors/pdf.py` using `pypdf`:
- Extract text per page, preserving page number
- Detect and skip pages that appear to be scanned (text length < 50 chars per page → flag as potentially scanned)
- Return `ExtractionResult` with page_count set
- If all pages are empty/scanned: raise `ExtractionError("PDF appears to be scanned. OCR is not supported in v1.")`

**Output files:**
- `backend/app/services/extractors/base.py`
- `backend/app/services/extractors/pdf.py`

---

### T011 — EPUB Extractor
**Type:** Coding | **Complexity:** Medium | **Depends on:** T005 | **Parallel with:** T010, T012, T013, T014

Create `backend/app/services/extractors/epub.py` using `ebooklib` + `beautifulsoup4`:
- Iterate over `ITEM_DOCUMENT` items in the EPUB
- Parse HTML content with BeautifulSoup, extract text stripping all tags
- Use item `title` or first `<h1>`/`<h2>` as `section_heading`
- Set `page_number = None` (EPUBs have no fixed pages); use item index as chapter position
- Assign sequential `chunk_index`

**Output files:**
- `backend/app/services/extractors/epub.py`

---

### T012 — DOCX/DOC Extractor
**Type:** Coding | **Complexity:** Medium | **Depends on:** T005 | **Parallel with:** T010, T011, T013, T014

Create `backend/app/services/extractors/docx.py` using `python-docx`:
- Extract paragraph text, tracking heading styles (`Heading 1`, `Heading 2`) as `section_heading`
- Group paragraphs into logical sections between headings
- Set `page_number = None` (python-docx does not expose page breaks reliably)
- Handle `.doc` legacy format: attempt conversion via `subprocess` call to `antiword`; if `antiword` not available, raise `ExtractionError("Legacy .doc files require antiword. Please convert to .docx.")`

**Output files:**
- `backend/app/services/extractors/docx.py`

---

### T013 — Markdown / TXT Extractor
**Type:** Coding | **Complexity:** Low | **Depends on:** T005 | **Parallel with:** T010, T011, T012, T014

Create `backend/app/services/extractors/markdown.py`:
- For `.md`: parse headings (`# `, `## `, `### `) to populate `section_heading`; split text at heading boundaries
- For `.txt`: split into fixed-size text blocks (~2000 chars); `section_heading = None`, `page_number = None`
- Both: `page_count = None`

**Output files:**
- `backend/app/services/extractors/markdown.py`

---

### T014 — Extractor Factory
**Type:** Coding | **Complexity:** Low | **Depends on:** T005 | **Parallel with:** T010, T011, T012, T013

Create `backend/app/services/extractors/factory.py`:
- `ExtractorFactory` class with `get_extractor(filename: str) -> BaseExtractor`
- Maps extensions to extractor classes: `.pdf` → `PdfExtractor`, `.epub` → `EpubExtractor`, `.docx`/`.doc` → `DocxExtractor`, `.md`/`.txt` → `MarkdownExtractor`
- Raises `UnsupportedFormatError` for unknown extensions

**Output files:**
- `backend/app/services/extractors/factory.py`
- `backend/app/services/extractors/__init__.py`

---

### T015 — Chunking Service
**Type:** Coding | **Complexity:** Medium | **Depends on:** T010, T011, T012, T013, T014 | **Parallel with:** T016, T017

Create `backend/app/services/chunker.py`:

Implements the **Parent Document strategy**:
1. Takes `ExtractionResult` as input
2. For each extracted section/page block, creates:
   - **Parent chunk**: up to `parent_chunk_size` tokens — stored as context text only
   - **Child chunks**: the parent chunk split into `chunk_size` pieces with `chunk_overlap` — used for embedding/search
3. Each child chunk stores a reference to its parent chunk text
4. Returns list of `ChunkRecord`:
   ```python
   @dataclass
   class ChunkRecord:
       child_text: str       # text to embed and search
       parent_text: str      # text to send to LLM as context
       source_filename: str
       page_number: int | None
       section_heading: str | None
       chunk_index: int
       document_id: str
   ```
Uses `langchain_text_splitters.RecursiveCharacterTextSplitter` for splitting.

**Output files:**
- `backend/app/services/chunker.py`

---

## Phase 3 — Vector Store & Embeddings

> **Goal**: Qdrant collection initialized, embeddings generated, hybrid search working.
> **Parallel group C**: T016 and T017 are independent; T018 depends on both; T019 depends on T018.

---

### T016 — Qdrant Client & Collection Setup
**Type:** Coding | **Complexity:** Medium | **Depends on:** T005 | **Parallel with:** T015, T017

Create `backend/app/services/vector_store.py` (first part):
- Initialize `QdrantClient` using `qdrant_host` from settings
- `initialize_collection()`: create collection if it doesn't exist with:
  - Vector size: 768 (nomic-embed-text output dimension)
  - Distance: `Cosine`
  - Enable sparse vectors for hybrid search (BM25 via `models.SparseVectorParams`)
- `collection_exists() -> bool`
- `delete_points_by_document_id(document_id: str)`: filter delete by `document_id` payload field
- `clear_collection()`: delete and recreate the collection

Call `initialize_collection()` in the FastAPI lifespan startup.

**Output files:**
- `backend/app/services/vector_store.py` (partial — collection management section)

---

### T017 — Embedding Service (FastEmbed)
**Type:** Coding | **Complexity:** Low | **Depends on:** T005 | **Parallel with:** T015, T016

Create `backend/app/services/embedder.py`:
- Singleton `EmbeddingService` class, initialized once at startup
- Uses `fastembed.TextEmbedding` with model `nomic-embed-text`
- `embed_texts(texts: list[str]) -> list[list[float]]`: batch embedding with progress logging
- `embed_query(text: str) -> list[float]`: single query embedding
- Lazy initialization (download model on first call, then cache)

**Output files:**
- `backend/app/services/embedder.py`

---

### T018 — Qdrant Indexing
**Type:** Coding | **Complexity:** Medium | **Depends on:** T016, T017 | **Parallel with:** —

Add to `backend/app/services/vector_store.py` (second part):
- `index_chunks(chunks: list[ChunkRecord]) -> list[str]`:
  - Generate embeddings for all `child_text` fields in batch
  - Build Qdrant `PointStruct` list with:
    - Dense vector: child text embedding
    - Payload: `{ document_id, source_filename, page_number, section_heading, chunk_index, parent_text, child_text }`
  - Upload points in batches of 100
  - Return list of Qdrant point UUIDs

**Output files:**
- `backend/app/services/vector_store.py` (complete)

---

### T019 — Hybrid Search
**Type:** Coding | **Complexity:** High | **Depends on:** T018 | **Parallel with:** T020

Add `search(query: str, top_k: int) -> list[SearchResult]` to `vector_store.py`:

**Dense search**: embed query → cosine similarity search → top `top_k * 2` results

**Sparse search (BM25)**: use Qdrant's built-in sparse vector support or `rank_bm25` library against stored child texts to produce sparse vector → search top `top_k * 2` results

**Fusion**: Reciprocal Rank Fusion (RRF) to merge dense and sparse result lists → take top `top_k` final results

Return list of `SearchResult`:
```python
@dataclass
class SearchResult:
    source_filename: str
    page_number: int | None
    section_heading: str | None
    parent_text: str      # context for LLM
    child_text: str       # matched excerpt for citation display
    score: float
    document_id: str
```

**Output files:**
- `backend/app/services/vector_store.py` (complete with search)

---

## Phase 4 — Ingestion Pipeline & Document API

> **Goal**: documents can be uploaded, processed, listed, and deleted via API.
> T020 must come first; T021–T024 can be parallelized after T020.

---

### T020 — Async Ingestion Pipeline
**Type:** Coding | **Complexity:** High | **Depends on:** T015, T018, T007 | **Parallel with:** T025, T026

Create `backend/app/services/ingestion.py`:

```python
async def ingest_document(
    file_path: str,
    document_id: str,
    filename: str,
    db_session: Session
) -> None
```

Pipeline steps with status updates written to SQLite after each step:
1. `status = "extracting"` → call `ExtractorFactory.get_extractor(filename).extract(file_path)`
2. `status = "chunking"` → call `chunker.chunk(extraction_result, document_id, filename)`
3. `status = "embedding"` → call `vector_store.index_chunks(chunks)`
4. `status = "indexed"`, set `chunk_count`, `page_count`, store `qdrant_ids` as JSON
5. On any exception: `status = "error"`, store `error_message`

The function runs in a background task (FastAPI `BackgroundTasks`), not blocking the upload response.

**Output files:**
- `backend/app/services/ingestion.py`

---

### T021 — Document Upload Endpoint
**Type:** Coding | **Complexity:** Medium | **Depends on:** T020 | **Parallel with:** T022, T023, T024

Create the upload route in `backend/app/routers/documents.py`:
- `POST /api/documents/upload` — accepts `multipart/form-data` with one or more files
- Validates file extension against allowed list
- Validates file size against `MAX_UPLOAD_SIZE_MB`
- Saves file to `UPLOAD_DIR/{document_id}_{filename}`
- Creates `Document` record in SQLite with `status = "pending"`
- Schedules `ingest_document()` as background task
- Returns `UploadResponse` immediately (does not wait for processing)

**Output files:**
- `backend/app/routers/documents.py` (upload route)

---

### T022 — Document List & Status Endpoint
**Type:** Coding | **Complexity:** Low | **Depends on:** T020 | **Parallel with:** T021, T023, T024

Add to `backend/app/routers/documents.py`:
- `GET /api/documents` → returns `DocumentListResponse` (all documents ordered by upload_time desc)
- `GET /api/documents/{id}` → returns single `DocumentResponse` or 404

**Output files:**
- `backend/app/routers/documents.py` (list + status routes added)

---

### T023 — Document Delete Endpoint
**Type:** Coding | **Complexity:** Low | **Depends on:** T020 | **Parallel with:** T021, T022, T024

Add to `backend/app/routers/documents.py`:
- `DELETE /api/documents/{id}`:
  1. Fetch document from SQLite (404 if not found)
  2. Call `vector_store.delete_points_by_document_id(id)`
  3. Delete uploaded file from disk
  4. Delete SQLite record
  5. Return `204 No Content`

**Output files:**
- `backend/app/routers/documents.py` (delete route added)

---

### T024 — Clear All Endpoint
**Type:** Coding | **Complexity:** Low | **Depends on:** T020 | **Parallel with:** T021, T022, T023

Add to `backend/app/routers/documents.py`:
- `DELETE /api/documents`:
  1. Call `vector_store.clear_collection()` (delete + recreate Qdrant collection)
  2. Delete all files in `UPLOAD_DIR`
  3. Delete all `Document` records from SQLite
  4. Return `204 No Content`

**Output files:**
- `backend/app/routers/documents.py` (complete)

---

## Phase 5 — LLM Integration

> **Goal**: Ollama client works, LLM produces streaming responses with citation-aware prompting.
> **Parallel group D**: T025, T026, T027 can run simultaneously. T025 is a prerequisite for T026.

---

### T025 — Ollama Client
**Type:** Coding | **Complexity:** Low | **Depends on:** T005 | **Parallel with:** T020, T027

Create `backend/app/services/ollama_client.py`:
- Async client using `httpx.AsyncClient` pointing to `OLLAMA_HOST`
- `check_health() -> dict`: GET `/api/tags`, return list of loaded model names
- `is_model_available(model_name: str) -> bool`: check if model appears in tags response
- `stream_chat(messages: list[dict], system_prompt: str) -> AsyncIterator[str]`:
  - POST to `/api/chat` with `stream: true`
  - Yield text tokens as they arrive (parse NDJSON response)

**Output files:**
- `backend/app/services/ollama_client.py`

---

### T026 — System Prompt & Citation Instructions
**Type:** Coding | **Complexity:** Medium | **Depends on:** T005 | **Parallel with:** T025, T027

Create `backend/app/agent/prompts.py`:

```python
SYSTEM_PROMPT = """
You are a research assistant with access to a personal library of books.
Your ONLY source of knowledge is the context provided below. Never use information outside of it.

CITATION RULES (mandatory — never skip):
1. Every factual statement must end with an inline citation: [1], [2], etc.
2. Citations must reference the exact source document and page number provided in the context.
3. If synthesizing from multiple sources, cite all of them: [1][3].
4. If the answer requires information not found in the context, say exactly:
   "I could not find information about this topic in the uploaded books."
5. Never guess, infer beyond the text, or fabricate page numbers.

After your response, output a JSON block (fenced as ```sources) listing every citation used:
[{"id": 1, "source_filename": "...", "page_number": ..., "section_heading": "...", "excerpt": "..."}]
"""

def build_context_block(search_results: list[SearchResult]) -> str:
    """Format retrieved chunks into a numbered context block for the prompt."""
    ...
```

**Output files:**
- `backend/app/agent/prompts.py`

---

### T027 — Agent State Definition
**Type:** Coding | **Complexity:** Low | **Depends on:** T005 | **Parallel with:** T025, T026

Create `backend/app/agent/state.py`:
```python
class AgentState(TypedDict):
    session_id: str
    messages: Annotated[list[BaseMessage], add_messages]
    current_query: str
    rewritten_query: str | None
    retrieved_chunks: list[SearchResult]
    retry_count: int
    is_trivial: bool
    final_response: str | None
    citations: list[dict]
```

**Output files:**
- `backend/app/agent/state.py`

---

## Phase 6 — LangGraph Agent

> **Goal**: the full agent graph is assembled and handles both trivial and document queries with streaming.
> **Parallel group E**: T028–T031 (individual nodes) can be developed simultaneously after T027.
> T032 (graph assembly) depends on all nodes. T033 (endpoint) depends on T032.

---

### T028 — Classifier Node
**Type:** Coding | **Complexity:** Medium | **Depends on:** T025, T027 | **Parallel with:** T029, T030, T031

Create `backend/app/agent/nodes.py` (first node):

`classify_query(state: AgentState) -> AgentState`:
- Takes `state.current_query`
- Sends a lightweight classification prompt to Ollama LLM:
  `"Is this message a greeting/trivial message, or a question about book content? Reply with only: TRIVIAL or DOCUMENT"`
- Sets `state.is_trivial = True/False`
- Returns updated state

**Output files:**
- `backend/app/agent/nodes.py` (classifier node)

---

### T029 — Retriever Node
**Type:** Coding | **Complexity:** Medium | **Depends on:** T019, T027 | **Parallel with:** T028, T030, T031

Add `retrieve_context(state: AgentState) -> AgentState` to `nodes.py`:
- Uses `state.rewritten_query or state.current_query`
- Calls `vector_store.search(query, top_k=settings.top_k_results)`
- Sets `state.retrieved_chunks`
- Returns updated state

**Output files:**
- `backend/app/agent/nodes.py` (retriever node added)

---

### T030 — Context Evaluator Node
**Type:** Coding | **Complexity:** Medium | **Depends on:** T025, T027 | **Parallel with:** T028, T029, T031

Add `evaluate_context(state: AgentState) -> AgentState` to `nodes.py`:
- If `state.retrieved_chunks` is empty or all scores < 0.4 threshold AND `state.retry_count < 2`:
  - Set a flag in state to trigger query rewrite
- Otherwise: proceed to generation
- Increment `state.retry_count`
- This node's output is used by a conditional edge in the graph

Add `rewrite_query(state: AgentState) -> AgentState` to `nodes.py`:
- Sends query rewrite prompt to LLM: `"Rephrase this question to improve document search: {query}"`
- Sets `state.rewritten_query`

**Output files:**
- `backend/app/agent/nodes.py` (evaluator + rewriter nodes added)

---

### T031 — Generator Node
**Type:** Coding | **Complexity:** High | **Depends on:** T025, T026, T027 | **Parallel with:** T028, T029, T030

Add `generate_response(state: AgentState) -> AgentState` to `nodes.py`:
- Builds context block from `state.retrieved_chunks` using `build_context_block()`
- Constructs messages list: system prompt + context + chat history + current query
- Calls `ollama_client.stream_chat()` — collects full response
- Parses the `\`\`\`sources` JSON block from the response to extract citations
- Sets `state.final_response` (text without the sources block) and `state.citations`

Also add `direct_reply(state: AgentState) -> AgentState`:
- For trivial queries: calls Ollama with a simple "you are a helpful assistant" prompt (no RAG)
- Sets `state.final_response`, `state.citations = []`

**Output files:**
- `backend/app/agent/nodes.py` (complete)

---

### T032 — LangGraph Graph Assembly
**Type:** Coding | **Complexity:** Medium | **Depends on:** T028, T029, T030, T031 | **Parallel with:** —

Create `backend/app/agent/graph.py`:
- Define `StateGraph(AgentState)`
- Add all nodes: `classifier`, `retriever`, `evaluator`, `rewriter`, `generator`, `direct_reply`
- Define edges:
  - `START → classifier`
  - `classifier → direct_reply` (if `is_trivial == True`)
  - `classifier → retriever` (if `is_trivial == False`)
  - `retriever → evaluator`
  - `evaluator → generator` (if context sufficient or retry_count >= 2)
  - `evaluator → rewriter` (if context insufficient and retry_count < 2)
  - `rewriter → retriever`
  - `generator → END`
  - `direct_reply → END`
- Compile graph: `graph = workflow.compile()`
- Export `compiled_graph` singleton

**Output files:**
- `backend/app/agent/graph.py`
- `backend/app/agent/__init__.py`

---

### T033 — Chat Streaming Endpoint (SSE)
**Type:** Coding | **Complexity:** High | **Depends on:** T032 | **Parallel with:** —

Create `backend/app/routers/chat.py`:
- `POST /api/chat/stream` — accepts `ChatRequest` (session_id, message)
- Maintains in-memory `dict[session_id → list[BaseMessage]]` (module-level, cleared on process restart)
- Loads session history, runs `compiled_graph.ainvoke(state)`
- Returns `StreamingResponse` with `media_type="text/event-stream"`
- SSE event sequence:
  1. `data: {"type": "status", "text": "Searching documents..."}` (before retriever runs)
  2. `data: {"type": "status", "text": "Analyzing excerpts..."}` (before generator runs)
  3. `data: {"type": "token", "text": "..."}` × N (one per token)
  4. `data: {"type": "citation", ...}` × M (one per citation found)
  5. `data: {"type": "done", "sources": [...]}` (final event)
- On error: `data: {"type": "error", "text": "..."}` + close stream
- After completion: append assistant message to session history in memory

> **Note**: True token-by-token streaming from LangGraph requires the generator node to yield tokens rather than collect them. The implementation should use LangGraph's streaming mode (`astream_events`) to forward tokens as they arrive from Ollama.

**Output files:**
- `backend/app/routers/chat.py`

---

## Phase 7 — Frontend Foundation

> **Goal**: Next.js app scaffolded, typed API client ready, session management working.
> This entire phase can run **in parallel with Phases 2–6** (frontend does not depend on backend code, only on the API contract defined in the spec).
> **Parallel group F**: T035–T037 can run simultaneously after T034.

---

### T034 — Next.js Project Initialization
**Type:** Setup | **Complexity:** Low | **Depends on:** T004 | **Parallel with:** Phase 2–6 tasks

Initialize Next.js project inside `frontend/` with:
- `npx create-next-app@latest . --typescript --tailwind --app --no-src-dir` (adjust flags to match target structure)
- Move source to `src/` subdirectory
- Install shadcn/ui: `npx shadcn@latest init` with neutral base color, CSS variables enabled
- Install additional shadcn components: `button`, `badge`, `popover`, `collapsible`, `scroll-area`, `tooltip`, `separator`, `skeleton`
- Install Framer Motion: `npm install framer-motion`
- Install React Hook Form + Zod: `npm install react-hook-form zod @hookform/resolvers`
- Update `next.config.ts` to add `NEXT_PUBLIC_API_URL` env variable support

**Output files:**
- `frontend/package.json`
- `frontend/src/app/layout.tsx` (root layout with font + global CSS)
- `frontend/tailwind.config.ts`
- `frontend/next.config.ts`
- `frontend/tsconfig.json`

---

### T035 — TypeScript Types
**Type:** Coding | **Complexity:** Low | **Depends on:** T034 | **Parallel with:** T036, T037

Create `frontend/src/types/document.ts`:
```typescript
export type DocumentStatus = 'pending' | 'extracting' | 'chunking' | 'embedding' | 'indexed' | 'error'
export interface Document { id: string; filename: string; file_format: string; upload_time: string; status: DocumentStatus; error_message: string | null; page_count: number | null; chunk_count: number | null }
```

Create `frontend/src/types/chat.ts`:
```typescript
export interface Citation { id: number; source_filename: string; page_number: number | null; section_heading: string | null; excerpt: string }
export interface ChatMessage { id: string; role: 'user' | 'assistant'; content: string; citations: Citation[]; timestamp: Date }
export type SSEEventType = 'status' | 'token' | 'citation' | 'done' | 'error'
export interface SSEEvent { type: SSEEventType; text?: string; citation?: Citation; sources?: Citation[] }
```

**Output files:**
- `frontend/src/types/document.ts`
- `frontend/src/types/chat.ts`

---

### T036 — API Client
**Type:** Coding | **Complexity:** Medium | **Depends on:** T034 | **Parallel with:** T035, T037

Create `frontend/src/lib/api.ts`:
- Base URL from `process.env.NEXT_PUBLIC_API_URL` (default: `http://localhost:8000`)
- `getDocuments(): Promise<Document[]>`
- `uploadDocuments(files: File[]): Promise<UploadResponse[]>` — multipart FormData
- `deleteDocument(id: string): Promise<void>`
- `clearAllDocuments(): Promise<void>`
- `getHealth(): Promise<HealthResponse>`
- `streamChat(sessionId: string, message: string, onEvent: (event: SSEEvent) => void, signal: AbortSignal): Promise<void>` — opens SSE connection via `fetch`, reads stream via `ReadableStream`, parses `data: {...}` lines, calls `onEvent` for each parsed event

**Output files:**
- `frontend/src/lib/api.ts`
- `frontend/src/lib/utils.ts` (`cn()` helper from shadcn/ui)

---

### T037 — Custom Hooks
**Type:** Coding | **Complexity:** Medium | **Depends on:** T035, T036 | **Parallel with:** —

Create `frontend/src/hooks/useSession.ts`:
- On mount, read `sessionId` from `sessionStorage`; if not present, generate UUID v4 and store it
- Returns `{ sessionId: string }`

Create `frontend/src/hooks/useDocuments.ts`:
- State: `documents: Document[]`, `isUploading: boolean`, `uploadProgress: Record<string, number>`
- `loadDocuments()`: calls `api.getDocuments()`, polls every 2s while any document has non-terminal status
- `uploadFiles(files: File[])`: calls `api.uploadDocuments()`, updates state
- `deleteDocument(id: string)`: calls `api.deleteDocument()`, removes from state
- `clearAll()`: calls `api.clearAllDocuments()`, resets state

Create `frontend/src/hooks/useChat.ts`:
- State: `messages: ChatMessage[]`, `isStreaming: boolean`, `agentStatus: string | null`
- `sendMessage(text: string)`: appends user message, calls `api.streamChat()`, builds assistant message incrementally as tokens arrive, appends citations as they are received
- `stopStreaming()`: calls `AbortController.abort()`
- `clearHistory()`: resets messages array

**Output files:**
- `frontend/src/hooks/useSession.ts`
- `frontend/src/hooks/useDocuments.ts`
- `frontend/src/hooks/useChat.ts`

---

## Phase 8 — Frontend Components

> **Goal**: all UI components built and individually functional (with mock data / Storybook-style isolation).
> **Parallel group G**: T038–T046 are all independent and can run simultaneously.

---

### T038 — ModelStatusIndicator
**Type:** Coding | **Complexity:** Low | **Depends on:** T034 | **Parallel with:** T039–T046

Polls `GET /api/health` every 5 seconds.
Shows: yellow pulsing dot + "Models Loading" | green dot + "Ready" | red dot + "Unavailable".
On "Unavailable": renders a dismissible banner with message "Ollama is not responding. Ensure Docker containers are running."

**Output files:**
- `frontend/src/components/ModelStatusIndicator.tsx`

---

### T039 — UploadZone
**Type:** Coding | **Complexity:** Medium | **Depends on:** T034 | **Parallel with:** T038, T040–T046

Drag-and-drop area using HTML5 drag events (no external library needed).
Accepts: `.pdf`, `.epub`, `.doc`, `.docx`, `.md`, `.txt`.
Shows file list before confirm. After confirm, calls `useDocuments.uploadFiles()`.
During upload: per-file progress bar with current step label (received from document status polling).
Validates file size client-side (rejects > `MAX_UPLOAD_SIZE_MB`).
Uses `React Hook Form` + `Zod` for the file input field.

**Output files:**
- `frontend/src/components/UploadZone.tsx`

---

### T040 — DocumentSidebar
**Type:** Coding | **Complexity:** Medium | **Depends on:** T034 | **Parallel with:** T038, T039, T041–T046

Left panel component. Receives `documents`, `onDelete`, `onClearAll` as props.
Renders each document with:
- Format icon (pdf/epub/docx/md/txt — simple emoji or svg)
- Filename (truncated to 24 chars with tooltip showing full name)
- Status badge: colored pill (indexed=green, processing=yellow+spinner, error=red)
- Delete button (trash icon, confirms via `AlertDialog` from Radix)
"Clear All" button at the bottom behind a confirmation dialog.
"+ Upload Books" button that opens the `UploadZone` in a `Dialog`.

**Output files:**
- `frontend/src/components/DocumentSidebar.tsx`

---

### T041 — CitationBadge & SourcePopover
**Type:** Coding | **Complexity:** Medium | **Depends on:** T034 | **Parallel with:** T038–T040, T042–T046

`CitationBadge`: small `[n]` badge rendered inline within message text. Uses Radix `Popover` trigger.
`SourcePopover`: popover content showing:
- Book title (filename, bold)
- Page number: `p. {n}` or Section: `{heading}` (or "No page info" if both null)
- Verbatim excerpt in a styled blockquote with subtle background

**Output files:**
- `frontend/src/components/CitationBadge.tsx`
- `frontend/src/components/SourcePopover.tsx`

---

### T042 — SourcesPanel
**Type:** Coding | **Complexity:** Low | **Depends on:** T034 | **Parallel with:** T038–T041, T043–T046

Collapsible section rendered at the bottom of assistant messages that have citations.
Header: "Sources Consulted (n)" with toggle chevron using Framer Motion for smooth open/close.
Content: numbered list of citations, each showing filename + page/section + excerpt snippet (max 120 chars).

**Output files:**
- `frontend/src/components/SourcesPanel.tsx`

---

### T043 — MessageBubble
**Type:** Coding | **Complexity:** Medium | **Depends on:** T034 | **Parallel with:** T038–T042, T044–T046

Renders a single chat message. Receives `ChatMessage` as prop.
- **User bubble**: right-aligned, accent background
- **Assistant bubble**: left-aligned, neutral background
- Content: renders Markdown via `react-markdown` (install as dependency)
- Inline citation badges (`[1]`, `[2]`) are parsed from the text and replaced with `CitationBadge` components
- Renders `SourcesPanel` below content if `citations.length > 0`
- During streaming (partial message): renders a blinking cursor at the end

**Output files:**
- `frontend/src/components/MessageBubble.tsx`

---

### T044 — AgentStatusBar
**Type:** Coding | **Complexity:** Low | **Depends on:** T034 | **Parallel with:** T038–T043, T045, T046

Animated bar shown between the last user message and the partial assistant response during generation.
Displays current `agentStatus` string: "Searching documents...", "Analyzing excerpts...", "Generating response..."
Uses Framer Motion for fade-in/out transitions between status strings.
Disappears once streaming is complete.

**Output files:**
- `frontend/src/components/AgentStatusBar.tsx`

---

### T045 — ChatInput
**Type:** Coding | **Complexity:** Low | **Depends on:** T034 | **Parallel with:** T038–T044, T046

Textarea (auto-resizes up to 6 rows) + Send button.
Send on `Enter` (new line on `Shift+Enter`).
Disabled when `isStreaming = true` or when no documents are indexed (shows tooltip: "Upload books to start chatting").
`StopButton` replaces Send button during streaming: red, "Stop" label, calls `useChat.stopStreaming()`.

**Output files:**
- `frontend/src/components/ChatInput.tsx`
- `frontend/src/components/StopButton.tsx`

---

### T046 — ChatThread
**Type:** Coding | **Complexity:** Low | **Depends on:** T034 | **Parallel with:** T038–T045

Scrollable container of `MessageBubble` components.
Auto-scrolls to bottom when new messages or tokens arrive (`useEffect` on messages).
When empty and no documents indexed: shows centered welcome message "Upload books to start chatting."
When empty but documents indexed: shows centered prompt "Ask anything about your books."
Renders `AgentStatusBar` after the last message when `isStreaming = true`.

**Output files:**
- `frontend/src/components/ChatThread.tsx`

---

## Phase 9 — Frontend Page Assembly

> **Goal**: all components wired together into a functional full page.
> T047 first (layout shell), then T048–T050 can be parallelized.

---

### T047 — Main Page Layout
**Type:** Coding | **Complexity:** Medium | **Depends on:** T037, T040, T046 | **Parallel with:** —

Create `frontend/src/app/page.tsx`:
- Two-column layout using CSS Grid or Flexbox:
  - Left column: fixed `280px` width, contains `DocumentSidebar`
  - Right column: flex-fill, contains `ChatThread` + `ChatInput` (chat panel)
- `ModelStatusIndicator` in the header bar (top right)
- Initialize hooks: `useSession()`, `useDocuments()`, `useChat()`
- Pass all required props down to child components

Create `frontend/src/app/layout.tsx`:
- Root layout with `<html lang="en">`
- Global font (Geist or Inter)
- Dark/light mode support (next-themes optional, but respect system preference via `prefers-color-scheme`)

**Output files:**
- `frontend/src/app/page.tsx`
- `frontend/src/app/layout.tsx`

---

### T048 — Chat Integration (SSE Wiring)
**Type:** Integration | **Complexity:** High | **Depends on:** T047, T033 | **Parallel with:** T049, T050

Wire `useChat` hook to the actual backend SSE endpoint:
- On `sendMessage`: open SSE connection via `fetch` to `POST /api/chat/stream`
- Parse each `data: {...}` line:
  - `status` → update `agentStatus` in state
  - `token` → append to the last assistant message's content
  - `citation` → append to the last assistant message's citations array
  - `done` → set `isStreaming = false`, clear `agentStatus`
  - `error` → show error toast (Radix Toast or shadcn Sonner)
- Pass `AbortController.signal` to fetch; `stopStreaming()` calls `controller.abort()`
- Test with real backend: send a question, verify tokens stream, verify citations appear

**Output files:**
- `frontend/src/hooks/useChat.ts` (final implementation)

---

### T049 — Document Library Integration
**Type:** Integration | **Complexity:** Medium | **Depends on:** T047, T021, T022, T023, T024 | **Parallel with:** T048, T050

Wire `useDocuments` hook to the real backend:
- On mount: call `loadDocuments()` and start polling (2s interval) while any document is in non-terminal status
- `UploadZone` → `uploadFiles()` → re-trigger polling
- Delete button → `deleteDocument()` → update list
- Clear All → `clearAll()` → reset list
- Test: upload a PDF, verify status transitions from `pending` → `extracting` → ... → `indexed`

**Output files:**
- `frontend/src/hooks/useDocuments.ts` (final implementation)

---

### T050 — Health & Model Status Integration
**Type:** Integration | **Complexity:** Low | **Depends on:** T047, T009 | **Parallel with:** T048, T049

Wire `ModelStatusIndicator` to the real `GET /api/health` endpoint.
Disable chat input while `ollama` status is not `"connected"`.
Show loading skeleton in `DocumentSidebar` while initial document list is fetching.

**Output files:**
- `frontend/src/components/ModelStatusIndicator.tsx` (final implementation)

---

## Phase 10 — Testing

> **Goal**: validate core logic and integration points. Tests run inside Docker containers.
> **Parallel group H**: T051–T053 are independent unit tests and can run simultaneously.
> T054–T055 are integration tests that require running containers.

---

### T051 — Backend Unit Tests: Extractors
**Type:** Testing | **Complexity:** Medium | **Depends on:** T010, T011, T012, T013, T014 | **Parallel with:** T052, T053

Create `tests/backend/unit/test_extractors.py`:
- Include small fixture files in `tests/fixtures/`: `sample.pdf` (2-page text PDF), `sample.epub`, `sample.docx`, `sample.md`, `sample.txt`
- Test per extractor:
  - Text is extracted (non-empty)
  - `page_number` is set correctly for PDF
  - `section_heading` is extracted for MD and DOCX
  - `ExtractionError` is raised for a fake scanned PDF (all-whitespace text)
  - `UnsupportedFormatError` raised for `.xyz` extension

**Output files:**
- `tests/backend/unit/test_extractors.py`
- `tests/fixtures/` (sample files)

---

### T052 — Backend Unit Tests: Chunker
**Type:** Testing | **Complexity:** Low | **Depends on:** T015 | **Parallel with:** T051, T053

Create `tests/backend/unit/test_chunker.py`:
- Given a mock `ExtractionResult` with 5000 chars of text and 3 pages:
  - Verify child chunks are ≤ `chunk_size` + `chunk_overlap`
  - Verify each child chunk has a non-null reference to its parent text
  - Verify `page_number` and `section_heading` are propagated correctly
  - Verify no text is lost (all source characters accounted for across parent chunks)

**Output files:**
- `tests/backend/unit/test_chunker.py`

---

### T053 — Backend Unit Tests: API Schemas
**Type:** Testing | **Complexity:** Low | **Depends on:** T008 | **Parallel with:** T051, T052

Create `tests/backend/unit/test_schemas.py`:
- Validate `DocumentResponse` serialization from a `Document` model instance
- Validate `ChatRequest` rejects missing `session_id`
- Validate `Citation` with `page_number = None` and `section_heading = None` is valid

**Output files:**
- `tests/backend/unit/test_schemas.py`

---

### T054 — Integration Test: Ingestion Pipeline
**Type:** Testing | **Complexity:** High | **Depends on:** T020, T021, T022, T051 | **Parallel with:** T055

Create `tests/backend/integration/test_ingestion_pipeline.py`:

Requires running Docker services (Qdrant + backend). Uses `httpx.AsyncClient`.

Test sequence:
1. `POST /api/documents/upload` with `sample.pdf` → assert `202` and `status = "pending"`
2. Poll `GET /api/documents/{id}` every 500ms for up to 30s → assert `status = "indexed"`
3. `GET /api/documents` → assert document appears in list with correct `chunk_count > 0`
4. Query Qdrant directly to verify vectors were inserted with correct payload fields
5. `DELETE /api/documents/{id}` → assert `204`
6. Verify Qdrant points for that `document_id` are gone

**Output files:**
- `tests/backend/integration/test_ingestion_pipeline.py`

---

### T055 — Integration Test: Chat Endpoint
**Type:** Testing | **Complexity:** High | **Depends on:** T033, T054 | **Parallel with:** —

Create `tests/backend/integration/test_chat_endpoint.py`:

Requires a running system with at least one indexed document (`sample.pdf` from T054).

Test sequence:
1. `POST /api/chat/stream` with a trivial message ("Hello") → assert stream contains `done` event, no `citation` events, response is a greeting
2. `POST /api/chat/stream` with a question whose answer is in `sample.pdf` → assert:
   - Stream contains `status` events
   - Stream contains `token` events
   - Stream contains at least one `citation` event with correct `source_filename`
   - Stream ends with `done` event containing `sources` list
3. `POST /api/chat/stream` with a question whose answer is NOT in the book → assert response contains "I could not find information"

**Output files:**
- `tests/backend/integration/test_chat_endpoint.py`

---

## Phase 11 — Final Polish & Documentation

> **Goal**: error handling, edge cases, and README.
> **Parallel group I**: T056–T058 can run simultaneously.

---

### T056 — Error Handling & Edge Cases
**Type:** Coding | **Complexity:** Medium | **Depends on:** T048, T049 | **Parallel with:** T057, T058

Backend:
- Return meaningful HTTP 422 with descriptive message for unsupported file format
- Return HTTP 413 for files exceeding `MAX_UPLOAD_SIZE_MB`
- Return HTTP 503 from `/api/chat/stream` if Ollama is unreachable, with `SSEEvent(type="error", text="LLM service unavailable. Check Docker containers.")`

Frontend:
- Toast notification on upload failure (unsupported format, file too large, server error)
- Toast notification on chat error
- Graceful degradation when backend is unreachable: show "Backend unavailable" banner instead of blank/broken UI
- Handle case where user tries to chat with 0 indexed documents (disable input + tooltip)

**Output files:**
- Minor changes across backend routers and frontend hooks/components

---

### T057 — Frontend Component Test: MessageBubble
**Type:** Testing | **Complexity:** Low | **Depends on:** T043 | **Parallel with:** T056, T058

Create `tests/frontend/components/MessageBubble.test.tsx` using `@testing-library/react`:
- Renders user message with correct alignment
- Renders assistant message with Markdown formatted correctly
- Renders citation badge `[1]` inline and opens popover on click showing the excerpt
- Renders `SourcesPanel` with correct source count
- Blinking cursor visible when `isStreaming = true`

**Output files:**
- `tests/frontend/components/MessageBubble.test.tsx`
- `frontend/jest.config.ts` + `frontend/jest.setup.ts`

---

### T058 — README & Operational Documentation
**Type:** Documentation | **Complexity:** Low | **Depends on:** T054, T055 | **Parallel with:** T056, T057

Create `README.md` at repository root covering:
1. **What it is**: one-paragraph description
2. **Requirements**: Docker Desktop 4.x+, NVIDIA Container Toolkit (optional, for GPU), 16GB RAM recommended
3. **First-time setup**: step-by-step (clone → copy .env → `docker-compose up -d` → wait for models → open browser)
4. **Session workflow**: start session, use it, reset with `docker-compose down -v`
5. **Supported file formats**: table with notes (scanned PDFs not supported)
6. **Troubleshooting**: Ollama model not loading, PDF not indexing, slow responses on CPU-only
7. **Configuration**: table of all `.env` variables with descriptions and defaults

**Output files:**
- `README.md`

---

## Dependency Graph Summary

```
Phase 0: T001 → T002,T003,T004 (parallel) → T005
                                                │
         ┌──────────────────────────────────────┤
         │                                      │
Phase 1: T006, T007, T008 (parallel) → T009    │
                                                │
Phase 2: T010,T011,T012,T013,T014 (parallel)   │
            └───────────────┬──────────────────┘
                            ▼
                    T015 (chunker)
                            │
Phase 3: T016, T017 (parallel) → T018 → T019
                                          │
Phase 4:        T020 ────────────────────┘
                 ├── T021, T022, T023, T024 (parallel)
                 │
Phase 5: T025, T026, T027 (parallel, starts with Phase 2)
                 │
Phase 6: T028, T029, T030, T031 (parallel) → T032 → T033
                                                        │
Phase 7: T034 → T035, T036 (parallel) → T037           │
Phase 8: T038–T046 (all parallel)                      │
Phase 9: T047 → T048, T049, T050 (parallel) ───────────┘
                 │
Phase 10: T051, T052, T053 (parallel) → T054 → T055
                 │
Phase 11: T056, T057, T058 (parallel)
```

---

## Task Index

| ID | Name | Phase | Type | Complexity | Parallel With |
|----|------|-------|------|------------|---------------|
| T001 | Repository Structure | 0 | Setup | Low | — |
| T002 | Docker Compose | 0 | Setup | Medium | T003, T004 |
| T003 | Backend Dockerfile | 0 | Setup | Low | T004 |
| T004 | Frontend Dockerfile | 0 | Setup | Low | T003 |
| T005 | Environment Config | 0 | Setup | Low | — |
| T006 | FastAPI App Skeleton | 1 | Coding | Low | T007, T008 |
| T007 | Database Schema | 1 | Coding | Low | T006, T008 |
| T008 | Pydantic Schemas | 1 | Coding | Low | T006, T007 |
| T009 | Health Endpoint | 1 | Coding | Low | — |
| T010 | PDF Extractor | 2 | Coding | Medium | T011–T014 |
| T011 | EPUB Extractor | 2 | Coding | Medium | T010,T012–T014 |
| T012 | DOCX/DOC Extractor | 2 | Coding | Medium | T010,T011,T013,T014 |
| T013 | Markdown/TXT Extractor | 2 | Coding | Low | T010–T012, T014 |
| T014 | Extractor Factory | 2 | Coding | Low | T010–T013 |
| T015 | Chunking Service | 2 | Coding | Medium | T016, T017 |
| T016 | Qdrant Client & Collection | 3 | Coding | Medium | T015, T017 |
| T017 | Embedding Service | 3 | Coding | Low | T015, T016 |
| T018 | Qdrant Indexing | 3 | Coding | Medium | — |
| T019 | Hybrid Search | 3 | Coding | High | T020 |
| T020 | Async Ingestion Pipeline | 4 | Coding | High | T025, T026 |
| T021 | Upload Endpoint | 4 | Coding | Medium | T022–T024 |
| T022 | List & Status Endpoints | 4 | Coding | Low | T021,T023,T024 |
| T023 | Delete Endpoint | 4 | Coding | Low | T021,T022,T024 |
| T024 | Clear All Endpoint | 4 | Coding | Low | T021–T023 |
| T025 | Ollama Client | 5 | Coding | Low | T020, T027 |
| T026 | System Prompt | 5 | Coding | Medium | T025, T027 |
| T027 | Agent State | 5 | Coding | Low | T025, T026 |
| T028 | Classifier Node | 6 | Coding | Medium | T029–T031 |
| T029 | Retriever Node | 6 | Coding | Medium | T028,T030,T031 |
| T030 | Evaluator Node | 6 | Coding | Medium | T028,T029,T031 |
| T031 | Generator Node | 6 | Coding | High | T028–T030 |
| T032 | Graph Assembly | 6 | Coding | Medium | — |
| T033 | Chat SSE Endpoint | 6 | Integration | High | — |
| T034 | Next.js Init | 7 | Setup | Low | Phases 2–6 |
| T035 | TypeScript Types | 7 | Coding | Low | T036, T037 |
| T036 | API Client | 7 | Coding | Medium | T035, T037 |
| T037 | Custom Hooks | 7 | Coding | Medium | — |
| T038 | ModelStatusIndicator | 8 | Coding | Low | T039–T046 |
| T039 | UploadZone | 8 | Coding | Medium | T038,T040–T046 |
| T040 | DocumentSidebar | 8 | Coding | Medium | T038,T039,T041–T046 |
| T041 | CitationBadge+Popover | 8 | Coding | Medium | T038–T040,T042–T046 |
| T042 | SourcesPanel | 8 | Coding | Low | T038–T041,T043–T046 |
| T043 | MessageBubble | 8 | Coding | Medium | T038–T042,T044–T046 |
| T044 | AgentStatusBar | 8 | Coding | Low | T038–T043,T045,T046 |
| T045 | ChatInput+StopButton | 8 | Coding | Low | T038–T044, T046 |
| T046 | ChatThread | 8 | Coding | Low | T038–T045 |
| T047 | Main Page Layout | 9 | Coding | Medium | — |
| T048 | Chat SSE Integration | 9 | Integration | High | T049, T050 |
| T049 | Document Library Integration | 9 | Integration | Medium | T048, T050 |
| T050 | Health Status Integration | 9 | Integration | Low | T048, T049 |
| T051 | Unit Tests: Extractors | 10 | Testing | Medium | T052, T053 |
| T052 | Unit Tests: Chunker | 10 | Testing | Low | T051, T053 |
| T053 | Unit Tests: Schemas | 10 | Testing | Low | T051, T052 |
| T054 | Integration: Ingestion | 10 | Testing | High | T055 |
| T055 | Integration: Chat | 10 | Testing | High | — |
| T056 | Error Handling | 11 | Coding | Medium | T057, T058 |
| T057 | Frontend Component Tests | 11 | Testing | Low | T056, T058 |
| T058 | README | 11 | Documentation | Low | T056, T057 |
