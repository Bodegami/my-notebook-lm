## 0. Phase 0 — Project Scaffolding

- [x] 0.1 (T001) Create top-level directory tree with `.gitkeep` placeholders and `.gitignore` (excludes `.env`, `__pycache__`, `node_modules`, `.next`, `uploads/`)
- [x] 0.2 (T002) Create `docker-compose.yml` with 4 services (`frontend`, `backend`, `qdrant`, `ollama`), internal `rag_network`, 4 named volumes, GPU config block, and Ollama model-pull entrypoint script
- [x] 0.3 (T003) Create `backend/Dockerfile` from `python:3.11-slim` with system deps (`build-essential`, `libpoppler-cpp-dev`, `antiword`) and `requirements.txt` with all pinned backend dependencies
- [x] 0.4 (T004) Create `frontend/Dockerfile` (multi-stage: deps → builder → runner) and `frontend/.dockerignore`
- [x] 0.5 (T005) Create `.env.example` and `.env` with all variables from spec (with comments); create `backend/app/config.py` using `pydantic-settings`
- [x] 0.6 Commit Phase 0: "feat: scaffold project structure, Docker infrastructure, and configuration"

## 1. Phase 1 — Backend Foundation

- [x] 1.1 (T006) Create `backend/app/main.py`: FastAPI app with lifespan (DB init, Qdrant verify, Ollama verify), CORS for `localhost:3000`, router registration, global exception handler
- [x] 1.2 (T007) Create `backend/app/models/document.py` (SQLModel `Document` table) and `backend/app/database.py` (engine, `create_db_and_tables()`, `get_session()`)
- [x] 1.3 (T008) Create `backend/app/schemas/document.py` (`DocumentResponse`, `DocumentListResponse`, `UploadResponse`) and `backend/app/schemas/chat.py` (`ChatRequest`, `Citation`, `SSEEvent`)
- [x] 1.4 (T009) Create `backend/app/routers/health.py`: async `GET /api/health` using `httpx.AsyncClient` checking Qdrant and Ollama; return structured health status
- [x] 1.5 Write unit tests for API schemas (`tests/backend/unit/test_schemas.py`): validate `DocumentResponse`, `ChatRequest`, `Citation` with null fields
- [x] 1.6 Commit Phase 1: "feat: FastAPI app skeleton, SQLModel schema, Pydantic schemas, and health endpoint"

## 2. Phase 2 — Document Extractors (TDD)

- [x] 2.1 (T010) Write failing tests for PDF extractor → implement `backend/app/services/extractors/base.py` (abstract interfaces) and `extractors/pdf.py` (`pypdf`, page-number metadata, scanned-PDF detection)
- [x] 2.2 (T011) Write failing tests for EPUB extractor → implement `extractors/epub.py` (`ebooklib` + `beautifulsoup4`, section headings from `<h1>`/`<h2>`)
- [x] 2.3 (T012) Write failing tests for DOCX extractor → implement `extractors/docx.py` (`python-docx`, heading tracking, `antiword` fallback for `.doc`)
- [x] 2.4 (T013) Write failing tests for Markdown/TXT extractor → implement `extractors/markdown.py` (heading-boundary splitting for `.md`, fixed-size blocks for `.txt`)
- [x] 2.5 (T014) Implement `extractors/factory.py` (`ExtractorFactory` mapping extensions to extractors, `UnsupportedFormatError`) and `extractors/__init__.py`
- [x] 2.6 Add fixture files to `tests/fixtures/`: `sample.pdf`, `sample.epub`, `sample.docx`, `sample.md`, `sample.txt`
- [x] 2.7 Ensure all extractor unit tests pass (`tests/backend/unit/test_extractors.py`)
- [x] 2.8 Commit Phase 2: "feat: document extractors (PDF, EPUB, DOCX, MD, TXT) with TDD"

## 3. Phase 3 — Chunking Service (TDD)

- [ ] 3.1 (T015) Write failing tests for chunker → implement `backend/app/services/chunker.py` with parent-document strategy (child ~300 tokens + 50 overlap, parent ~1000 tokens, `ChunkRecord` dataclass)
- [ ] 3.2 Ensure chunker unit tests pass (`tests/backend/unit/test_chunker.py`): verify chunk size bounds, parent-child linkage, metadata propagation, no text loss
- [ ] 3.3 Commit Phase 3: "feat: parent-document chunking service with TDD"

## 4. Phase 4 — Vector Store & Embeddings (TDD)

