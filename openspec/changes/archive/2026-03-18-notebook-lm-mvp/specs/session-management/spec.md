## ADDED Requirements

### Requirement: Client-side session ID generation
The frontend SHALL generate a UUID v4 `session_id` on page load and store it in `sessionStorage`. The ID SHALL persist across component re-renders within the same tab but SHALL be discarded when the tab is closed or the page is refreshed.

#### Scenario: Session ID generated on first load
- **WHEN** a user opens the application for the first time in a browser tab
- **THEN** a UUID v4 SHALL be generated and stored in `sessionStorage` under the key `sessionId`

#### Scenario: Session ID reused within same tab
- **WHEN** a user navigates or triggers component re-renders without refreshing
- **THEN** the same `sessionId` from `sessionStorage` SHALL be used for all requests

#### Scenario: New session ID after page refresh
- **WHEN** a user refreshes the browser page
- **THEN** a new UUID v4 SHALL be generated, effectively starting a new session with empty history

---

### Requirement: Session ID transmitted via request header
Every chat request from the frontend SHALL include the `X-Session-ID` header containing the current `session_id`. The backend SHALL use this header to identify which in-memory message history to use.

#### Scenario: X-Session-ID header present in chat requests
- **WHEN** the frontend sends `POST /api/chat/stream`
- **THEN** the request SHALL include the `X-Session-ID` header with the current UUID

#### Scenario: Backend stores history keyed by session ID
- **WHEN** the backend receives a chat request with a known `session_id`
- **THEN** it SHALL retrieve the corresponding message history from the in-memory dictionary and append the new message to it

#### Scenario: Unknown session ID starts empty history
- **WHEN** the backend receives a `session_id` not present in the in-memory dictionary
- **THEN** it SHALL create a new empty history for that session

---

### Requirement: In-memory history cleared on process restart
Chat history SHALL be stored exclusively in a Python `dict[str, list[BaseMessage]]` in the backend process memory. No history SHALL be written to SQLite, disk, or any persistent store. Restarting the backend container SHALL clear all session histories.

#### Scenario: History not persisted to disk
- **WHEN** the backend process is restarted
- **THEN** all session histories SHALL be lost and `GET /api/documents` SHALL still return indexed documents (SQLite is persistent)

#### Scenario: Multiple sessions maintained simultaneously
- **WHEN** two different `session_id` values are used (e.g., two browser tabs)
- **THEN** the backend SHALL maintain independent message histories for each session

---

### Requirement: No chat history written to disk
The system SHALL explicitly NOT write any chat message to disk, SQLite, or any log file that could be read by a third party. This is a privacy requirement.

#### Scenario: Chat messages absent from SQLite
- **WHEN** a user sends multiple messages and the backend SQLite database is inspected
- **THEN** the `Document` table SHALL contain only document metadata — no message records SHALL exist

#### Scenario: Chat messages absent from disk files
- **WHEN** a user sends messages and the backend upload directory is inspected
- **THEN** only uploaded document files SHALL be present — no chat logs or session files SHALL exist
