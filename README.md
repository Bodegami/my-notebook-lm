# Local Book Library

A fully local, privacy-first document intelligence system. Upload your digital books and chat with an AI that answers based solely on their content — with exact source citations — all running on your own hardware via Docker.

No data ever leaves your machine. No cloud APIs. No subscriptions.

---

## What It Is

A "personal NotebookLM" that runs entirely inside Docker:

| Component | Technology | Role |
|-----------|-----------|------|
| Frontend | Next.js 14 | Chat UI + document manager |
| Backend | FastAPI + LangGraph | RAG agent + document API |
| Vector DB | Qdrant | Stores text embeddings |
| LLM + Embeddings | Ollama (local) | AI inference |

---

## Requirements

| Requirement | Details |
|------------|---------|
| **Docker Desktop** | 4.x or later (with Compose V2) |
| **RAM** | 16 GB recommended (LLM runs on CPU) |
| **Storage** | ~5 GB for models + your books |
| **GPU** (optional) | NVIDIA with NVIDIA Container Toolkit for partial GPU offload |

---

## First-Time Setup

```bash
# 1. Clone the repository
git clone <repo-url> && cd <repo-dir>

# 2. Copy environment template
cp .env.example .env

# 3. Start all services (downloads AI models on first run — needs internet)
docker-compose up -d

# 4. Watch model download progress (~2–4 GB total)
docker-compose logs -f ollama

# 5. Once models are ready, open the app
open http://localhost:3000   # macOS
# Or visit http://localhost:3000 in your browser
```

The header indicator will turn green ("Models Ready") when the system is ready for use.

---

## Session Workflow

### Start a study session
```bash
docker-compose up -d
# Open http://localhost:3000 → upload books → start chatting
```

### Stop without losing data (books stay indexed)
```bash
docker-compose stop
# Resume later with: docker-compose start
```

### Reset for a fresh session (clears all books and vectors)
```bash
docker-compose down -v   # removes all volumes
docker-compose up -d     # starts fresh
```

---

## Supported File Formats

| Format | Extension | Page/Section Info | Notes |
|--------|-----------|-------------------|-------|
| PDF | `.pdf` | Page numbers | Text-layer PDFs only; scanned PDFs not supported |
| EPUB | `.epub` | Chapter/section headings | HTML content extracted |
| Word | `.docx`, `.doc` | Section headings | `.doc` requires antiword (included in container) |
| Markdown | `.md` | Heading hierarchy | Splits at `#`, `##`, `###` boundaries |
| Plain text | `.txt` | None | Split into 2000-character blocks |

> **Scanned PDFs**: If a PDF was created by scanning physical pages with no text layer, it will fail to index with an "appears to be scanned" error. OCR is not supported in v1.

---

## Troubleshooting

### Ollama models not loading (yellow indicator)
- Check container logs: `docker-compose logs -f ollama`
- First startup downloads ~2–4 GB; wait for download to complete
- If download stalled: `docker-compose restart ollama`

### PDF not indexing (error badge)
- Verify the PDF has a text layer (open it and try selecting text)
- Scanned PDFs without OCR cannot be indexed
- Try converting to DOCX or TXT as a workaround

### Slow responses (CPU-only mode)
- With ≤ 2 GB GPU vRAM, the LLM runs on CPU — expect 10–30s for first token
- Alternative faster model: set `LLM_MODEL=llama3.2:1b-instruct-q4_0` in `.env` (lower quality, much faster)
- Ensure no other memory-intensive applications are running

### Backend unavailable banner
- Run `docker-compose ps` to verify all containers are running
- Check logs: `docker-compose logs backend`

---

## Configuration

All settings live in `.env` (copied from `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://ollama:11434` | Ollama service URL (internal) |
| `LLM_MODEL` | `phi3.5:mini-instruct` | Chat LLM model name |
| `EMBED_MODEL` | `nomic-embed-text` | Embedding model name |
| `OLLAMA_NUM_GPU` | `1` | GPU layers to offload (0 = CPU only) |
| `QDRANT_HOST` | `http://qdrant:6333` | Qdrant service URL (internal) |
| `QDRANT_COLLECTION` | `books` | Qdrant collection name |
| `UPLOAD_DIR` | `/app/uploads` | Path for uploaded files |
| `DB_PATH` | `/app/data/db.sqlite` | SQLite database path |
| `MAX_UPLOAD_SIZE_MB` | `200` | Maximum file size per upload |
| `CHUNK_SIZE` | `300` | Child chunk size in tokens |
| `CHUNK_OVERLAP` | `50` | Overlap between child chunks |
| `PARENT_CHUNK_SIZE` | `1000` | Parent chunk size in tokens (LLM context) |
| `TOP_K_RESULTS` | `6` | Number of search results to send to LLM |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL visible to browser |
