"""Application configuration settings."""

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Power Automate
    power_automate_url: str = ""

    # SharePoint (optional)
    sharepoint_flow_url: str = ""
    sharepoint_site_name: str = ""
    sharepoint_folder_path: str = ""

    # ── External persistent data root ────────────────────────────────
    data_root_path: str = "/home/rootadmin/data/Control_formacion"
    max_history: int = 10

    # Contacts
    contacts_file_path: str = "data/Contactos_Tutores.xlsx"
    contacts_store_path: str = "data/contacts_store.json"
    contacts_delete_password: str = "Formacion2026"

    # Presets & Templates persistence
    presets_store_path: str = "data/column_presets.json"
    templates_store_path: str = "data/email_templates.json"

    # Email
    default_cc_emails: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8002
    debug: bool = False

    # App Identity
    app_name: str = "Formación Evaluation Splitter"
    app_version: str = "2.0.0"

    @property
    def cc_email_list(self) -> List[str]:
        """Parse CC emails from comma-separated string."""
        if not self.default_cc_emails:
            return []
        return [e.strip() for e in self.default_cc_emails.split(",") if e.strip()]

    @property
    def data_root(self) -> Path:
        return Path(self.data_root_path)

    @property
    def temp_path(self) -> Path:
        return self.data_root / "temp"

    @property
    def basedata_path(self) -> Path:
        return self.data_root / "basedata"

    @property
    def history_file(self) -> Path:
        return self.data_root / "history.json"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
