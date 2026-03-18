## ADDED Requirements

### Requirement: Multi-format file upload
The system SHALL accept file uploads via drag-and-drop or file picker supporting PDF (`.pdf`), EPUB (`.epub`), Word (`.docx`, `.doc`), Markdown (`.md`), and plain text (`.txt`) formats. Multiple files MAY be uploaded simultaneously. Files exceeding `MAX_UPLOAD_SIZE_MB` (default: 200 MB) SHALL be rejected before processing.

#### Scenario: Valid PDF upload accepted
- **WHEN** a user uploads a `.pdf` file under 200 MB
- **THEN** the system SHALL return a response with `status: "pending"` and a unique `document_id` immediately (without waiting for processing)

#### Scenario: Unsupported format rejected
- **WHEN** a user uploads a file with an extension not in the supported list (e.g., `.xlsx`)
- **THEN** the system SHALL return HTTP 422 with a descriptive error message listing supported formats

#### Scenario: File too large rejected
- **WHEN** a user uploads a file exceeding `MAX_UPLOAD_SIZE_MB`
- **THEN** the system SHALL return HTTP 413 with an error message stating the size limit

#### Scenario: Multiple files uploaded simultaneously
- **WHEN** a user uploads 3 files at once
- **THEN** the system SHALL create 3 separate document records each with `status: "pending"` and return all 3 `UploadResponse` objects

---

### Requirement: Asynchronous ingestion pipeline
After a file is accepted, the system SHALL automatically execute an async pipeline per document with the following status transitions: `pending` → `extracting` → `chunking` → `embedding` → `indexed`. On any failure, the document SHALL transition to `error` status with an `error_message` field.

#### Scenario: Successful PDF ingestion
- **WHEN** a valid text-based PDF is uploaded
- **THEN** the system SHALL transition through all pipeline stages and reach `status: "indexed"` with `chunk_count > 0` and `page_count > 0`

#### Scenario: Ingestion does not block upload response
- **WHEN** a file is uploaded
- **THEN** the upload endpoint SHALL respond immediately with `status: "pending"` while processing continues in the background

#### Scenario: Scanned PDF produces error status
- **WHEN** a PDF with no extractable text layer is uploaded (all pages < 50 chars)
- **THEN** the document SHALL reach `status: "error"` with `error_message` containing "scanned" or "OCR"

#### Scenario: Corrupted file produces error status
- **WHEN** an unreadable or corrupted file is uploaded
- **THEN** the document SHALL reach `status: "error"` with a descriptive `error_message`

---

### Requirement: Format-specific text extraction with metadata
The system SHALL extract text from each supported format using the appropriate library, preserving structural metadata: `page_number` (PDF/EPUB), `section_heading` (EPUB/DOCX/MD), or `null` when not applicable.

#### Scenario: PDF page numbers extracted
- **WHEN** a multi-page PDF is ingested
- **THEN** each extracted chunk SHALL have a non-null `page_number` corresponding to its source page

#### Scenario: EPUB section headings extracted
- **WHEN** an EPUB file is ingested
- **THEN** each chunk SHALL have a `section_heading` derived from the nearest `<h1>` or `<h2>` in the chapter

#### Scenario: Markdown headings extracted
- **WHEN** a `.md` file is ingested
- **THEN** each chunk SHALL have a `section_heading` derived from the nearest heading above the chunk (`#`, `##`, or `###`)

#### Scenario: Plain text has no structural metadata
- **WHEN** a `.txt` file is ingested
- **THEN** chunks SHALL have `page_number: null` and `section_heading: null`

---

### Requirement: Document metadata persistence
The system SHALL persist document metadata in SQLite including: `id` (UUID), `filename`, `file_format`, `upload_time`, `status`, `error_message`, `page_count`, `chunk_count`, and `qdrant_ids` (JSON array of vector point IDs).

#### Scenario: Document record created on upload
- **WHEN** a file is uploaded
- **THEN** a `Document` record SHALL be created in SQLite with `status: "pending"` before the background task starts

#### Scenario: Status updated at each pipeline stage
- **WHEN** the ingestion pipeline progresses
- **THEN** the SQLite record SHALL be updated at each stage transition so that `GET /api/documents/{id}` reflects the current status

#### Scenario: Qdrant IDs stored after indexing
- **WHEN** ingestion completes successfully
- **THEN** the `qdrant_ids` field SHALL contain a JSON array of all Qdrant point UUIDs created for the document
