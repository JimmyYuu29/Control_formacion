"""FastAPI application entry point for Formación Evaluation Splitter."""

import base64
import json
import logging
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import settings
from models.schemas import (
    EmailTemplate,
    SendStatus,
)
from services.excel_parser import ExcelParser
from services.excel_generator import ExcelGenerator
from services.contact_mapper import ContactMapper
from services.email_sender import EmailSender

# ── Logging ──────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    description="Automatización de distribución de evaluaciones de formación",
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Session ──────────────────────────────────────────────────────────

session_data = {
    "document": None,
    "file_content": None,
    "mappings": None,
    "generated_files": None,
    "generated_screenshots": None,
    "split_mode": None,
    "selected_columns": None,
    "template": None,
}


# ── Request / Response Models ────────────────────────────────────────

class ColumnSelectionRequest(BaseModel):
    columns: List[str]


class TemplateRequest(BaseModel):
    subject: str
    body: str
    is_html: bool = True


class SendRequest(BaseModel):
    excluded_codes: List[str] = []
    cc_emails: List[str] = []
    test_mode: bool = False


class DeleteContactsRequest(BaseModel):
    password: str


class PresetSaveRequest(BaseModel):
    name: str
    columns: List[str]


class EmailTemplateSaveRequest(BaseModel):
    name: str
    subject: str
    body: str
    is_html: bool = True


# ── JSON Persistence Helpers ─────────────────────────────────────────

