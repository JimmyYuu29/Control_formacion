# Design Standards & Conventions: Formación Evaluation Splitter

> **Version:** 1.0.0
> **App Name:** Formación Evaluation Splitter
> **Last Updated:** 2026-03-05

---

## 1. Code Conventions

### 1.1 Python Style

| Rule | Standard |
|------|----------|
| Style Guide | PEP 8 |
| Line Length | 100 characters max |
| Quotes | Double quotes for strings (`"hello"`) |
| Imports | Standard lib → Third-party → Local (separated by blank lines) |
| Type Hints | Required for all function signatures |
| Docstrings | Required for classes and public functions |

### 1.2 Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Files | snake_case | `excel_parser.py` |
| Classes | PascalCase | `ExcelParser` |
| Functions | snake_case | `parse_excel()` |
| Variables | snake_case | `file_content` |
| Constants | UPPER_SNAKE_CASE | `MAX_FILE_SIZE` |
| Private | Leading underscore | `_find_tutor_column()` |
| API Routes | kebab-case | `/api/map-contacts` |
| Env Variables | UPPER_SNAKE_CASE | `POWER_AUTOMATE_URL` |
| CSS Classes | kebab-case | `.upload-zone` |
| JS Functions | camelCase | `parseResponse()` |

---

## 2. Project Structure

```
Control_formacion/
├── main.py              # FastAPI application (single entry point)
├── config.py            # Settings class with env var loading
├── requirements.txt     # Pinned dependency versions
├── .env.example         # Template for .env file
├── Dockerfile           # Docker build configuration
├── docker-compose.yml   # Docker Compose for deployment
├── models/
│   ├── __init__.py
│   └── schemas.py       # All Pydantic models
├── services/
│   ├── __init__.py
│   ├── excel_parser.py  # Multi-row header parsing & Tutor grouping
│   ├── excel_generator.py  # File generation with formatting
│   ├── contact_mapper.py   # Tutor→Email fuzzy matching
│   └── email_sender.py     # Email via Power Automate
├── static/
│   ├── index.html       # Frontend SPA (6-step wizard)
│   └── images/          # Email template images
├── templates/
│   └── email_default.html  # Default email template
├── data/
│   └── .gitkeep
└── tests/
    ├── test_parser.py
    ├── test_generator.py
    ├── test_mapper.py
    └── test_sender.py
```

### Forbidden Patterns

- NO `app.py` — always use `main.py`
- NO external frontend frameworks — vanilla HTML/JS only
- NO databases — file-based storage only
- NO external CDN — all resources inline or local
- NO frontend build steps — no npm/webpack

---

## 3. API Design

### Route Naming

```
GET  /health                    # Health check
POST /api/parse                 # Parse uploaded file
POST /api/set-columns           # Select columns
POST /api/generate-files        # Generate files
GET  /api/download-zip          # Download all as ZIP
GET  /api/download-file/{name}  # Download single file
POST /api/map-contacts          # Map Tutor contacts
GET  /api/contacts/stored       # Get stored contacts
POST /api/contacts/delete       # Delete contacts
GET  /api/template              # Get email template
POST /api/template              # Update email template
GET  /api/preview-email         # Preview email
GET  /api/power-automate/status # Check PA status
POST /api/send                  # Send emails
```

### Error Messages

- Always in Spanish (target user language)
- Be specific: `"Solo se permiten archivos .xlsx"`
- Include guidance: `"No hay contactos mapeados. Suba un archivo de contactos primero."`

---

## 4. Frontend Standards

| Rule | Requirement |
|------|-------------|
| Language | Spanish (es) |
| Loading states | Spinner/overlay for async operations |
| Error display | In-page toast notifications (no `alert()`) |
| File upload | Drag-and-drop + click fallback |
| Confirmation | Show confirmation before sending emails |
| Results | Per-Tutor status after sending |
| Responsive | 1024px+ width screens |
| No external CDN | All resources local or inline |

---

## 5. Data Handling

### Excel Processing

| Rule | Standard |
|------|----------|
| Library | openpyxl only |
| Read mode | `load_workbook(data_only=True)` for values |
| Formatting | Preserve all original styles (colors, fonts, borders, fills) |
| Headers | 3-row header structure (Rows 1-3) with merged cells |
| Date format | DD/MM/YYYY for Spanish locale |
| Currency format | European: 1.234,56 |
| File naming | `{Tutor_Name}_{Original_Filename}.xlsx` |

### Contact Persistence

- JSON format at `data/contacts_store.json`
- Keyed by Tutor name
- Password-protected deletion (default: `Formacion2026`)

---

## 6. Configuration

### Port Assignment

| App | Port |
|-----|------|
| deuda_power | 8001 |
| **Control_formacion** | **8002** |

### Required .env Variables

```env
POWER_AUTOMATE_URL=          # (Mandatory) Power Automate webhook
HOST=0.0.0.0                 # Server host
PORT=8002                    # Server port
DEBUG=false                  # Debug mode
```

---

## 7. Testing Standards

| Requirement | Standard |
|-------------|----------|
| Framework | pytest |
| Current count | 33 tests (8 parser + 6 generator + 8 mapper + 11 sender) |
| Mocking | `unittest.mock` for Power Automate HTTP calls |
| Test data | In-memory workbooks created with openpyxl |

---

## 8. Logging

### What to Log

| Level | What |
|-------|------|
| INFO | File uploaded, parse complete, emails sent |
| WARNING | Unmapped contacts, partial failures |
| ERROR | Parse failures, send failures, connection errors |
| DEBUG | Detailed processing (only when DEBUG=true) |

### What NOT to Log

- Email addresses or body content
- Power Automate URLs (contains SAS tokens)
- Attachment data
- Any PII

---

## 9. Version Control

### .gitignore

```gitignore
.env
__pycache__/
*.pyc
venv/
.venv/
data/contacts_store.json
build/
dist/
.vscode/
.idea/
*.log
.DS_Store
Thumbs.db
```
