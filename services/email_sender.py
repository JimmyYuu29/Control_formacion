"""Email sender service via Power Automate HTTP trigger."""

import base64
import html as html_module
import logging
from datetime import date, datetime
from typing import List, Optional, Tuple

import requests

from config import settings
from models.schemas import (
    ContactMapping,
    DataBlock,
    EmailTemplate,
    EmailComposition,
    SendResult,
    SendStatus,
    ProcessingResult,
    Recipient,
)

logger = logging.getLogger(__name__)

# Timeout in seconds for HTTP POST
REQUEST_TIMEOUT = 60


class EmailSender:
    """Service for sending emails via Power Automate HTTP trigger."""

    def __init__(self, power_automate_url: Optional[str] = None):
        """Initialize with Power Automate webhook URL.

        Args:
            power_automate_url: Override URL (uses settings if None)
        """
        self._url = power_automate_url or settings.power_automate_url
        self._template = EmailTemplate()
        self._cc_emails: List[str] = list(settings.cc_email_list)

    def set_template(self, template: EmailTemplate) -> None:
        """Set the email template."""
        self._template = template

    def set_cc_emails(self, emails: List[str]) -> None:
        """Set CC email addresses."""
        self._cc_emails = [e.strip() for e in emails if e.strip()]

    def get_template(self) -> EmailTemplate:
        """Get current email template."""
        return self._template

    def compose_email(
        self,
        template: EmailTemplate,
        mapping: ContactMapping,
        attachment: Tuple[str, bytes],
        cc_emails: Optional[List[str]] = None,
        extra_vars: Optional[dict] = None,
    ) -> EmailComposition:
        """Compose email with variable substitution.

        Args:
            template: Email template to use
            mapping: Contact mapping with recipient and contact info
            attachment: (filename, content_bytes) tuple
            cc_emails: Additional CC emails
            extra_vars: Extra template variables

        Returns:
            Composed email ready for sending
        """
        # Build template variables
        variables = {
            "tutor_name": (
                mapping.contact.nombre_completo
                if mapping.contact
                else mapping.recipient.nombre
            ),
            "nombre": (
                mapping.contact.nombre_completo
                if mapping.contact
                else mapping.recipient.nombre
            ),
            "fecha": date.today().strftime("%d/%m/%Y"),
            "periodo": str(date.today().year),
        }

        if extra_vars:
            variables.update(extra_vars)

        # Substitute variables
        subject = self._substitute_variables(template.subject, variables)
        body = self._substitute_variables(template.body, variables)

        # Ensure body is HTML
        is_html = template.is_html
        if not is_html:
            body = self._plain_text_to_html(body)
            is_html = True

        # Build CC list
        cc_list = list(self._cc_emails)
        if cc_emails:
            cc_list.extend(cc_emails)
        if mapping.contact and mapping.contact.email_cc:
            cc_list.append(mapping.contact.email_cc)

        return EmailComposition(
            to=mapping.contact.email,
            cc=cc_list,
            subject=subject,
            body=body,
            is_html=is_html,
            attachment_filename=attachment[0],
            attachment_content=attachment[1],
        )

    def send_email(self, composition: EmailComposition) -> SendResult:
        """Send single email via Power Automate.

        Args:
            composition: Composed email to send

        Returns:
            SendResult with status
        """
        if not self._url:
            return SendResult(
                recipient=Recipient(codigo="unknown", nombre="unknown"),
                status=SendStatus.FAILED,
                email_sent_to=composition.to,
                message="Power Automate URL no configurada",
            )

        try:
            attachment_b64 = base64.b64encode(
                composition.attachment_content
            ).decode("utf-8")

            payload = {
                "to": composition.to,
                "cc": ";".join(composition.cc) if composition.cc else "",
                "subject": composition.subject,
                "body": composition.body,
                "isHtml": composition.is_html,
                "attachmentName": composition.attachment_filename,
                "attachmentContent": attachment_b64,
            }

            response = requests.post(
                self._url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code in (200, 202):
                return SendResult(
                    recipient=Recipient(codigo="", nombre=""),
                    status=SendStatus.SUCCESS,
                    email_sent_to=composition.to,
                    message="Email enviado via Power Automate",
                )
            else:
                error_detail = (
                    response.text[:200] if response.text
                    else f"HTTP {response.status_code}"
                )
                return SendResult(
                    recipient=Recipient(codigo="", nombre=""),
                    status=SendStatus.FAILED,
                    email_sent_to=composition.to,
                    message=f"Error Power Automate: {error_detail}",
                )

        except requests.exceptions.Timeout:
            return SendResult(
                recipient=Recipient(codigo="", nombre=""),
                status=SendStatus.FAILED,
                email_sent_to=composition.to,
                message="Timeout al enviar via Power Automate",
            )
        except Exception as e:
            logger.error("Fallo al enviar email via Power Automate")
            return SendResult(
                recipient=Recipient(codigo="", nombre=""),
                status=SendStatus.FAILED,
                email_sent_to=composition.to,
                message=str(e),
            )

    def send_batch(
        self,
        mappings: List[ContactMapping],
        blocks: List[DataBlock],
        generated_files: List[Tuple[str, bytes]],
        template: Optional[EmailTemplate] = None,
        cc_emails: Optional[List[str]] = None,
        test_mode: bool = False,
    ) -> ProcessingResult:
        """Send batch of emails.

        Args:
            mappings: Contact mappings
            blocks: Data blocks (one per Tutor)
            generated_files: List of (filename, content) tuples
            template: Email template (uses default if None)
            cc_emails: Additional CC emails
            test_mode: If True, skip actual sending

        Returns:
            ProcessingResult with all results
        """
        tpl = template or self._template
        result = ProcessingResult(
            total=len(mappings),
            generated_files=[f[0] for f in generated_files],
        )

        # Build file lookup by Tutor name
        file_lookup: Dict[str, Tuple[str, bytes]] = {}
        for block in blocks:
            tutor_safe = block.recipient.nombre.replace(" ", "_")
            for fname, content in generated_files:
                if tutor_safe in fname or block.recipient.nombre in fname:
                    file_lookup[block.recipient.nombre] = (fname, content)
                    break

        for mapping in mappings:
            nombre = mapping.recipient.nombre

            # Handle excluded
            if mapping.excluded or mapping.recipient.excluded:
                result.excluded += 1
                result.results.append(SendResult(
                    recipient=mapping.recipient,
                    status=SendStatus.EXCLUDED,
                    message="Excluido por el usuario",
                ))
                continue

            # Handle no email
            if not mapping.email_found or not mapping.contact:
                result.sent_failed += 1
                result.results.append(SendResult(
                    recipient=mapping.recipient,
                    status=SendStatus.FAILED,
                    message="No se encontró dirección de email",
                ))
                continue

            # Get file for this tutor
            file_data = file_lookup.get(nombre)
            if not file_data:
                result.sent_failed += 1
                result.results.append(SendResult(
                    recipient=mapping.recipient,
                    status=SendStatus.FAILED,
                    message="No se generó archivo para este tutor",
                ))
                continue

            # Find block for extra variables
            block = next(
                (b for b in blocks if b.recipient.nombre == nombre), None
            )
            extra_vars = {}
            if block:
                extra_vars["num_profesionales"] = str(len(block.entries))

            # Compose
            composition = self.compose_email(
                template=tpl,
                mapping=mapping,
                attachment=file_data,
                cc_emails=cc_emails,
                extra_vars=extra_vars,
            )

            if test_mode:
                result.sent_success += 1
                result.results.append(SendResult(
                    recipient=mapping.recipient,
                    status=SendStatus.SUCCESS,
                    email_sent_to=mapping.contact.email,
                    message="Modo prueba — no enviado realmente",
                ))
            else:
                send_result = self.send_email(composition)
                send_result.recipient = mapping.recipient
                send_result.email_sent_to = mapping.contact.email

                if send_result.status == SendStatus.SUCCESS:
                    result.sent_success += 1
                else:
                    result.sent_failed += 1

                result.results.append(send_result)

        return result

    def check_status(self) -> dict:
        """Check Power Automate URL reachability.

        Returns:
            Dict with 'available' (bool) and 'message' (str)
        """
        if not self._url:
            return {
                "available": False,
                "message": "Power Automate URL no configurada (POWER_AUTOMATE_URL)",
            }

        try:
            response = requests.post(
                self._url,
                json={"ping": True},
                timeout=15,
            )
            if response.status_code in (200, 202):
                return {"available": True, "message": "Power Automate conectado"}
            elif response.status_code < 500:
                return {"available": True, "message": "Power Automate conectado (URL accesible)"}
            else:
                return {
                    "available": False,
                    "message": f"Error Power Automate: HTTP {response.status_code}",
                }
        except requests.exceptions.ConnectionError:
            return {
                "available": False,
                "message": "No se puede conectar a Power Automate URL",
            }
        except requests.exceptions.Timeout:
            return {
                "available": False,
                "message": "Timeout al conectar con Power Automate",
            }
        except Exception as e:
            return {
                "available": False,
                "message": f"Error verificando Power Automate: {str(e)}",
            }

    def preview_email(
        self,
        mapping: ContactMapping,
        block: DataBlock,
    ) -> dict:
        """Preview email content without attachment.

        Returns:
            Dict with to, cc, subject, body
        """
        variables = {
            "tutor_name": (
                mapping.contact.nombre_completo
                if mapping.contact
                else mapping.recipient.nombre
            ),
            "nombre": (
                mapping.contact.nombre_completo
                if mapping.contact
                else mapping.recipient.nombre
            ),
            "num_profesionales": str(len(block.entries)),
            "fecha": date.today().strftime("%d/%m/%Y"),
            "periodo": str(date.today().year),
        }

        subject = self._substitute_variables(self._template.subject, variables)
        body = self._substitute_variables(self._template.body, variables)

        cc_list = list(self._cc_emails)
        if mapping.contact and mapping.contact.email_cc:
            cc_list.append(mapping.contact.email_cc)

        return {
            "to": mapping.contact.email if mapping.contact else "Sin email",
            "cc": cc_list,
            "subject": subject,
            "body": body,
        }

    @staticmethod
    def _plain_text_to_html(text: str) -> str:
        """Convert plain text to HTML preserving line breaks."""
        escaped = html_module.escape(text)
        return escaped.replace("\n", "<br>\n")

    @staticmethod
    def _substitute_variables(text: str, variables: dict) -> str:
        """Substitute {{variable}} placeholders in text."""
        result = text
        for var_name, value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            result = result.replace(placeholder, str(value))
        return result
