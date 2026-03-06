"""Unit tests for EmailSender service."""

import pytest
from unittest.mock import patch, MagicMock

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.schemas import (
    Recipient,
    Contact,
    ContactMapping,
    DataBlock,
    DataEntry,
    EmailTemplate,
    SendStatus,
)
from services.email_sender import EmailSender


def _make_mapping(name: str = "Oscar Herranz", email: str = "oscar@test.com") -> ContactMapping:
    """Create a test contact mapping."""
    return ContactMapping(
        recipient=Recipient(codigo=name, nombre=name),
        contact=Contact(codigo=name, nombre=name, email=email),
        email_found=True,
    )


def _make_block(name: str = "Oscar Herranz", entries: int = 3) -> DataBlock:
    """Create a test data block."""
    return DataBlock(
        recipient=Recipient(codigo=name, nombre=name),
        entries=[DataEntry(raw_cells={"C": f"Prof{i}"}, source_row=5 + i) for i in range(entries)],
    )


class TestEmailSender:
    """Tests for EmailSender."""

    def test_compose_email(self):
        """Test email composition with variable substitution."""
        sender = EmailSender()
        template = EmailTemplate(
            subject="Evaluacion -- {{tutor_name}}",
            body="<p>Hola {{tutor_name}}, tienes {{num_profesionales}} profesionales.</p>",
            is_html=True,
        )
        mapping = _make_mapping()
        attachment = ("test.xlsx", b"content")

        composition = sender.compose_email(
            template=template,
            mapping=mapping,
            attachment=attachment,
            extra_vars={"num_profesionales": "3"},
        )

        assert composition.to == "oscar@test.com"
        assert "Oscar Herranz" in composition.subject
        assert "3 profesionales" in composition.body
        assert composition.attachment_filename == "test.xlsx"

    def test_compose_email_cc(self):
        """Test CC emails are included."""
        sender = EmailSender()
        sender.set_cc_emails(["extra@test.com"])

        mapping = ContactMapping(
            recipient=Recipient(codigo="Test", nombre="Test"),
            contact=Contact(codigo="Test", nombre="Test", email="to@test.com", email_cc="cc@test.com"),
            email_found=True,
        )

        composition = sender.compose_email(
            template=EmailTemplate(),
            mapping=mapping,
            attachment=("f.xlsx", b"x"),
        )

        assert "extra@test.com" in composition.cc
        assert "cc@test.com" in composition.cc

    def test_check_status_no_url(self):
        """Test status check with no URL configured."""
        sender = EmailSender(power_automate_url="")
        status = sender.check_status()

        assert status["available"] is False
        assert "no configurada" in status["message"].lower()

    @patch("services.email_sender.requests.post")
    def test_send_email_success(self, mock_post):
        """Test successful email send."""
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_post.return_value = mock_response

        sender = EmailSender(power_automate_url="https://test.com/flow")
        mapping = _make_mapping()

        composition = sender.compose_email(
            template=EmailTemplate(),
            mapping=mapping,
            attachment=("file.xlsx", b"data"),
        )

        result = sender.send_email(composition)
        assert result.status == SendStatus.SUCCESS

    @patch("services.email_sender.requests.post")
    def test_send_email_failure(self, mock_post):
        """Test failed email send."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        sender = EmailSender(power_automate_url="https://test.com/flow")
        mapping = _make_mapping()

        composition = sender.compose_email(
            template=EmailTemplate(),
            mapping=mapping,
            attachment=("file.xlsx", b"data"),
        )

        result = sender.send_email(composition)
        assert result.status == SendStatus.FAILED

    def test_send_batch_test_mode(self):
        """Test batch send in test mode."""
        sender = EmailSender(power_automate_url="https://test.com/flow")

        mappings = [_make_mapping("Oscar Herranz", "oscar@t.com")]
        blocks = [_make_block("Oscar Herranz")]
        files = [("Oscar_Herranz_test.xlsx", b"content")]

        result = sender.send_batch(
            mappings=mappings,
            blocks=blocks,
            generated_files=files,
            test_mode=True,
        )

        assert result.sent_success == 1
        assert result.sent_failed == 0
        assert result.results[0].status == SendStatus.SUCCESS

    def test_send_batch_excluded(self):
        """Test excluded recipients in batch."""
        sender = EmailSender()
        mapping = _make_mapping()
        mapping.excluded = True
        mapping.recipient.excluded = True

        result = sender.send_batch(
            mappings=[mapping],
            blocks=[_make_block()],
            generated_files=[("Oscar_Herranz_test.xlsx", b"x")],
            test_mode=True,
        )

        assert result.excluded == 1
        assert result.results[0].status == SendStatus.EXCLUDED

    def test_send_batch_no_email(self):
        """Test handling of unmapped contacts in batch."""
        sender = EmailSender()
        mapping = ContactMapping(
            recipient=Recipient(codigo="Unknown", nombre="Unknown"),
            contact=None,
            email_found=False,
        )

        result = sender.send_batch(
            mappings=[mapping],
            blocks=[_make_block("Unknown")],
            generated_files=[],
            test_mode=True,
        )

        assert result.sent_failed == 1

    def test_preview_email(self):
        """Test email preview."""
        sender = EmailSender()
        mapping = _make_mapping()
        block = _make_block()

        preview = sender.preview_email(mapping, block)

        assert preview["to"] == "oscar@test.com"
        assert "Oscar Herranz" in preview["subject"]
        assert isinstance(preview["body"], str)

    def test_plain_text_to_html(self):
        """Test plain text to HTML conversion."""
        result = EmailSender._plain_text_to_html("Linea 1\nLinea 2")
        assert "<br>" in result
        assert "Linea 1" in result

    def test_variable_substitution(self):
        """Test template variable substitution."""
        result = EmailSender._substitute_variables(
            "Hola {{nombre}}, fecha: {{fecha}}",
            {"nombre": "Test", "fecha": "01/01/2026"},
        )
        assert result == "Hola Test, fecha: 01/01/2026"
