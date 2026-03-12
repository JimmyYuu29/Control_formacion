# Architecture Design: Formación Evaluation Splitter

> **Version:** 2.0.0
> **App Name:** Formación Evaluation Splitter
> **Port:** 8002
> **Last Updated:** 2026-03-10

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              System Context                                     │
│                                                                                 │
│  ┌────────────┐    HTTP     ┌──────────────────┐    HTTP      ┌──────────────┐ │
│  │   User     │◀──────────▶│  Formación       │─────────────▶│   Power      │ │
│  │  Browser   │   :8002    │  Eval Splitter   │  POST JSON   │  Automate    │ │
│  └────────────┘            └────────┬─────────┘              └──────┬───────┘ │
│                                     │                               │         │
│                                     │ File I/O                      │ Email   │
│                                     ▼                               ▼         │
│                            ┌────────────────┐              ┌──────────────┐   │
│                            │  Local File    │              │  Office 365  │   │
│                            │  System        │              │  Outlook     │   │
│                            │  (data/)       │              └──────────────┘   │
│                            └────────────────┘                                 │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Layered Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Frontend SPA (static/index.html) — 6-Step Wizard       │    │
│  │                                                          │    │
│  │  [1.Upload] → [2.Columns] → [3.Review] → [4.Contacts]  │    │
│  │            → [5.Email] → [6.Send]                        │    │
│  │                                                          │    │
│  │  Features: Drag-drop upload, column selector with        │    │
│  │  categories, rich text email editor (images, tables,     │    │
│  │  formatting), toast notifications, loading overlay       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                    API LAYER (FastAPI — main.py)                  │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│  │ /api/    │  │ /api/    │  │ /api/    │  │ /api/        │    │
│  │ parse    │  │ set-     │  │ map-     │  │ send         │    │
│  │          │  │ columns  │  │ contacts │  │              │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘    │
│       │              │              │               │            │
├───────┼──────────────┼──────────────┼───────────────┼────────────┤
│       │         SERVICE LAYER       │               │            │
│       │              │              │               │            │
│  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐  ┌─────▼──────┐    │
│  │ Excel    │  │ Excel    │  │ Contact  │  │ Email      │    │
│  │ Parser   │  │ Generator│  │ Mapper   │  │ Sender     │    │
│  │          │  │          │  │          │  │            │    │
│  │ Multi-row│  │ Format   │  │ Fuzzy    │  │ Power      │    │
│  │ headers  │  │ preserve │  │ matching │  │ Automate   │    │
│  │ Tutor    │  │ Merged   │  │ JSON     │  │ HTML email │    │
│  │ grouping │  │ cells    │  │ persist  │  │ Base64 att │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘    │
│       │              │              │               │            │
├───────┼──────────────┼──────────────┼───────────────┼────────────┤
│       │          DATA LAYER         │               │            │
│       │              │              │               │            │
│  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐  ┌─────▼──────┐    │
│  │ openpyxl │  │ openpyxl │  │ JSON     │  │ requests   │    │
│  │ (read)   │  │ (write)  │  │ (persist)│  │ (HTTP POST)│    │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘    │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                    INFRASTRUCTURE LAYER                           │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│  │ Uvicorn  │  │ File     │  │ .env     │  │ Docker       │    │
│  │ :8002    │  │ System   │  │ Config   │  │ Container    │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      FastAPI Application (main.py)                       │
│                                                                          │
│  app = FastAPI(title="Formación Evaluation Splitter")                    │
│  session_data = {}  ← In-memory session (single worker)                 │
│                                                                          │
│  Routes:                                                                 │
│  - /health, /, /api/parse, /api/set-columns                             │
│  - /api/generate-files, /api/download-zip, /api/download-file/{name}    │
│  - /api/map-contacts, /api/contacts/stored, /api/contacts/delete        │
│  - /api/template (GET/POST), /api/preview-email                         │
│  - /api/power-automate/status, /api/send                                │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                        Services                                    │  │
│  │                                                                    │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐      │  │
│  │  │ ExcelParser    │  │ ExcelGenerator │  │ ContactMapper  │      │  │
│  │  │                │  │                │  │                │      │  │
│  │  │ parse()        │  │ generate_      │  │ load_contacts()│      │  │
│  │  │ _find_tutor_   │  │ files()        │  │ map_contacts() │      │  │
│  │  │ column()       │  │ create_zip_    │  │ delete_stored_ │      │  │
│  │  │ _group_by_     │  │ archive()      │  │ contacts()     │      │  │
│  │  │ tutor()        │  │                │  │ persist to JSON│      │  │
│  │  │ _build_column_ │  │ Copies:        │  │                │      │  │
│  │  │ info()         │  │ - Headers 1-3  │  │ Matching:      │      │  │
│  │  │ _get_merged_   │  │ - Formatting   │  │ - Exact        │      │  │
│  │  │ ranges()       │  │ - Merged cells │  │ - Accent-free  │      │  │
│  │  └────────────────┘  │ - Col widths   │  │ - Token-based  │      │  │
│  │                       └────────────────┘  └────────────────┘      │  │
│  │  ┌────────────────┐                                                │  │
│  │  │ EmailSender    │                                                │  │
│  │  │                │  Variables:                                     │  │
│  │  │ compose_email()│  {{tutor_name}}, {{num_profesionales}},        │  │
│  │ send_email()   │  {{fecha}}, {{periodo}}, {{screenshot}}        │  │
│  │ send_batch()   │                                                │  │
│  │ check_status() │  Payload → Power Automate HTTP POST           │  │
│  │ preview_email()│  CID inline images + HTML wrapper              │  │
│  └────────────────┘  Timeout: 60s                                  │  │
│  │                                                                │  │
│  │  ┌────────────────┐                                            │  │
│  │  │ DataManager    │  NEW v2.0.0                                │  │
│  │  │                │                                            │  │
│  │  │ sync_data_on_  │  External data:                            │  │
│  │  │ startup()      │  /home/rootadmin/data/Control_formacion/   │  │
│  │  │ create_run_    │  ├── temp/ (per-run files)                 │  │
│  │  │ folder()       │  ├── basedata/ (synced templates)          │  │
│  │  │ add_history_   │  └── history.json (max 10 runs)            │  │
│  │  │ entry()        │                                            │  │
│  │  └────────────────┘                                            │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  Models (models/schemas.py)                                        │  │
│  │                                                                    │  │
│  │  Recipient, DataEntry (source_row), DataBlock, ParsedDocument     │  │
│  │  (tutor_column, sample_tutor), ColumnInfo (category),              │  │
│  │  Contact, ContactMapping, EmailTemplate, EmailComposition,         │  │
│  │  SendStatus, SendResult, ProcessingResult                          │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌────────────────┐                                                      │
│  │   config.py    │ ← Pydantic BaseSettings, port 8002, loads .env      │
│  └────────────────┘                                                      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Data Flow

