## ADDED Requirements

### Requirement: Ollama LLM service for chat inference
The system SHALL use Ollama running `phi3.5:mini-instruct` (Q4 quantized, ~2.5 GB RAM) for all LLM chat completions. Ollama SHALL automatically use GPU layers when vRAM is available and fall back to CPU processing when GPU memory is insufficient.

#### Scenario: LLM responds to chat request
- **WHEN** the agent sends a list of messages to the Ollama chat endpoint
- **THEN** Ollama SHALL return a streaming NDJSON response with text tokens

#### Scenario: CPU fallback when GPU vRAM insufficient
- **WHEN** the system runs on hardware with ≤ 2 GB vRAM
- **THEN** Ollama SHALL automatically offload remaining model layers to CPU RAM without requiring manual configuration

#### Scenario: Model loaded at container startup
- **WHEN** the Ollama container starts for the first time
- **THEN** the entrypoint script SHALL pull `phi3.5:mini-instruct` and `nomic-embed-text` before the backend becomes ready

---

### Requirement: Embedding model for vector generation
The system SHALL use `nomic-embed-text` (768-dimensional vectors, ~300 MB RAM) via FastEmbed for generating embeddings during document ingestion. The same model MUST be used consistently for both indexing and query embedding to ensure cosine similarity is valid.

#### Scenario: Embeddings generated during ingestion
- **WHEN** child chunks are passed to the embedding service
- **THEN** each chunk SHALL produce a 768-dimensional float vector

#### Scenario: Query embedded with same model
- **WHEN** a user query is embedded for search
- **THEN** the same `nomic-embed-text` model SHALL be used as was used during ingestion

#### Scenario: Embedding model cached after first use
- **WHEN** the embedding service is called for the first time
- **THEN** the model SHALL be downloaded and cached; subsequent calls SHALL use the cached model without re-downloading

---

### Requirement: Health check reports model availability
The `GET /api/health` endpoint SHALL report whether Qdrant and Ollama are reachable and which models are currently loaded in Ollama.

#### Scenario: Health endpoint returns loaded models
- **WHEN** both Ollama and Qdrant are running and models are pulled
- **THEN** `GET /api/health` SHALL return `{"status": "ok", "qdrant": "connected", "ollama": "connected", "models_loaded": ["phi3.5:mini-instruct", "nomic-embed-text"]}`

#### Scenario: Health endpoint reports Ollama unreachable
- **WHEN** the Ollama container is not running
- **THEN** `GET /api/health` SHALL return `{"status": "degraded", "ollama": "unreachable", "models_loaded": []}`

#### Scenario: Frontend polls health every 5 seconds
- **WHEN** the frontend is loaded
- **THEN** the `ModelStatusIndicator` component SHALL poll `GET /api/health` every 5 seconds and update the badge color accordingly

---

### Requirement: Model status indicator in UI header
The frontend SHALL display a persistent model status badge: yellow pulsing "Models Loading", green "Ready", or red "Unavailable". The chat input SHALL be disabled while models are not ready.

#### Scenario: Chat disabled while models loading
- **WHEN** the health endpoint returns `ollama: "unreachable"` or models are not yet loaded
- **THEN** the chat input SHALL be disabled with a tooltip: "Models are loading, please wait"

#### Scenario: Unavailable state shows error banner
- **WHEN** Ollama is unreachable for more than one health check cycle
- **THEN** the UI SHALL display a dismissible error banner: "Ollama is not responding. Ensure Docker containers are running."
