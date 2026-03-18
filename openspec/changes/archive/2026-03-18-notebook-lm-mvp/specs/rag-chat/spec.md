## ADDED Requirements

### Requirement: Multi-turn chat with in-memory session history
The system SHALL maintain full message history for the duration of a browser session. History SHALL be stored in-memory only (Python process); closing or refreshing the browser tab SHALL discard the session. A unique `session_id` (UUID v4) SHALL be generated client-side on page load and passed with every chat request via the `X-Session-ID` header.

#### Scenario: Second message uses prior context
- **WHEN** a user sends a follow-up question in the same browser session
- **THEN** the agent SHALL have access to previous messages and MAY reference them in its response

#### Scenario: Page refresh starts a new session
- **WHEN** a user refreshes the browser
- **THEN** a new `session_id` SHALL be generated and the prior message history SHALL be inaccessible

#### Scenario: Session ID passed with every request
- **WHEN** the frontend sends a chat request
- **THEN** the `X-Session-ID` header SHALL be present with the UUID stored in `sessionStorage`

---

### Requirement: Trivial message handling without RAG
The system SHALL classify incoming messages as trivial (greetings, thanks, off-topic) or document questions. Trivial messages SHALL be handled by calling the LLM directly without querying the vector database.

#### Scenario: Greeting handled without vector search
- **WHEN** a user sends "Hello" or "Thanks"
- **THEN** the agent SHALL respond with a friendly reply and the SSE stream SHALL contain no `citation` events

#### Scenario: Document question triggers full RAG pipeline
- **WHEN** a user asks a question about book content
- **THEN** the agent SHALL execute the full retrieval and generation pipeline

---

### Requirement: Mandatory inline citations in every RAG response
Every factual claim in an agent response SHALL include an inline citation badge (e.g., `[1]`). Each citation SHALL identify the source book filename and either the page number (PDF/EPUB) or section heading (MD/TXT/DOCX). When no relevant content is found in the knowledge base, the agent SHALL state explicitly that it could not find information on the topic rather than hallucinating.

#### Scenario: Single-source citation
- **WHEN** the agent answers from a single document
- **THEN** the response SHALL contain at least one inline `[n]` citation referencing the correct `source_filename` and `page_number` or `section_heading`

#### Scenario: Multi-source synthesis
- **WHEN** the agent synthesizes from multiple documents
- **THEN** the response SHALL cite all contributing sources with distinct citation numbers

#### Scenario: No relevant content found
- **WHEN** a user asks about a topic not present in any indexed document
- **THEN** the agent SHALL respond with a message containing the phrase "could not find information" and SHALL NOT fabricate citations

---

### Requirement: SSE token streaming with status events
The system SHALL stream responses token-by-token via Server-Sent Events. The SSE stream SHALL emit events in this order: `status` events → `token` events → `citation` events → `done` event. An `error` event SHALL be emitted on failures.

#### Scenario: Full SSE event sequence for RAG response
- **WHEN** a document question is processed
- **THEN** the SSE stream SHALL contain: at least one `status` event, multiple `token` events, at least one `citation` event, and a final `done` event with a `sources` array

#### Scenario: Stop button interrupts streaming
- **WHEN** a user clicks the Stop button during streaming
- **THEN** the frontend SHALL abort the SSE connection and the streaming SHALL halt

#### Scenario: LLM unavailable produces error event
- **WHEN** Ollama is unreachable during a chat request
- **THEN** the system SHALL emit `{"type": "error", "text": "LLM service unavailable. Check Docker containers."}` and close the stream

---

### Requirement: Collapsible Sources Consulted panel
Every RAG-generated response SHALL include a collapsible "Sources Consulted" panel listing all cited sources with: book filename, page number or section heading, and a verbatim text excerpt (parent chunk). Clicking an inline citation badge SHALL open a popover showing the same information.

#### Scenario: Sources panel rendered after response
- **WHEN** an agent response with citations is displayed
- **THEN** a "Sources Consulted (n)" collapsible section SHALL appear below the message content

#### Scenario: Citation badge opens source popover
- **WHEN** a user clicks a `[n]` citation badge
- **THEN** a popover SHALL open showing the book filename, page number or section, and the verbatim excerpt
