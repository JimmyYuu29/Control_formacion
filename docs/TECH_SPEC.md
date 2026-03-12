# Technical Specification: Formación Evaluation Splitter

> **Version:** 2.1.0
> **App Name:** Formación Evaluation Splitter
> **Category:** Excel Upload → Split → Email Distribution
> **Organization:** Forvis Mazars
> **Last Updated:** 2026-03-12

---

## 1. Overview

This document defines the technical specification for the **Formación Evaluation Splitter** app. The app automates the distribution of training evaluations (Formación) to each responsible Tutor via email:

1. **Upload** an Excel file containing all professionals' evaluations
2. **Parse** multi-row headers (Rows 1-3) and auto-detect the "Tutor" column
3. **Split** data by Tutor, allowing column selection via sample preview
4. **Generate** individual Excel files per Tutor preserving all original formatting
5. **Map contacts** — match Tutors to email addresses
6. **Send** files as email attachments via Power Automate with rich HTML content, CID-embedded images, and full style preservation
7. **Persist data** to external directory for survival across app updates
8. **Track history** of up to 10 operations with restore capability

---

## 2. Technology Stack

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| **Language** | Python | ≥ 3.9 | Type hints required |
| **Web Framework** | FastAPI | ≥ 0.104.0 | ASGI-based |
| **ASGI Server** | Uvicorn | ≥ 0.24.0 | Single worker for session state |
| **Excel Processing** | openpyxl | ≥ 3.1.2 | .xlsx only |
| **Data Validation** | Pydantic | ≥ 2.5.0 | BaseSettings for config |
| **Email Delivery** | Power Automate | HTTP POST | Via webhook URL |
| **HTTP Client** | requests | ≥ 2.31.0 | For Power Automate calls |
| **Environment** | python-dotenv | ≥ 1.0.0 | .env file loading |
| **Async File I/O** | aiofiles | ≥ 23.2.1 | For file upload handling |
| **Email Validation** | email-validator | ≥ 2.0.0 | RFC-compliant validation |
| **Frontend** | HTML5 + Vanilla JS | - | Single-page application |
| **Image Processing** | Pillow | ≥ 10.0.0 | Screenshot handling & CID embedding |
| **PDF/Image** | PyMuPDF | ≥ 1.23.0 | PDF → PNG conversion |

---

## 3. Project Structure

```
Control_formacion/
├── main.py                     # FastAPI application entry point
├── config.py                   # Configuration (Pydantic BaseSettings)
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (git-ignored)
├── .env.example                # Template for .env (git-tracked)
├── Dockerfile                  # Docker build configuration
├── docker-compose.yml          # Docker Compose for deployment
├── models/
│   ├── __init__.py
│   └── schemas.py              # All Pydantic data models
├── services/
│   ├── __init__.py
│   ├── excel_parser.py         # Multi-row header parsing & Tutor grouping
│   ├── excel_generator.py      # Individual Excel file generation with formatting
│   ├── contact_mapper.py       # Tutor→Email mapping with fuzzy matching
│   ├── email_sender.py         # Power Automate email (CID images, HTML wrapper)
│   └── data_manager.py         # External data persistence & history (NEW v2.0.0)
├── static/
│   ├── index.html              # Frontend SPA (6-step wizard)
│   └── images/                 # Email template images
│       ├── logo_header.png
│       ├── template_rating_scale.png
│       ├── template_evaluation_table.png
│       └── escala_evaluacion.png
├── templates/
│   └── email_default.html      # Default email template
├── data/
│   ├── .gitkeep
│   ├── contacts_store.json     # Persistent contacts (auto-generated)
│   └── Contactos_Tutores.xlsx  # Default contacts file
├── tests/
│   ├── test_parser.py          # 8 parser tests
│   ├── test_generator.py       # 6 generator tests
│   ├── test_mapper.py          # 8 contact mapper tests
│   └── test_sender.py          # 11 email sender tests
├── docs/
│   ├── PRD.md
│   ├── TECH_SPEC.md
│   ├── ARCHITECTURE.md
│   └── CONVENTIONS.md
└── Ejemplo/                    # Sample input files
    └── 2025-Notas evaluaciones Auditoria_Gerente y Socios.xlsx
```

---

## 4. Configuration

### 4.1 Environment Variables (.env)

```env
# Power Automate (MANDATORY)
POWER_AUTOMATE_URL=https://...

# Contacts Configuration
CONTACTS_FILE_PATH=data/Contactos_Tutores.xlsx
CONTACTS_STORE_PATH=data/contacts_store.json
CONTACTS_DELETE_PASSWORD=Formacion2026

# Email Configuration
DEFAULT_CC_EMAILS=

# Server Configuration
HOST=0.0.0.0
PORT=8002
DEBUG=false

# App Identity
APP_NAME=Formación Evaluation Splitter
APP_VERSION=2.0.0

# Data Persistence (NEW v2.0.0)
DATA_ROOT_PATH=/home/rootadmin/data/Control_formacion
MAX_HISTORY=10
```

### 4.2 Configuration Class (config.py)

