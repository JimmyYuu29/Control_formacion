"""Pydantic models for data validation and serialization."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, EmailStr


# ─── Recipient / Tutor ───────────────────────────────────────────────

class Recipient(BaseModel):
    """Represents a Tutor (group entity for splitting)."""

    codigo: str = Field(..., description="Identificador del tutor (nombre como clave)")
    nombre: str = Field(..., description="Nombre completo del tutor")
    excluded: bool = Field(default=False, description="Excluido del envío")


# ─── Data Entry ──────────────────────────────────────────────────────

class DataEntry(BaseModel):
    """Single row of data (one professional's evaluation)."""

    raw_cells: Dict[str, Any] = Field(default_factory=dict)
    source_row: int = Field(default=0, description="Fila original en el archivo Excel")


# ─── Data Block ──────────────────────────────────────────────────────

class DataBlock(BaseModel):
    """A block of entries belonging to one Tutor."""

    recipient: Recipient
    entries: List[DataEntry] = Field(default_factory=list)
    total: Decimal = Field(default=Decimal("0"))
    start_row: int = 0
    end_row: int = 0


# ─── Column Info ─────────────────────────────────────────────────────

class ColumnInfo(BaseModel):
    """Metadata about an Excel column with category/subcategory hierarchy."""

    letter: str
    header: Optional[str] = None
    category: Optional[str] = None
    has_data: bool = True


# ─── Parsed Document ─────────────────────────────────────────────────

class ParsedDocument(BaseModel):
    """Fully parsed Excel document."""

    filename: str
    blocks: List[DataBlock] = Field(default_factory=list)
    total_general: Decimal = Field(default=Decimal("0"))
    header_rows: List[int] = Field(default_factory=list)
    all_columns: List[ColumnInfo] = Field(default_factory=list)
    default_columns: List[str] = Field(default_factory=list)
    tutor_column: Optional[str] = Field(None, description="Letra de la columna Tutor detectada")
    sample_tutor: Optional[str] = Field(None, description="Nombre del primer tutor (para preview)")


# ─── Contact ─────────────────────────────────────────────────────────

class Contact(BaseModel):
    """Contact information for a Tutor."""

    codigo: str = Field(..., description="Nombre del tutor (clave de mapeo)")
    nombre: str = Field(..., description="Nombre del tutor")
    apellido: Optional[str] = Field(None)
    email: EmailStr = Field(..., description="Email del tutor")
    email_cc: Optional[EmailStr] = Field(None, description="Email CC")

    @property
    def nombre_completo(self) -> str:
        """Nombre completo combinando nombre y apellido."""
        if self.apellido:
            return f"{self.nombre} {self.apellido}"
        return self.nombre


# ─── Contact Mapping ─────────────────────────────────────────────────

class ContactMapping(BaseModel):
    """Maps a Tutor to a Contact."""

    recipient: Recipient
    contact: Optional[Contact] = None
    email_found: bool = False
    excluded: bool = False


# ─── Email Template ──────────────────────────────────────────────────

class EmailTemplate(BaseModel):
    """Email template with variable placeholders."""

    subject: str = Field(
        default="Evaluación Formación — {{tutor_name}}",
        description="Asunto del email"
    )
    body: str = Field(
        default=(
            "<p>Estimado/a {{tutor_name}},</p>"
            "<p>Adjunto encontrará el resumen de calificaciones de los profesionales "
            "a su cargo correspondiente al periodo de evaluación actual.</p>"
            "<p>Por favor, revise la información y no dude en contactarnos "
            "si tiene alguna consulta.</p>"
            "<p>Saludos cordiales,</p>"
            "<p>Departamento de Calidad</p>"
        ),
        description="Cuerpo del email con placeholders"
    )
    is_html: bool = Field(default=True)


# ─── Email Composition ───────────────────────────────────────────────

class EmailComposition(BaseModel):
    """Composed email ready for sending."""

    to: EmailStr
    cc: List[str] = Field(default_factory=list)
    subject: str
    body: str
    is_html: bool = True
    attachment_filename: str
    attachment_content: bytes = Field(exclude=True)


# ─── Send Status ─────────────────────────────────────────────────────

class SendStatus(str, Enum):
    """Status of an email send operation."""

    PENDING = "pending"
    SENDING = "sending"
    SUCCESS = "success"
    FAILED = "failed"
    EXCLUDED = "excluded"


# ─── Send Result ─────────────────────────────────────────────────────

class SendResult(BaseModel):
    """Result of sending one email."""

    recipient: Recipient
    status: SendStatus
    message: Optional[str] = None
    email_sent_to: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ─── Processing Result ───────────────────────────────────────────────

class ProcessingResult(BaseModel):
    """Overall processing result."""

    total: int = 0
    sent_success: int = 0
    sent_failed: int = 0
    excluded: int = 0
    results: List[SendResult] = Field(default_factory=list)
    generated_files: List[str] = Field(default_factory=list)
