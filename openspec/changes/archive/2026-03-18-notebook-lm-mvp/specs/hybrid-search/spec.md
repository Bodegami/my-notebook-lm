## ADDED Requirements

### Requirement: Dense vector search over child chunks
The system SHALL embed each query using `nomic-embed-text` and perform cosine similarity search over all indexed child chunk vectors in Qdrant, returning the top `TOP_K_RESULTS * 2` candidates before fusion.

#### Scenario: Semantically similar content retrieved
- **WHEN** a user asks a question paraphrased differently from the source text
- **THEN** the dense search SHALL retrieve relevant chunks even when exact keywords don't match

#### Scenario: Query embedded at search time
- **WHEN** a chat query is processed
- **THEN** the system SHALL generate a single embedding for the query text before searching Qdrant

---

### Requirement: Sparse BM25 keyword search
The system SHALL perform keyword-based BM25 search alongside dense search. The BM25 search SHALL excel at exact-term matching for technical jargon, book titles, author names, and acronyms.

#### Scenario: Exact term matched via BM25
- **WHEN** a user searches for a specific technical term or author name that appears verbatim in the source
- **THEN** the sparse BM25 search SHALL rank the containing chunk highly

#### Scenario: BM25 complements dense search
- **WHEN** a query contains both semantic concepts and exact technical terms
- **THEN** the combined search result set SHALL contain relevant chunks from both search methods

---

### Requirement: Reciprocal Rank Fusion result merging
The system SHALL merge dense and sparse search result lists using Reciprocal Rank Fusion (RRF). The final top `TOP_K_RESULTS` (default: 6) results SHALL be passed as context to the LLM generator.

#### Scenario: RRF produces merged top-K results
- **WHEN** dense and sparse searches each return `TOP_K_RESULTS * 2` candidates
- **THEN** RRF SHALL produce a single ranked list of `TOP_K_RESULTS` results containing the best candidates from both methods

#### Scenario: Duplicate results deduplicated
- **WHEN** the same chunk appears in both dense and sparse result lists
- **THEN** it SHALL appear only once in the final fused list, with its RRF score reflecting both rankings

---

### Requirement: Parent chunk context provided to LLM
Each search result SHALL return the **parent chunk** text (~1000 tokens) as context to the LLM, while the **child chunk** text (~300 tokens) is used for the citation excerpt display.

#### Scenario: LLM receives parent chunk
- **WHEN** a chunk is retrieved for LLM context
- **THEN** the `parent_text` field (up to 1000 tokens) SHALL be included in the prompt, not the shorter `child_text`

#### Scenario: Citation excerpt uses child chunk
- **WHEN** a citation is displayed to the user
- **THEN** the verbatim excerpt shown SHALL be the `child_text` (the matched portion), providing a precise reference

---

### Requirement: Chunk metadata propagated through search results
Every search result SHALL include: `source_filename`, `page_number` (or `null`), `section_heading` (or `null`), `parent_text`, `child_text`, `score`, and `document_id`.

#### Scenario: Metadata available in search result
- **WHEN** hybrid search returns results
- **THEN** each `SearchResult` object SHALL contain non-null `source_filename` and at least one of `page_number` or `section_heading`

#### Scenario: Document filter by document_id possible
- **WHEN** a document is deleted from the knowledge base
- **THEN** the system SHALL be able to delete all Qdrant points for that document using the `document_id` payload field
