## Why

Knowledge workers and students need a private, offline way to interact with their personal book collections without sending documents to cloud services. This MVP delivers a local-first document intelligence system — a "personal NotebookLM" — that runs entirely via Docker, enabling users to upload digital books and have grounded, citation-backed conversations with their library.

## What Changes

- **New system**: fully containerized local RAG application (no prior version exists in this repo)
- New Docker Compose stack: `frontend` (Next.js), `backend` (FastAPI + LangGraph), `qdrant` (vector DB), `ollama` (local LLM + embeddings)
- New document ingestion pipeline supporting PDF, EPUB, DOCX, DOC, Markdown, and plain text
- New hybrid search retrieval (dense + sparse BM25 via Qdrant) with parent-document chunking strategy
- New LangGraph agent with classifier, retriever, evaluator, rewriter, and generator nodes
- New streaming chat interface with inline citation badges and source popovers
- New knowledge base management UI (upload, list, delete, clear all)
- All data remains local; no cloud API dependencies after initial model download

## Capabilities

### New Capabilities

- `document-ingestion`: Upload and process digital books (PDF, EPUB, DOCX, MD, TXT) into a vector knowledge base; async pipeline with status tracking from `pending` → `indexed`
- `rag-chat`: Multi-turn conversational chat against indexed documents with mandatory inline citations (book + page/section); responses streamed token-by-token via SSE
- `hybrid-search`: Combined dense (semantic) + sparse (BM25 keyword) retrieval over Qdrant, fused with Reciprocal Rank Fusion (RRF) for best top-K results
- `knowledge-base-management`: List, delete individual, and clear-all documents from the knowledge base; visual status badges and error reporting
- `local-llm-inference`: Ollama-backed LLM (phi3.5:mini-instruct) and embedding (nomic-embed-text) services running fully offline after first pull
- `session-management`: In-memory chat history scoped to browser session (UUID); no persistence to disk; ephemeral by design

### Modified Capabilities

<!-- No existing capabilities — this is a greenfield project -->

## Impact

- **New repo structure**: `backend/`, `frontend/`, `tests/`, `docker-compose.yml`, `.env.example`
- **Backend dependencies**: FastAPI, LangChain, LangGraph, Qdrant Client, FastEmbed, SQLModel, pypdf, ebooklib, python-docx
- **Frontend dependencies**: Next.js 14 (App Router), TypeScript, shadcn/ui, Tailwind CSS, Framer Motion, React Hook Form + Zod
- **Infrastructure**: Docker Compose with 4 services and 4 named volumes; requires Docker Desktop and optionally NVIDIA Container Toolkit for GPU offload
- **Hardware target**: 16 GB RAM, optional NVIDIA GPU with 2 GB vRAM; LLM runs on CPU when GPU is insufficient
