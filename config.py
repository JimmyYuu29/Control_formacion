"""Application configuration settings."""

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
    app_version: str = "1.0.0"

    @property
    def cc_email_list(self) -> List[str]:
        """Parse CC emails from comma-separated string."""
        if not self.default_cc_emails:
            return []
        return [e.strip() for e in self.default_cc_emails.split(",") if e.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