```
           INPUT                    PROCESSING                   OUTPUT
  ┌────────────────────┐    ┌────────────────────┐    ┌────────────────────┐
  │                    │    │                    │    │                    │
  │  Excel File (.xlsx)│───▶│  ExcelParser       │───▶│  ParsedDocument   │
  │  - Multi-row header│    │  - Detect "Tutor"  │    │  - Blocks by Tutor│
  │    (Rows 1-3)      │    │    column in Row 3 │    │  - Column metadata│
  │  - ~70 columns     │    │  - Parse merged    │    │    with categories│
  │  - Grouped by Tutor│    │    cell categories │    │  - Header rows    │
  │                    │    │  - Group by Tutor  │    │    [1, 2, 3]      │
  └────────────────────┘    └────────────────────┘    └────────┬───────────┘
                                                               │
  ┌────────────────────┐    ┌────────────────────┐             │
  │  Contacts (.xlsx)  │    │                    │◀────────────┘
  │  A: Tutor Name     │───▶│  ContactMapper     │
  │  B: Email          │    │  - Fuzzy match by  │───▶ ContactMapping[]
  │  C: CC Email       │    │    Tutor name      │
  │                    │    │  - NFKD accent     │
  │  contacts_store    │◀──▶│    normalization   │
  │  (.json)           │    │  - Persist to JSON │
  └────────────────────┘    └────────────────────┘
                                                      ┌────────────────────┐
  ParsedDocument ────────────────────────────────────▶│  ExcelGenerator    │
  Selected Columns ──────────────────────────────────▶│  - Copy headers    │
  Original File Bytes ───────────────────────────────▶│    1-3 with format │
                                                       │  - Preserve styles │
                                                       │  - Adjust merged   │
                                                       │    cells for cols  │
                                                       └────────┬───────────┘
                                                                │
                                                    (filename, bytes)[]
                                                                │
  ContactMapping[] ───────────────────────────────────┐         │
  EmailTemplate ──────────────────────────────────────┤         │
  Generated Files ────────────────────────────────────┤◀────────┘
                                                       │
                                                       ▼
                                               ┌────────────────────┐
                                               │  EmailSender       │
                                               │  - Substitute vars │
                                               │  - Base64 attach   │
                                               │  - POST to PA      │
                                               └────────┬───────────┘
                                                        │
                                                        ▼
                                                 ProcessingResult
```

---

