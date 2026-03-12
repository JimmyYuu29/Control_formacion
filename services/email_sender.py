"""Email sender service via Power Automate HTTP trigger.

Ensures full HTML fidelity: inline styles, CID-based image embedding
for screenshots, and proper email-compatible HTML wrapping.
"""

import base64
import html as html_module
import logging
import re
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

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

REQUEST_TIMEOUT = 60

# Full HTML email wrapper — uses inline styles only for maximum email client compatibility.
# Clean layout without card/border effects to avoid visible side borders in email clients.
EMAIL_HTML_WRAPPER = """\
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{subject}</title>
</head>
<body style="margin:0;padding:0;background-color:#ffffff;font-family:Calibri,Arial,Helvetica,sans-serif;line-height:1.6;color:#333333;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#ffffff;">
<tr><td style="padding:24px 32px;">
{body}
</td></tr>
</table>
</body>
</html>"""


class EmailSender:
    """Service for sending emails via Power Automate HTTP trigger."""

    def __init__(self, power_automate_url: Optional[str] = None):
        self._url = power_automate_url or settings.power_automate_url
        self._template = EmailTemplate()
        self._cc_emails: List[str] = list(settings.cc_email_list)

    def set_template(self, template: EmailTemplate) -> None:
        self._template = template

    def set_cc_emails(self, emails: List[str]) -> None:
        self._cc_emails = [e.strip() for e in emails if e.strip()]

    def get_template(self) -> EmailTemplate:
        return self._template

    # ── HTML Processing ──────────────────────────────────────────────

    @staticmethod
    def _wrap_html_email(body: str, subject: str = "") -> str:
        """Wrap editor HTML content in a full email-compatible HTML document."""
        return EMAIL_HTML_WRAPPER.format(subject=subject, body=body)

    @staticmethod
    def _extract_inline_images(html_body: str) -> Tuple[str, List[Dict]]:
        """Extract base64 data-URI images from HTML and convert to CID references.

        Returns:
            (modified_html, list_of_inline_attachments)
            Each attachment: {name, content_b64, content_type, cid}
        """
        attachments = []
        counter = 0

        def replace_data_uri(match):
            nonlocal counter
            content_type = match.group(1)
            b64_data = match.group(2)
            ext = "png" if "png" in content_type else "jpg"
            cid = f"inline_img_{counter}"
            name = f"image_{counter}.{ext}"
            counter += 1
            attachments.append({
                "Name": name,
                "ContentBytes": b64_data,
                "ContentType": content_type,
                "ContentId": cid,
                "IsInline": True,
            })
            return f'src="cid:{cid}"'

        pattern = r'src="data:(image/[^;]+);base64,([^"]+)"'
        modified = re.sub(pattern, replace_data_uri, html_body)
        return modified, attachments

    # ── Composition ──────────────────────────────────────────────────

    def compose_email(
        self,
        template: EmailTemplate,
        mapping: ContactMapping,
        attachment: Tuple[str, bytes],
        cc_emails: Optional[List[str]] = None,
        extra_vars: Optional[dict] = None,
        screenshot_data: Optional[Tuple[str, bytes]] = None,
    ) -> EmailComposition:
        """Compose email with variable substitution and CID image handling."""
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

        # Handle screenshot — embed as base64 data URI directly in HTML
        if screenshot_data:
            sname, scontent = screenshot_data
            b64 = base64.b64encode(scontent).decode("utf-8")
            variables["screenshot"] = (
                f'<img src="data:image/png;base64,{b64}" '
                f'style="max-width:100%;height:auto;display:block;margin:8px 0;" '
                f'alt="Evaluación {mapping.recipient.nombre}">'
            )
        else:
            variables["screenshot"] = ""

        subject = self._substitute_variables(template.subject, variables)

        # Strip the decorative screenshot placeholder wrapper so only {{screenshot}} remains
        raw_body = self._clean_screenshot_placeholder(template.body)
        body = self._substitute_variables(raw_body, variables)

        is_html = template.is_html
        if not is_html:
            body = self._plain_text_to_html(body)
            is_html = True

        # Editor-inserted images already use base64 data URIs — keep them as-is
        # (no CID conversion needed since data URIs work in Outlook)

        # Wrap in full email HTML
        body = self._wrap_html_email(body, subject)

        cc_list = list(self._cc_emails)
        if cc_emails:
            cc_list.extend(cc_emails)
        if mapping.contact and mapping.contact.email_cc:
            cc_list.append(mapping.contact.email_cc)

        composition = EmailComposition(
            to=mapping.contact.email,
            cc=cc_list,
            subject=subject,
            body=body,
            is_html=is_html,
            attachment_filename=attachment[0],
            attachment_content=attachment[1],
        )
        return composition

    def send_email(self, composition: EmailComposition) -> SendResult:
        """Send single email via Power Automate with full attachment support."""
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
                # Excel attachment only — images are embedded as data URIs in body
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
        screenshots: Optional[List[Tuple[str, bytes]]] = None,
    ) -> ProcessingResult:
        """Send batch of emails with CID-embedded screenshots."""
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

            if mapping.excluded or mapping.recipient.excluded:
                result.excluded += 1
                result.results.append(SendResult(
                    recipient=mapping.recipient,
                    status=SendStatus.EXCLUDED,
                    message="Excluido por el usuario",
                ))
                continue

            if not mapping.email_found or not mapping.contact:
                result.sent_failed += 1
                result.results.append(SendResult(
                    recipient=mapping.recipient,
                    status=SendStatus.FAILED,
                    message="No se encontró dirección de email",
                ))
                continue

            file_data = file_lookup.get(nombre)
            if not file_data:
                result.sent_failed += 1
                result.results.append(SendResult(
                    recipient=mapping.recipient,
                    status=SendStatus.FAILED,
                    message="No se generó archivo para este tutor",
                ))
                continue

            block = next(
                (b for b in blocks if b.recipient.nombre == nombre), None
            )
            extra_vars = {}
            if block:
                extra_vars["num_profesionales"] = str(len(block.entries))

            # Find screenshot for this tutor
            screenshot_data = None
            if screenshots:
                tutor_safe = nombre.replace(" ", "_")
                for sname, scontent in screenshots:
                    if tutor_safe in sname:
                        screenshot_data = (sname, scontent)
                        break

            composition = self.compose_email(
                template=tpl,
                mapping=mapping,
                attachment=file_data,
                cc_emails=cc_emails,
                extra_vars=extra_vars,
                screenshot_data=screenshot_data,
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
        if not self._url:
            return {
                "available": False,
                "message": "Power Automate URL no configurada (POWER_AUTOMATE_URL)",
            }
        try:
            response = requests.post(
                self._url, json={"ping": True}, timeout=15,
            )
            if response.status_code in (200, 202):
                return {"available": True, "message": "Power Automate conectado"}
            elif response.status_code < 500:
                return {"available": True, "message": "Power Automate conectado (URL accesible)"}
            else:
                return {"available": False, "message": f"Error Power Automate: HTTP {response.status_code}"}
        except requests.exceptions.ConnectionError:
            return {"available": False, "message": "No se puede conectar a Power Automate URL"}
        except requests.exceptions.Timeout:
            return {"available": False, "message": "Timeout al conectar con Power Automate"}
        except Exception as e:
            return {"available": False, "message": f"Error verificando Power Automate: {str(e)}"}

    def preview_email(
        self,
        mapping: ContactMapping,
        block: DataBlock,
        screenshots: Optional[List[Tuple[str, bytes]]] = None,
    ) -> dict:
        """Preview email content — uses data-URI for browser display."""
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

        if screenshots:
            nombre = mapping.recipient.nombre
            tutor_safe = nombre.replace(" ", "_")
            for sname, scontent in screenshots:
                if tutor_safe in sname:
                    b64 = base64.b64encode(scontent).decode("utf-8")
                    variables["screenshot"] = (
                        '<img src="data:image/png;base64,' + b64
                        + '" style="max-width:100%;height:auto;display:block;margin:8px 0;">'
                    )
                    break
        if "screenshot" not in variables:
            variables["screenshot"] = ""

        subject = self._substitute_variables(self._template.subject, variables)
        raw_body = self._clean_screenshot_placeholder(self._template.body)
        body = self._substitute_variables(raw_body, variables)

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
        escaped = html_module.escape(text)
        return escaped.replace("\n", "<br>\n")

    @staticmethod
    def _clean_screenshot_placeholder(html_body: str) -> str:
        """Strip the decorative screenshot placeholder wrapper, keeping only {{screenshot}}.

        The rich-text editor inserts a styled div with descriptive text around
        the {{screenshot}} variable.  Before substitution we reduce the entire
        wrapper to just the bare placeholder so the <img> tag (or empty string)
        replaces everything cleanly.

        Multiple patterns handle browser style normalization (hex vs RGB, with/without spaces).
        """
        patterns = [
            # Original hex color as inserted by JS: background:#fff3cd
            r'<div[^>]*style="[^"]*background(?:-color)?[^:]*:\s*#fff3cd[^"]*"[^>]*>.*?\{\{screenshot\}\}.*?</div>',
            # Browser-normalized RGB: background-color: rgb(255, 243, 205)
            r'<div[^>]*style="[^"]*background(?:-color)?[^:]*:\s*rgb\(255,\s*243,\s*205\)[^"]*"[^>]*>.*?\{\{screenshot\}\}.*?</div>',
            # Fallback: match by unique placeholder text content (any wrapper style)
            r'<div[^>]*>.*?\{\{screenshot\}\}.*?Captura del Excel se insertara aqui automaticamente.*?</div>',
        ]
        for pattern in patterns:
            result = re.sub(pattern, "{{screenshot}}", html_body, flags=re.DOTALL | re.IGNORECASE)
            if result != html_body:
                return result
        return html_body

    @staticmethod
    def _substitute_variables(text: str, variables: dict) -> str:
        result = text
        for var_name, value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            result = result.replace(placeholder, str(value))
        return result
