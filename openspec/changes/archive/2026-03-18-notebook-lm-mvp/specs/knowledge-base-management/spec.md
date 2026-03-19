## ADDED Requirements

### Requirement: List all indexed documents
The system SHALL provide an endpoint that returns all documents ordered by upload time (descending), including their current status, file format, page count, chunk count, and any error messages.

#### Scenario: Documents listed after upload
- **WHEN** one or more documents have been uploaded
- **THEN** `GET /api/documents` SHALL return an array of document records with correct `status`, `filename`, and `upload_time`

#### Scenario: Empty list when no documents exist
- **WHEN** no documents have been uploaded or all have been deleted
- **THEN** `GET /api/documents` SHALL return an empty array with HTTP 200

#### Scenario: Single document status accessible
- **WHEN** a `document_id` is known
- **THEN** `GET /api/documents/{id}` SHALL return the current status record or HTTP 404 if not found

---

### Requirement: Delete single document
The system SHALL allow deleting a single document by ID, removing its vector points from Qdrant, its uploaded file from disk, and its SQLite record. Documents in non-terminal status (still processing) SHALL be deletable.

#### Scenario: Indexed document deleted completely
- **WHEN** a user deletes an indexed document
- **THEN** the system SHALL delete its Qdrant vectors, disk file, and SQLite record; subsequent `GET /api/documents/{id}` SHALL return HTTP 404

#### Scenario: Delete of non-existent document returns 404
- **WHEN** a user requests deletion of an unknown `document_id`
- **THEN** the system SHALL return HTTP 404

#### Scenario: Qdrant vectors removed on delete
- **WHEN** a document is deleted
- **THEN** querying Qdrant for vectors with that `document_id` in their payload SHALL return zero results

---

### Requirement: Clear entire knowledge base
The system SHALL provide a "Clear All" operation that deletes all Qdrant vectors, all uploaded files from disk, and all SQLite document records in a single atomic-looking operation.

#### Scenario: Knowledge base fully cleared
- **WHEN** the user invokes "Clear All"
- **THEN** `GET /api/documents` SHALL return an empty array, Qdrant collection SHALL contain zero vectors, and the upload directory SHALL be empty

#### Scenario: Clear All returns 204
- **WHEN** `DELETE /api/documents` is called
- **THEN** the system SHALL return HTTP 204 No Content

#### Scenario: Clear All works on empty knowledge base
- **WHEN** the knowledge base is already empty and "Clear All" is invoked
- **THEN** the system SHALL return HTTP 204 without error

---

### Requirement: Visual status badges in document sidebar
The frontend SHALL display each document with a colored status badge: green for `indexed`, yellow with spinner for in-progress states (`pending`, `extracting`, `chunking`, `embedding`), red for `error`. Error state SHALL display the `error_message`.

#### Scenario: Processing document shows spinner
- **WHEN** a document is in `extracting` or `chunking` status
- **THEN** the sidebar SHALL show a yellow badge with a loading spinner next to the filename

#### Scenario: Indexed document shows green badge
- **WHEN** a document reaches `indexed` status
- **THEN** the sidebar SHALL show a green "indexed" badge without a spinner

#### Scenario: Error document shows red badge and message
- **WHEN** a document reaches `error` status
- **THEN** the sidebar SHALL show a red badge and display the `error_message` to the user

---

### Requirement: Delete confirmation dialog
Deletion of a single document or clearing all documents SHALL require user confirmation via a modal dialog to prevent accidental data loss.

#### Scenario: Single document delete requires confirmation
- **WHEN** a user clicks the delete (trash) icon next to a document
- **THEN** an `AlertDialog` SHALL appear asking for confirmation before the deletion API call is made

#### Scenario: Clear All requires confirmation
- **WHEN** a user clicks "Clear All"
- **THEN** a confirmation dialog SHALL appear; if the user cancels, no documents SHALL be deleted