## 5. Storage Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Storage                               │
│                                                           │
│  ┌─── Ephemeral (In-Memory) ─────────────────────────┐  │
│  │                                                     │  │
│  │  session_data = {                                   │  │
│  │    "document":         ParsedDocument,              │  │
│  │    "file_content":     bytes,                       │  │
│  │    "mappings":         List[ContactMapping],        │  │
│  │    "generated_files":  List[Tuple[str, bytes]],     │  │
│  │    "split_mode":       "tutor",                     │  │
│  │    "selected_columns": List[str],                   │  │
│  │    "template":         EmailTemplate,               │  │
│  │  }                                                  │  │
│  │                                                     │  │
│  │  Lifecycle: Created on upload, cleared on new upload│  │
│  │  Scope: Single server process (--workers 1)         │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌─── Persistent (File System — Local App Data) ─────┐  │
│  │                                                     │  │
│  │  data/contacts_store.json                           │  │
│  │  data/column_presets.json                           │  │
│  │  data/email_templates.json                          │  │
│  │                                                     │  │
│  │  Lifecycle: Persists across restarts                 │  │
│  │  Auto-synced to external data directory              │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌─── Persistent (External Data Directory) ──────────┐  │
│  │                                                     │  │
│  │  /home/rootadmin/data/Control_formacion/            │  │
│  │  ├── temp/                                          │  │
│  │  │   └── run_YYYYMMDD_HHMMSS/                      │  │
│  │  │       ├── generated/  (Excel files)              │  │
│  │  │       └── screenshots/ (PNG files)               │  │
│  │  ├── basedata/                                      │  │
│  │  │   ├── contacts_store.json                        │  │
│  │  │   ├── column_presets.json                        │  │
│  │  │   └── email_templates.json                       │  │
│  │  └── history.json  (max 10 entries, auto-cleanup)   │  │
│  │                                                     │  │
│  │  Lifecycle: Survives app updates (git pull)          │  │
│  │  Sync: Bidirectional on startup, push on changes    │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌─── Configuration (File System) ───────────────────┐  │
│  │                                                     │  │
│  │  .env                          Environment vars     │  │
│  │  data/Contactos_Tutores.xlsx   Default contacts     │  │
│  │  templates/email_default.html  Email HTML template  │  │
│  │  static/images/                Email images         │  │
│  │                                                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## 6. Frontend Architecture (6-Step Wizard)

```
┌─────────────────────────────────────────────────────────────────┐
│  Formación Evaluation Splitter                                   │
├──────────────────────────────────────────────────────────────────┤
│  [1.Upload] → [2.Columns] → [3.Review] → [4.Contacts]          │
│            → [5.Email] → [6.Send]                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Step 1: Drag-drop / click file upload (.xlsx)                   │
│  Step 2: Column selection with category grouping + sample data   │
│  Step 3: Tutor group review (name, count, exclude toggle)        │
│  Step 4: Contact mapping table (upload or use stored)            │
│  Step 5: Rich text email editor (WYSIWYG)                        │
│          - Bold, italic, underline, font size, color             │
│          - Alignment, lists, tables                               │
│          - Image insert (URL or file upload)                      │
│          - Template variable insertion                            │
│  Step 6: Preview + Send (exclusions, test mode, results)         │
│                                                                   │
├──────────────────────────────────────────────────────────────────┤
│  Status: ● Power Automate    v2.0.0  [Historial]                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## 7. Deployment Architecture

```
┌──────────────────────────────────────────┐
│           Docker Container               │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │  Python 3.11-slim                │   │
│  │                                  │   │
│  │  Uvicorn --workers 1 --port 8002│   │
│  │       │                          │   │
│  │       ▼                          │   │
│  │  FastAPI App                     │   │
│  │  ├── static/                     │   │
│  │  ├── templates/                  │   │
│  │  └── data/ (volume mount)        │   │
│  │                                  │   │
│  └──────────────────────────────────┘   │
│                                          │
│  Volumes:                                │
│  - ./data:/app/data (contacts persist)   │
│  - /home/rootadmin/data/Control_formacion│
│    :/home/rootadmin/data/Control_formaci │
│    on (external persistent data)         │
│  - ./.env:/app/.env:ro                   │
│                                          │
│  Port: 8002:8002                         │
│  Restart: unless-stopped                 │
│                                          │
└──────────────────────────────────────────┘
```

---

## 8. Security Architecture

- No credentials in code — all secrets in `.env`
- Power Automate URL contains SAS token — treated as secret
- Contact deletion requires password authentication
- File upload validation: `.xlsx` only, 50MB max
- In-memory session data — no persistent user data beyond contacts
- Deploy behind reverse proxy (Nginx) for production HTTPS
- Single-user design — no authentication layer needed