def _load_json_store(path: str) -> dict:
    """Load a JSON file, returning empty dict if not found."""
    p = Path(path)
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_json_store(path: str, data: dict) -> None:
    """Save data to a JSON file, creating directories if needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Health ───────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }


# ── File Processing ─────────────────────────────────────────────────

@app.post("/api/parse")
async def parse_file(
    file: UploadFile = File(...),
    mode: str = Query(default="tutor"),
):
    """Upload and parse Excel file."""
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten archivos .xlsx",
        )

    try:
        content = await file.read()
        session_data["file_content"] = content
        session_data["split_mode"] = mode
        # Clear previous session
        session_data["mappings"] = None
        session_data["generated_files"] = None

        parser = ExcelParser(mode=mode)
        document = parser.parse(content, file.filename)
        session_data["document"] = document
        session_data["selected_columns"] = list(document.default_columns)

        # Build response
        groups = [
            {
                "code": block.recipient.codigo,
                "name": block.recipient.nombre,
                "total": float(block.total),
                "entries_count": len(block.entries),
            }
            for block in document.blocks
        ]

        all_columns = [
            {
                "letter": col.letter,
                "header": col.header,
                "category": col.category,
                "has_data": col.has_data,
            }
            for col in document.all_columns
        ]

        return {
            "filename": document.filename,
            "split_criteria": "tutor",
            "total_general": float(document.total_general),
            "groups": groups,
            "groups_count": len(groups),
            "all_columns": all_columns,
            "default_columns": document.default_columns,
            "tutor_column": document.tutor_column,
            "sample_tutor": document.sample_tutor,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error al analizar el archivo")
        raise HTTPException(
            status_code=400,
            detail=f"Error al analizar el archivo: {str(e)}",
        )


@app.post("/api/set-columns")
async def set_columns(request: ColumnSelectionRequest):
    """Select columns for output files."""
    session_data["selected_columns"] = request.columns
    session_data["generated_files"] = None  # Invalidate previous generation
    session_data["generated_screenshots"] = None
    return {"status": "ok", "selected": request.columns}


# ── Column Presets ───────────────────────────────────────────────────

@app.get("/api/presets")
async def get_presets():
    """List all saved column presets."""
    store = _load_json_store(settings.presets_store_path)
    return {"presets": store}


@app.post("/api/presets")
async def save_preset(request: PresetSaveRequest):
    """Save a column preset."""
    name = request.name.strip()
    if not name or len(name) > 100:
        raise HTTPException(status_code=400, detail="Nombre inválido")
    if not request.columns:
        raise HTTPException(status_code=400, detail="Debe incluir al menos una columna")

    store = _load_json_store(settings.presets_store_path)
    store[name] = {
        "name": name,
        "columns": request.columns,
        "created_at": datetime.now().isoformat(),
    }
    _save_json_store(settings.presets_store_path, store)
    return {"status": "ok", "message": f"Preset '{name}' guardado"}


@app.delete("/api/presets/{name}")
async def delete_preset(name: str):
    """Delete a column preset."""
    store = _load_json_store(settings.presets_store_path)
    if name not in store:
        raise HTTPException(status_code=404, detail=f"Preset '{name}' no encontrado")
    del store[name]
    _save_json_store(settings.presets_store_path, store)
    return {"status": "ok", "message": f"Preset '{name}' eliminado"}


@app.post("/api/generate-files")
async def generate_files():
    """Generate individual Excel files per Tutor."""
    document = session_data.get("document")
    file_content = session_data.get("file_content")

    if not document:
        raise HTTPException(
            status_code=409,
            detail="Primero debe cargar un archivo Excel",
        )

    try:
        selected_columns = session_data.get("selected_columns") or document.default_columns

        generator = ExcelGenerator()
        files = generator.generate_files(
            document=document,
            source_content=file_content,
            selected_columns=selected_columns,
            original_filename=document.filename,
        )
        session_data["generated_files"] = files

        # Generate PNG screenshots
        screenshots = generator.generate_screenshots(files)
        session_data["generated_screenshots"] = screenshots

        return {
            "status": "ok",
            "files_generated": len(files),
            "filenames": [f[0] for f in files],
            "screenshots": [s[0] for s in screenshots],
        }

    except Exception as e:
        logger.exception("Error al generar archivos")
        raise HTTPException(
            status_code=400,
            detail=f"Error al generar archivos: {str(e)}",
        )


@app.get("/api/download-zip")
async def download_zip():
    """Download all generated files as ZIP."""
    files = session_data.get("generated_files")
    if not files:
        raise HTTPException(
            status_code=409,
            detail="No hay archivos generados. Genere los archivos primero.",
        )

    generator = ExcelGenerator()
    zip_content = generator.create_zip_archive(files)

    return StreamingResponse(
        BytesIO(zip_content),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=evaluaciones.zip"},
    )


@app.get("/api/download-file/{filename}")
async def download_file(filename: str):
    """Download a specific generated file."""
    files = session_data.get("generated_files")
    if not files:
        raise HTTPException(status_code=409, detail="No hay archivos generados.")

    file_data = next((f for f in files if f[0] == filename), None)
    if not file_data:
        raise HTTPException(
            status_code=404,
            detail=f"Archivo '{filename}' no encontrado",
        )

    return StreamingResponse(
        BytesIO(file_data[1]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ── Screenshot Downloads ─────────────────────────────────────────────

@app.get("/api/screenshots/{filename}")
async def download_screenshot(filename: str):
    """Download a specific PNG screenshot."""
    screenshots = session_data.get("generated_screenshots")
    if not screenshots:
        raise HTTPException(status_code=409, detail="No hay capturas generadas.")

    safe_name = Path(filename).name
    file_data = next((s for s in screenshots if s[0] == safe_name), None)
    if not file_data:
        raise HTTPException(
            status_code=404,
            detail=f"Captura '{filename}' no encontrada",
        )

    return StreamingResponse(
        BytesIO(file_data[1]),
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename={safe_name}"},
    )


@app.get("/api/download-screenshots-zip")
async def download_screenshots_zip():
    """Download all screenshots as ZIP."""
    screenshots = session_data.get("generated_screenshots")
    if not screenshots:
        raise HTTPException(
            status_code=409,
            detail="No hay capturas generadas.",
        )

    generator = ExcelGenerator()
    zip_content = generator.create_zip_archive(screenshots, "capturas.zip")

    return StreamingResponse(
        BytesIO(zip_content),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=capturas.zip"},
    )


# ── Contact Management ──────────────────────────────────────────────

@app.post("/api/map-contacts")
async def map_contacts(contacts_file: Optional[UploadFile] = None):
    """Load and map contacts to Tutors."""
    document = session_data.get("document")

    try:
        mapper = ContactMapper()

        if contacts_file:
            content = await contacts_file.read()
            mapper.load_contacts(file_content=content)
        else:
            mapper.load_contacts()

        # If no document parsed, return success with empty mapping
        if not document:
            return {
                "mappings": [],
                "unmapped_count": 0,
                "total_count": 0,
            }

        recipients = [block.recipient for block in document.blocks]
        mappings = mapper.map_contacts(recipients)
        session_data["mappings"] = mappings

        mapping_list = [
            {
                "code": m.recipient.codigo,
                "name": m.recipient.nombre,
                "email": m.contact.email if m.contact else None,
                "email_cc": m.contact.email_cc if m.contact else None,
                "email_found": m.email_found,
                "excluded": m.excluded,
                "entries_count": len(
                    next(
                        (b.entries for b in document.blocks
                         if b.recipient.nombre == m.recipient.nombre),
                        [],
                    )
                ),
            }
            for m in mappings
        ]

        unmapped = len([m for m in mappings if not m.email_found])

        return {
            "mappings": mapping_list,
            "unmapped_count": unmapped,
            "total_count": len(mappings),
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Error al mapear contactos")
        raise HTTPException(
            status_code=400,
            detail=f"Error al mapear contactos: {str(e)}",
        )


@app.get("/api/contacts/stored")
async def get_stored_contacts():
    """Get info about stored contacts."""
    mapper = ContactMapper()
    return mapper.get_stored_contacts_info()


@app.post("/api/contacts/delete")
async def delete_stored_contacts(request: DeleteContactsRequest):
    """Delete stored contacts with password verification."""
    mapper = ContactMapper()
    if mapper.delete_stored_contacts(request.password):
        return {"status": "ok", "message": "Contactos eliminados"}
    raise HTTPException(status_code=403, detail="Contraseña incorrecta")


# ── Email Template ───────────────────────────────────────────────────

@app.get("/api/template")
async def get_template():
    """Get current email template."""
    template = session_data.get("template") or EmailTemplate()
    return {
        "subject": template.subject,
        "body": template.body,
        "is_html": template.is_html,
    }


@app.post("/api/template")
async def update_template(request: TemplateRequest):
    """Update email template."""
    session_data["template"] = EmailTemplate(
        subject=request.subject,
        body=request.body,
        is_html=request.is_html,
    )
    return {"status": "ok", "message": "Plantilla actualizada"}


# ── Persistent Email Templates ───────────────────────────────────────

@app.get("/api/email-templates")
async def list_email_templates():
    """List all saved email templates."""
    store = _load_json_store(settings.templates_store_path)
    return {"templates": store}


@app.post("/api/email-templates")
async def save_email_template(request: EmailTemplateSaveRequest):
    """Save an email template persistently."""
    name = request.name.strip()
    if not name or len(name) > 100:
        raise HTTPException(status_code=400, detail="Nombre inválido")

    store = _load_json_store(settings.templates_store_path)
    store[name] = {
        "name": name,
        "subject": request.subject,
        "body": request.body,
        "is_html": request.is_html,
        "created_at": datetime.now().isoformat(),
    }
    _save_json_store(settings.templates_store_path, store)
    return {"status": "ok", "message": f"Plantilla '{name}' guardada"}


@app.get("/api/email-templates/{name}")
async def load_email_template(name: str):
    """Load a specific email template."""
    store = _load_json_store(settings.templates_store_path)
    if name not in store:
        raise HTTPException(status_code=404, detail=f"Plantilla '{name}' no encontrada")
    return store[name]


@app.delete("/api/email-templates/{name}")
async def delete_email_template(name: str):
    """Delete a saved email template."""
    store = _load_json_store(settings.templates_store_path)
    if name not in store:
        raise HTTPException(status_code=404, detail=f"Plantilla '{name}' no encontrada")
    del store[name]
    _save_json_store(settings.templates_store_path, store)
    return {"status": "ok", "message": f"Plantilla '{name}' eliminada"}


@app.get("/api/preview-email")
async def preview_email(code: str = Query(...)):
    """Preview email for a specific Tutor."""
    document = session_data.get("document")
    mappings = session_data.get("mappings")

    if not document or not mappings:
        raise HTTPException(
            status_code=409,
            detail="Primero debe cargar un archivo y mapear contactos.",
        )

    mapping = next((m for m in mappings if m.recipient.codigo == code), None)
    block = next(
        (b for b in document.blocks if b.recipient.codigo == code), None
    )

    if not mapping or not block:
        raise HTTPException(
            status_code=404,
            detail=f"Tutor '{code}' no encontrado",
        )

    sender = EmailSender()
    if session_data.get("template"):
        sender.set_template(session_data["template"])

    screenshots = session_data.get("generated_screenshots")
    return sender.preview_email(mapping, block, screenshots=screenshots)


# ── Power Automate ───────────────────────────────────────────────────

@app.get("/api/power-automate/status")
def power_automate_status():
    """Check Power Automate connectivity."""
    sender = EmailSender()
    return sender.check_status()


# ── Email Sending ────────────────────────────────────────────────────

@app.post("/api/send")
def send_emails(request: SendRequest):
    """Send emails to all mapped Tutors via Power Automate."""
    document = session_data.get("document")
    mappings = session_data.get("mappings")
    files = session_data.get("generated_files")

    if not document or not mappings:
        raise HTTPException(
            status_code=409,
            detail="Primero debe cargar un archivo y mapear contactos.",
        )

    if not files:
        raise HTTPException(
            status_code=409,
            detail="No hay archivos generados. Genere los archivos primero.",
        )

    # Check PA connectivity (skip in test mode)
    if not request.test_mode:
        sender = EmailSender()
        pa_status = sender.check_status()
        if not pa_status["available"]:
            raise HTTPException(
                status_code=502,
                detail=f"Power Automate no disponible: {pa_status['message']}",
            )

    try:
        # Apply exclusions
        for mapping in mappings:
            mapping.excluded = mapping.recipient.codigo in request.excluded_codes
            mapping.recipient.excluded = mapping.excluded

        sender = EmailSender()
        template = session_data.get("template") or EmailTemplate()
        sender.set_template(template)

        result = sender.send_batch(
            mappings=mappings,
            blocks=document.blocks,
            generated_files=files,
            template=template,
            cc_emails=request.cc_emails if request.cc_emails else None,
            test_mode=request.test_mode,
            screenshots=session_data.get("generated_screenshots"),
        )

        return {
            "status": "completed",
            "total": result.total,
            "success": result.sent_success,
            "failed": result.sent_failed,
            "excluded": result.excluded,
            "results": [
                {
                    "code": r.recipient.codigo,
                    "name": r.recipient.nombre,
                    "status": r.status.value,
                    "email": r.email_sent_to,
                    "message": r.message,
                }
                for r in result.results
            ],
        }

    except Exception as e:
        logger.exception("Error al enviar emails")
        raise HTTPException(
            status_code=500,
            detail=f"Error al enviar emails: {str(e)}",
        )


# ── Frontend ─────────────────────────────────────────────────────────

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/")
async def serve_frontend():
    """Serve the web frontend."""
    return FileResponse(STATIC_DIR / "index.html")


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Entrypoint ───────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