- [ ] 4.1 (T016) Implement `backend/app/services/vector_store.py` (Part 1): `QdrantClient` init, `initialize_collection()` (768-dim, Cosine, sparse vectors), `delete_points_by_document_id()`, `clear_collection()`
- [ ] 4.2 (T017) Implement `backend/app/services/embedder.py`: singleton `EmbeddingService` with `fastembed.TextEmbedding("nomic-embed-text")`, `embed_texts()` batch, `embed_query()` single
- [ ] 4.3 (T018) Add `index_chunks()` to `vector_store.py`: batch embed child texts, build `PointStruct` with dense vectors + full payload (parent_text, metadata), upload in batches of 100, return Qdrant UUIDs
- [ ] 4.4 (T019) Add `search()` to `vector_store.py`: dense cosine search + sparse BM25 search, RRF fusion, return top-K `SearchResult` objects
- [ ] 4.5 Commit Phase 4: "feat: Qdrant vector store with hybrid search (dense+BM25+RRF) and FastEmbed embeddings"

## 5. Phase 5 — Ingestion Pipeline & Document API

- [ ] 5.1 (T020) Implement `backend/app/services/ingestion.py`: async `ingest_document()` pipeline (extract → chunk → embed → index) with SQLite status updates at each step; runs as FastAPI `BackgroundTask`
- [ ] 5.2 (T021) Implement `POST /api/documents/upload` in `routers/documents.py`: multipart upload, extension + size validation, save to `UPLOAD_DIR`, create SQLite record, schedule background task
- [ ] 5.3 (T022) Add `GET /api/documents` and `GET /api/documents/{id}` routes to `routers/documents.py`
- [ ] 5.4 (T023) Add `DELETE /api/documents/{id}` route: delete Qdrant vectors + disk file + SQLite record
- [ ] 5.5 (T024) Add `DELETE /api/documents` route (Clear All): `clear_collection()` + delete all files + delete all SQLite records
- [ ] 5.6 Commit Phase 5: "feat: async ingestion pipeline and full document CRUD API"

## 6. Phase 6 — LLM Integration

- [ ] 6.1 (T025) Implement `backend/app/services/ollama_client.py`: async `httpx` client, `check_health()`, `is_model_available()`, `stream_chat()` (NDJSON streaming)
- [ ] 6.2 (T026) Create `backend/app/agent/prompts.py`: `SYSTEM_PROMPT` with mandatory citation rules + JSON sources block; `build_context_block()` function
- [ ] 6.3 (T027) Create `backend/app/agent/state.py`: `AgentState` TypedDict with `session_id`, `messages`, `current_query`, `rewritten_query`, `retrieved_chunks`, `retry_count`, `is_trivial`, `final_response`, `citations`
- [ ] 6.4 Commit Phase 6: "feat: Ollama client, system prompt with citation rules, and agent state"

## 7. Phase 7 — LangGraph Agent (TDD)

- [ ] 7.1 (T028) Write failing test for classifier → implement `classify_query()` node in `backend/app/agent/nodes.py`: LLM classification (TRIVIAL/DOCUMENT), sets `is_trivial`
- [ ] 7.2 (T029) Write failing test for retriever → implement `retrieve_context()` node: calls `vector_store.search()`, sets `retrieved_chunks`
- [ ] 7.3 (T030) Write failing test for evaluator/rewriter → implement `evaluate_context()` and `rewrite_query()` nodes: score threshold check, retry counter, query rewrite via LLM
- [ ] 7.4 (T031) Write failing test for generator → implement `generate_response()` and `direct_reply()` nodes: builds prompt with context, calls `ollama_client.stream_chat()`, parses `sources` JSON block
- [ ] 7.5 (T032) Assemble `backend/app/agent/graph.py`: `StateGraph` with all nodes and conditional edges (classifier → direct_reply|retriever → evaluator → generator|rewriter loop); compile and export singleton
- [ ] 7.6 (T033) Create `backend/app/routers/chat.py`: `POST /api/chat/stream` SSE endpoint using `StreamingResponse`; in-memory session dict; `astream_events` for token-by-token streaming; status events sequence
- [ ] 7.7 Commit Phase 7: "feat: LangGraph ReAct agent with classifier, retriever, evaluator, rewriter, generator nodes and SSE chat endpoint"

## 8. Phase 8 — Frontend Foundation

- [ ] 8.1 (T034) Initialize Next.js 14 project in `frontend/` (TypeScript, Tailwind, App Router, `src/` dir); install shadcn/ui components (`button`, `badge`, `popover`, `collapsible`, `scroll-area`, `tooltip`, `separator`, `skeleton`); install Framer Motion, React Hook Form + Zod
- [ ] 8.2 (T035) Create `frontend/src/types/document.ts` (`Document`, `DocumentStatus`) and `frontend/src/types/chat.ts` (`Citation`, `ChatMessage`, `SSEEvent`, `SSEEventType`)
- [ ] 8.3 (T036) Create `frontend/src/lib/api.ts`: typed fetch wrappers for all backend endpoints including `streamChat()` with SSE parsing and `AbortSignal` support
- [ ] 8.4 (T037) Create hooks: `useSession.ts` (UUID from `sessionStorage`), `useDocuments.ts` (load + poll + upload + delete + clearAll), `useChat.ts` (SSE streaming, `AbortController`, status state)
- [ ] 8.5 Commit Phase 8: "feat: Next.js frontend foundation — types, API client, and custom hooks"