```python
class Settings(BaseSettings):
    power_automate_url: str = ""
    sharepoint_flow_url: str = ""
    sharepoint_site_name: str = ""
    sharepoint_folder_path: str = ""
    contacts_file_path: str = "data/Contactos_Tutores.xlsx"
    contacts_store_path: str = "data/contacts_store.json"
    contacts_delete_password: str = "Formacion2026"
    default_cc_emails: str = ""
    host: str = "0.0.0.0"
    port: int = 8002
    debug: bool = False
    app_name: str = "Formación Evaluation Splitter"
    app_version: str = "2.0.0"

    # Data persistence (NEW v2.0.0)
    data_root_path: str = "/home/rootadmin/data/Control_formacion"
    max_history: int = 10

    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
```

---

## 5. API Specification

### 5.1 Health & Status

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check, returns app name + version |
| `GET` | `/api/power-automate/status` | Check Power Automate URL reachability |

### 5.2 File Processing

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/parse` | Upload & parse Excel file, detect Tutor column |
| `POST` | `/api/set-columns` | Select columns for output files |
| `POST` | `/api/generate-files` | Generate individual Excel files per Tutor |
| `GET` | `/api/download-zip` | Download all files as ZIP |
| `GET` | `/api/download-file/{filename}` | Download specific file |

**Response: `POST /api/parse`**
```json
{
  "filename": "evaluaciones.xlsx",
  "split_criteria": "Tutor (Column I)",
  "groups": [
    {
      "code": "Oscar Herranz",
      "name": "Oscar Herranz",
      "entries_count": 5
    }
  ],
  "groups_count": 4,
  "all_columns": [
    {
      "letter": "C",
      "header": "Profesional",
      "category": "Datos Personales",
      "has_data": true
    }
  ],
  "default_columns": ["C", "D", "E", "F", "G", "H", "I", ...],
  "tutor_column": "I",
  "sample_tutor": "Oscar Herranz"
}
```

### 5.3 Contact Management

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/map-contacts` | Load & map Tutors to email addresses |
| `GET` | `/api/contacts/stored` | Get stored contacts info |
| `POST` | `/api/contacts/delete` | Delete stored contacts (password-protected) |

### 5.4 Email Template

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/template` | Get current email template |
| `POST` | `/api/template` | Update email template |
| `GET` | `/api/preview-email` | Preview email for a Tutor |

### 5.5 Email Sending

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/send` | Send emails via Power Automate |

**Request Body:**
```json
{
  "excluded_codes": ["Oscar Herranz"],
  "cc_emails": ["cc@example.com"],
  "test_mode": false
}
```

### 5.6 History & Data Persistence (NEW v2.0.0)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/history` | List all history entries (max 10) |
| `GET` | `/api/history/{run_id}` | Get history entry with file listing |
| `GET` | `/api/history/{run_id}/file/{filename}` | Download file from history |
| `DELETE` | `/api/history/{run_id}` | Delete history entry and files |
| `POST` | `/api/history/{run_id}/restore` | Restore files from history into session |
| `POST` | `/api/sync` | Manual data sync with external directory |
| `GET` | `/api/data-info` | Get storage paths and status info |

### 5.7 Frontend

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Serve frontend SPA |
| Static | `/static/` | Static file serving |

---

## 6. Data Models

### 6.1 Core Models (models/schemas.py)

```python
class Recipient(BaseModel):
    """Represents a Tutor (group entity)."""
    codigo: str        # Tutor name (used as identifier)
    nombre: str        # Tutor display name
    excluded: bool = False

class DataEntry(BaseModel):
    """Single professional's row of data."""
    raw_cells: Dict[str, Any] = {}
    source_row: int = 0    # Original row number in source file

class DataBlock(BaseModel):
    """All professionals belonging to one Tutor."""
    recipient: Recipient
    entries: List[DataEntry]
    total: Decimal = Decimal("0")
    start_row: int = 0
    end_row: int = 0

class ColumnInfo(BaseModel):
    """Excel column metadata with category support."""
    letter: str
    header: Optional[str] = None
    category: Optional[str] = None    # From Row 2 merged cells
    has_data: bool = True

class ParsedDocument(BaseModel):
    """Fully parsed Excel document."""
    filename: str
    blocks: List[DataBlock]
    total_general: Decimal = Decimal("0")
    header_rows: List[int] = [1, 2, 3]
    all_columns: List[ColumnInfo] = []
    default_columns: List[str] = []
    tutor_column: Optional[str] = None    # Auto-detected column letter
    sample_tutor: Optional[str] = None    # For column selection preview

class Contact(BaseModel):
    """Tutor contact information."""
    codigo: str
    nombre: str
    apellido: Optional[str] = None
    email: str
    email_cc: Optional[str] = None

class ContactMapping(BaseModel):
    """Maps a Tutor to their contact info."""
    recipient: Recipient
    contact: Optional[Contact] = None
    email_found: bool = False
    excluded: bool = False

class EmailTemplate(BaseModel):
    """Email template with variable placeholders."""
    subject: str = "Evaluación Formación — {{tutor_name}}"
    body: str = ""
    is_html: bool = False

class EmailComposition(BaseModel):
    """Fully composed email ready to send."""
    to_email: str
    cc_emails: List[str] = []
    subject: str
    body: str
    attachment_name: str
    attachment_content: str    # Base64-encoded

class SendResult(BaseModel):
    """Result of sending one email."""
    recipient: Recipient
    status: SendStatus
    message: Optional[str] = None
    email_sent_to: Optional[str] = None
    timestamp: datetime

class ProcessingResult(BaseModel):
    """Overall batch send result."""
    total: int
    sent_success: int
    sent_failed: int
    excluded: int
    results: List[SendResult]
```

