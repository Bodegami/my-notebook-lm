## Context

This is a greenfield project implementing a local-first document intelligence system (RAG library) that runs entirely inside Docker. Users upload digital books in various formats; the system extracts, chunks, embeds, and indexes the content; then exposes a streaming chat interface backed by a local LLM. The system targets hardware with limited GPU vRAM (2 GB) and must function on CPU alone.

There is no existing codebase to migrate — the design decisions below establish the architectural baseline for the MVP.

**Key constraints:**
- No cloud APIs; no data leaves the local machine
- GPU vRAM ≤ 2 GB; LLM must fall back to CPU automatically
- Single-user, single-session model — no authentication, no concurrent user support
- Ephemeral knowledge base by design (reset via `docker-compose down -v`)

## Goals / Non-Goals

**Goals:**
- Containerized 4-service stack runnable with a single `docker-compose up -d`
- End-to-end RAG pipeline: upload → extract → chunk → embed → index → chat with citations
- Hybrid search (dense + sparse) for better retrieval than pure semantic search
- Streaming token-by-token responses via SSE with mandatory source attribution
- In-memory session history per browser tab; no disk persistence of chat

**Non-Goals:**
- User authentication or multi-user support
- Cloud deployment or remote access
- OCR for scanned PDFs
- Chat history persistence across browser sessions
- Book collections, categories, or tagging
- Web search or external tool use by the agent

## Decisions

### D1 — LangGraph for Agent Orchestration (over plain LangChain LCEL or raw Python)

**Decision**: Use LangGraph `StateGraph` to model the agent as an explicit state machine with typed nodes and conditional edges.

**Rationale**: The agent has branching logic (trivial vs. document query, retry on poor retrieval) that maps naturally to a graph. LangGraph makes retry loops and conditional routing explicit and testable. LCEL would produce a linear chain that is harder to branch; raw Python would require manual state management.

**Alternative considered**: Pure LangChain LCEL pipeline — rejected because conditional retry requires awkward imperative code outside the chain.

---

### D2 — FastEmbed for Embeddings (over Ollama embeddings endpoint)

**Decision**: Use `fastembed` (CPU-optimized, no PyTorch) for generating embeddings at ingest time.

**Rationale**: FastEmbed loads `nomic-embed-text` directly in the Python process without requiring a round-trip to the Ollama container. It is CPU-efficient and avoids additional HTTP latency during bulk ingestion. Ollama is used exclusively for LLM chat inference.

**Alternative considered**: Calling `POST /api/embeddings` on Ollama — rejected because it adds network overhead and ties embedding throughput to Ollama's request queue.

---

### D3 — Parent Document Chunking Strategy

**Decision**: Use a two-tier chunk structure: small child chunks (~300 tokens) for embedding/search, large parent chunks (~1000 tokens) as LLM context.

**Rationale**: Embedding shorter text improves retrieval precision; providing longer context windows to the LLM improves answer coherence. Qdrant stores parent text in the point payload alongside the child embedding, avoiding a second database lookup.

**Alternative considered**: Single-size chunks — rejected because embedding quality degrades on long texts and LLM context quality degrades on very short excerpts.

---

### D4 — Hybrid Search with RRF Fusion (over pure dense search)

**Decision**: Combine Qdrant dense vector search with BM25 sparse search; merge results using Reciprocal Rank Fusion (RRF).

**Rationale**: Pure semantic search misses exact-term matches (book titles, author names, technical jargon). BM25 handles these well. RRF is parameter-free and robust for fusing ranked lists.

**Alternative considered**: Dense search only — rejected because users frequently search for specific technical terms that pure semantic search ranks poorly.

---

### D5 — SSE over WebSockets for Streaming

**Decision**: Use Server-Sent Events (SSE) via FastAPI's `StreamingResponse` for token streaming.

**Rationale**: SSE is unidirectional (server → client), which is all that's needed for token streaming. SSE is simpler than WebSockets (no handshake, native browser EventSource support, works with standard fetch + ReadableStream). FastAPI supports it without additional libraries.

**Alternative considered**: WebSockets — rejected as over-engineered for a unidirectional stream.

---

### D6 — SQLite via SQLModel for Document Metadata

**Decision**: Use SQLite (via SQLModel) for document metadata persistence. Qdrant stores vector payloads; SQLite stores document-level records.

**Rationale**: SQLite requires no separate container and is zero-config. Document metadata (status, filenames, chunk counts) is low-volume and relational. SQLModel provides Pydantic-compatible models that double as FastAPI schemas.

**Alternative considered**: PostgreSQL — rejected as unnecessary overhead for a single-user local system.

---

### D7 — In-Memory Chat Session Storage

**Decision**: Chat history is stored in a Python `dict[session_id → list[BaseMessage]]` in memory; never written to disk.

**Rationale**: The spec explicitly requires ephemeral sessions. Storing to disk would complicate the "start fresh" workflow and add GDPR-like privacy concerns. The session UUID is generated client-side and passed via `X-Session-ID` header; the backend dictionary is cleared on process restart.

---

### D8 — TDD Cycle for All Implementation Tasks

**Decision**: Every feature task follows the Red → Green → Refactor TDD cycle. Unit tests are written before implementation; integration tests validate end-to-end behavior with real containers.

**Rationale**: The plan document (`PLAN.md`) includes explicit test tasks (T051–T057) and integration tests (T054–T055) that validate the pipeline with running Docker services. TDD ensures testability is built in, not bolted on.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| LLM first-token latency > 30s on CPU-only hardware | Use quantized `phi3.5:mini-instruct` (Q4, ~2.5 GB RAM); show "Models Loading" indicator; allow user to interrupt with Stop button |
| `nomic-embed-text` download fails on first startup | Ollama entrypoint retries; health endpoint reports model availability; UI blocks chat until models are ready |
| Scanned PDFs produce empty text | Detect low character density per page; report `error` status with clear message; OCR explicitly out of scope for v1 |
| BM25 sparse vectors require Qdrant ≥ 1.9 sparse vector support | Pin `qdrant/qdrant:latest` and `qdrant-client≥1.9`; test collection creation at startup |
| Legacy `.doc` files require `antiword` binary in backend container | Include `antiword` in `backend/Dockerfile`; raise clear `ExtractionError` if not found |
| Context window overflow for books with very dense content | Parent chunk cap at 1000 tokens; top-K=6 limits context to ~6000 tokens, within phi3.5 limits |

## Migration Plan

This is a greenfield deployment:
1. Developer runs `cp .env.example .env`
2. `docker-compose up -d` — downloads models on first run (~2–4 GB, requires internet)
3. Open `http://localhost:3000`
4. To reset: `docker-compose down -v && docker-compose up -d`

No rollback needed for v1 — all data is local and user-controlled.

## Open Questions

- **BM25 implementation approach**: Qdrant supports sparse vectors natively (≥1.7). Should we use Qdrant's built-in sparse vector indexing with a separate BM25 vectorizer, or use `rank_bm25` in Python against stored child texts? → Prefer Qdrant-native sparse vectors if the `qdrant-client` version supports it, otherwise fall back to `rank_bm25` in Python.
- **Framer Motion vs. CSS animations**: Framer Motion adds ~35 KB to the bundle. For simple fade/slide transitions, CSS transitions may suffice. Decision deferred to T044 implementation.
