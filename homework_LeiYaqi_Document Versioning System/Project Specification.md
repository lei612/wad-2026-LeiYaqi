# Document Versioning System (MVP) — Project Specification

## 1. What This Project Is

This repository contains a small web-based Document Versioning System.

- Users can create documents, edit them in a block editor, and save immutable versions.
- The system maintains full version history per document.
- Users can preview any historical version, roll back the document’s “current” pointer to a chosen version, and delete documents or versions.

The application is implemented as a lightweight single-page UI served by a FastAPI backend.

## 2. Functional Requirements

### 2.1 Documents

- List documents (title + current version metadata).
- Create a new document with a title.
- Delete a document (also deletes all of its versions).
- Fetch a document’s metadata plus its current version’s content.

### 2.2 Versions

- Save the current editor content as a new version (creates a new revision number).
- List versions for a document (latest first).
- Retrieve a specific version’s content for preview.
- Roll back the document to a selected version.
- Delete a version.
  - Constraint: the last remaining version for a document cannot be deleted.

### 2.3 Editor Content Format

Versions store an Editor.js JSON snapshot (a JSON object with at least blocks as a list).

## 3. Technology Stack

### Backend

- Language: Python
- Framework: FastAPI
- Server: Uvicorn
- Templating: Jinja2 (serves the SPA HTML)
- Data validation: Pydantic v2
- Database client: PyMongo
- Optional in-memory/mock DB: mongomock (activated by a special URI prefix)

See requirements.txt for exact pinned versions.

### Frontend

- HTML + CSS + Vanilla JavaScript (embedded in a Jinja2 template)
- Rich text editor: Editor.js loaded from CDN

## 4. Repository Layout

The actual application lives under app/.

.
├─ app/
│ ├─ main.py # FastAPI app + HTTP routes
│ ├─ storage.py # Business logic + MongoDB operations
│ ├─ db.py # Mongo client creation + index setup
│ ├─ schemas.py # Pydantic request/response schemas
│ ├─ templates/
│ │ └─ editor.html # SPA UI (HTML + JS)
│ └─ static/
│ └─ app.css # Styling
├─ requirements.txt
└─ homework-Leiyaqi-Document Versioning System.(md|pdf)

Note: IDE/virtualenv folders may exist locally (e.g. .idea/, .venv/) and are not part of the app logic.

## 5. Architecture and Data Flow

### 5.1 High-Level Flow

1. Browser loads / → server returns templates/editor.html.
2. The page’s JavaScript uses fetch() to call JSON endpoints under /api/...
3. Backend routes call the service layer in storage.py.
4. storage.py reads/writes MongoDB collections via db.get_db().

### 5.2 Separation of Responsibilities

- main.py: HTTP routing, input validation, and error-to-status-code mapping.
- schemas.py: request/response shapes.
- storage.py: database access + business rules (revision sequencing, rollback, deletion constraints).
- db.py: client creation (real MongoDB or mongomock) and index initialization.

## 6. Persistence Model (MongoDB)

### 6.1 Collections

#### documents

- _id: ObjectId
- title: string
- current_version_id: ObjectId or null
- current_version_revision: int (0 if no versions yet)
- created_at: string (ISO timestamp)

#### document_versions

- _id: ObjectId
- document_id: ObjectId (references documents._id)
- revision: int (1, 2, 3, ...; unique per document)
- content: object (Editor.js JSON snapshot)
- created_at: string (ISO timestamp)

### 6.2 Indexes

On startup the app creates indexes:

- document_versions(document_id, revision) unique
- document_versions(document_id, created_at)
- documents(created_at)

## 7. API Specification

Base path: /api

### 7.1 Documents

#### GET /api/documents

Returns a list of documents with current version metadata.

Response (example shape):

[
{
"id": "...",
"title": "Untitled",
"current_version_id": "...",
"current_version_revision": 3,
"created_at": "..."
}
]

#### POST /api/documents

Request body:

{ "title": "My doc" }

Response: the created document object.

#### GET /api/documents/{document_id}

Returns metadata plus content for the current version.

Errors:

- 422 with detail="invalid_id" if the id is not a valid ObjectId.
- 404 with detail="document_not_found" if not found.

#### DELETE /api/documents/{document_id}

Deletes the document and all versions.

Errors:

- 404 with detail="document_not_found" if not found.

### 7.2 Versions

#### GET /api/documents/{document_id}/versions

Lists versions for a document, ordered by revision descending.

Errors:

- 404 with detail="document_not_found" if document does not exist.

#### GET /api/documents/{document_id}/versions/{version_id}

Returns the stored Editor.js JSON snapshot for that version.

Errors:

- 404 with detail="version_not_found" if not found.

#### POST /api/documents/{document_id}/versions

Creates a new immutable version.

Request body:

{ "content": { "time": 0, "blocks": [], "version": "2" } }

Validation:

- If content.blocks is not a JSON array/list → 422 with detail="invalid_editorjs_content".

Errors:

- 404 with detail="document_not_found" if document does not exist.

Response:

{ "version_id": "...", "revision": 4 }

#### POST /api/documents/{document_id}/rollback/{version_id}

Moves the document’s current_version_id pointer to the selected version.

Errors:

- 404 with detail="version_not_found" if the version does not exist for this document.

#### DELETE /api/documents/{document_id}/versions/{version_id}

Deletes a version.

Business rules:

- If there is only one version, deletion is forbidden.

Errors:

- 404 with detail="document_not_found" or detail="version_not_found".
- 409 with detail="cannot_delete_last_version" when trying to delete the last version.

Response:

{ "status": "ok", "current_version_id": "..." }

If the deleted version was current, the backend promotes the latest remaining version to current.

## 8. Configuration

Environment variables:

- MONGODB_URI
  - Default: mongodb://localhost:27017
  - Special case: if it starts with mongomock://, the app uses an in-memory mongomock client.
- MONGODB_DB
  - Default: doc_versioning

## 9. How To Run

From the repository root:

1. Install dependencies:

   pip install -r requirements.txt

2. Choose a database:

- Real MongoDB (default): ensure MongoDB is running and reachable at MONGODB_URI.
- Mock DB (mongomock):
  - Windows PowerShell:
    $env:MONGODB_URI = "mongomock://localhost"

1. Start the server:

   uvicorn app.main:app --reload

Open http://localhost:8000/.

## 10. AI / LLM Usage

During development, I used Trae (an AI coding assistant) to help generate boilerplate code, API routes, Pydantic schemas, MongoDB interactions, and the frontend JavaScript. No runtime LLM functionality is included.

## 11. Known Limitations / Non-Goals

- No authentication/authorization (all endpoints are open).
- No multi-user permissions or audit trails.
- No explicit migrations/seeding scripts.
- No automated tests included (dependencies include httpx/mongomock, but no test suite exists in the repository).