---

## 7. Service Layer

### 7.1 ExcelParser (services/excel_parser.py)

- Auto-detects "Tutor" column by scanning Row 3 headers
- Reads multi-row headers (Rows 1-3) with merged cell detection
- Groups data rows by Tutor value
- Extracts column metadata with category from Row 2 merged cells
- Skips empty separator rows (e.g., Row 4)

### 7.2 ExcelGenerator (services/excel_generator.py)

- Generates individual `.xlsx` files per Tutor
- Preserves all original formatting: colors, fonts, borders, fill patterns
- Copies header rows 1-3 with merged cell ranges
- Adjusts merged cells for selected columns
- Copies column widths and row heights
- Filename: `{Tutor_Name}_{Original_Filename}.xlsx`

### 7.3 ContactMapper (services/contact_mapper.py)

- Loads contacts from Excel (columns: A=Name, B=Email, C=CC)
- Matches Tutors by name using:
  1. Exact match (case-insensitive)
  2. Accent-insensitive match (NFKD normalization)
  3. Token-based partial match
- Persistent JSON storage for contact reuse
- Password-protected deletion

### 7.4 EmailSender (services/email_sender.py)

- Template variables: `{{tutor_name}}`, `{{num_profesionales}}`, `{{fecha}}`, `{{periodo}}`, `{{screenshot}}`
- Sends via Power Automate HTTP POST webhook
- 60-second timeout per request
- Batch sending with test mode and exclusion support
- **Base64 data URI image embedding** — screenshots and editor images embedded directly in HTML body
- **Clean HTML email wrapper** — white background without card borders or shadows
- No CID attachments needed — images are self-contained in the HTML
- **Simple payload** — only Excel attachment fields (`attachmentName`/`attachmentContent`), all images in `body`

### 7.5 DataManager (services/data_manager.py) — NEW v2.0.0

- Manages external data directory at `/home/rootadmin/data/Control_formacion/`
- **Bidirectional sync** of JSON stores (contacts, presets, templates) on startup
- Creates timestamped run folders (`temp/run_YYYYMMDD_HHMMSS/`) for each file generation
- **History tracking** with max 10 entries; auto-cleanup of oldest when limit exceeded
- Each history entry stores: filename, tutors_count, files_count, timestamps, status
- Run folders contain `generated/` (Excel) and `screenshots/` (PNG) subdirectories
- Supports restore operations to reload files from a previous run

---

## 8. Power Automate JSON Payload

### 8.1 Standard Payload (v2.1.0 — images embedded in body)

```json
{
  "to": "tutor@example.com",
  "cc": "cc1@example.com;cc2@example.com",
  "subject": "Evaluación Formación — Juan Berral",
  "body": "<html>...<img src='data:image/png;base64,...'>...</html>",
  "isHtml": true,
  "attachmentName": "Juan_Berral_evaluaciones.xlsx",
  "attachmentContent": "BASE64_ENCODED_EXCEL"
}
```

### 8.2 Key Changes from v2.0.0

- **Base64 data URI images**: Screenshots and editor images embedded directly in HTML body — no CID, no inline attachments
- **Simplified payload**: Only `attachmentName`/`attachmentContent` for the Excel file
- **Simplified Power Automate**: Single attachment entry, no CID/IsInline configuration
- **Clean HTML wrapper**: White background without card borders or shadows
- See `docs/POWER_AUTOMATE_FLOW.md` for complete flow construction guide
```

---

## 9. Session Management

```python
session_data = {
    "document": None,           # ParsedDocument
    "file_content": None,       # Raw uploaded file bytes
    "mappings": None,           # List[ContactMapping]
    "generated_files": None,    # List[Tuple[str, bytes]]
    "split_mode": "tutor",      # Fixed mode for this app
    "selected_columns": None,   # List[str]: column letters
    "template": None,           # EmailTemplate
    "current_run_path": None,   # Path to current run folder (NEW v2.0.0)
    "current_run_id": None,     # ID of current run (NEW v2.0.0)
}
```

- Single-worker deployment REQUIRED (`--workers 1`)
- Session is per-server instance (single-user design)
- Session cleared on new file upload

---

## 10. Error Handling

| Code | Usage |
|------|-------|
| `200` | Success |
| `400` | Invalid request (bad file type, missing params) |
| `404` | Resource not found |
| `409` | Session state conflict |
| `422` | Validation error (Pydantic) |
| `500` | Internal server error |
| `502` | Power Automate unreachable |

Error messages are in Spanish. Example:
```json
{"detail": "Solo se permiten archivos .xlsx"}
```