## 9. Phase 9 — Frontend Components

- [ ] 9.1 (T038) Implement `ModelStatusIndicator.tsx`: polls `GET /api/health` every 5s, yellow/green/red badge, error banner when Ollama unreachable
- [ ] 9.2 (T039) Implement `UploadZone.tsx`: HTML5 drag-and-drop, file list preview, React Hook Form + Zod validation, per-file progress bar with step labels
- [ ] 9.3 (T040) Implement `DocumentSidebar.tsx`: document list with format icons, status badges (spinner for processing), delete button with `AlertDialog`, "Clear All" confirmation, "+ Upload Books" button
- [ ] 9.4 (T041) Implement `CitationBadge.tsx` (inline `[n]` badge with Radix Popover trigger) and `SourcePopover.tsx` (filename, page/section, verbatim excerpt blockquote)
- [ ] 9.5 (T042) Implement `SourcesPanel.tsx`: collapsible "Sources Consulted (n)" with Framer Motion chevron animation, numbered citation list with 120-char excerpt snippets
- [ ] 9.6 (T043) Implement `MessageBubble.tsx`: user/assistant bubbles, Markdown via `react-markdown`, inline `[n]` → `CitationBadge` parsing, `SourcesPanel` below agent messages, blinking cursor during streaming
- [ ] 9.7 (T044) Implement `AgentStatusBar.tsx`: Framer Motion fade between status strings ("Searching documents...", "Analyzing excerpts...", "Generating response..."), hidden when streaming complete
- [ ] 9.8 (T045) Implement `ChatInput.tsx` (auto-resize textarea, Enter to send, Shift+Enter for newline, disabled states with tooltip) and `StopButton.tsx` (red, replaces Send during streaming)
- [ ] 9.9 (T046) Implement `ChatThread.tsx`: scrollable `MessageBubble` list, auto-scroll to bottom, empty states ("Upload books..." / "Ask anything..."), `AgentStatusBar` during streaming
- [ ] 9.10 Commit Phase 9: "feat: all UI components — sidebar, upload zone, chat thread, citation badges, source panel"

## 10. Phase 10 — Frontend Page Assembly & Integration

- [ ] 10.1 (T047) Create `frontend/src/app/page.tsx`: two-column layout (280px sidebar + flex chat panel), wire `useSession()`, `useDocuments()`, `useChat()` hooks, `ModelStatusIndicator` in header
- [ ] 10.2 (T047) Create/update `frontend/src/app/layout.tsx`: root layout with `<html lang="en">`, global font (Geist or Inter), system `prefers-color-scheme` support
- [ ] 10.3 (T048) Wire `useChat` to real SSE backend: parse `status`/`token`/`citation`/`done`/`error` events, `AbortController` stop, error toast on failure
- [ ] 10.4 (T049) Wire `useDocuments` to real backend: mount load + 2s polling while non-terminal, upload → re-trigger poll, delete and clear all wired
- [ ] 10.5 (T050) Wire `ModelStatusIndicator` to real health endpoint; disable chat input when Ollama not ready; loading skeleton in sidebar during initial fetch
- [ ] 10.6 Commit Phase 10: "feat: main page layout and full frontend-backend integration (SSE chat, document management, health status)"

## 11. Phase 11 — Integration Testing

- [ ] 11.1 (T054) Create `tests/backend/integration/test_ingestion_pipeline.py`: upload `sample.pdf` → poll until `indexed` → verify `chunk_count` → check Qdrant vectors → delete → verify vectors gone
- [ ] 11.2 (T055) Create `tests/backend/integration/test_chat_endpoint.py`: trivial message (no citations) → document question (status+token+citation+done events) → out-of-scope question ("could not find information")
- [ ] 11.3 Run integration tests against running Docker stack; all tests must pass
- [ ] 11.4 Commit Phase 11: "test: integration tests for ingestion pipeline and SSE chat endpoint"

## 12. Phase 12 — Error Handling, Polish & Documentation

- [ ] 12.1 (T056) Backend: HTTP 422 for unsupported format, HTTP 413 for oversized files, HTTP 503 SSE error event when Ollama unreachable
- [ ] 12.2 (T056) Frontend: toast on upload failure (format, size, server error), toast on chat error, "Backend unavailable" banner, chat disabled with tooltip when 0 documents indexed
- [ ] 12.3 (T057) Create `tests/frontend/components/MessageBubble.test.tsx` with `@testing-library/react`: user bubble alignment, Markdown rendering, citation badge click → popover, `SourcesPanel` count, streaming cursor
- [ ] 12.4 (T058) Create `README.md`: what it is, requirements, first-time setup, session workflow, supported formats table, troubleshooting, `.env` variable reference
- [ ] 12.5 Commit Phase 12: "feat: error handling, edge cases, frontend component tests, and README documentation"
