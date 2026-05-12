from __future__ import annotations

from azure.communication.email import EmailClient

from app.config import SecretProvider, Settings


class AcsEmailClient:
    def __init__(self, settings: Settings, secrets: SecretProvider):
        self.settings = settings
        self.client = EmailClient.from_connection_string(secrets.get(settings.acs_email_connection_string_secret))

    def send_html(self, to_email: str, subject: str, html: str, correlation_id: str) -> str:
        message = {
            "senderAddress": self.settings.email_sender_address,
            "recipients": {"to": [{"address": to_email}]},
            "content": {"subject": subject, "html": html},
            "headers": {"x-orbit-correlation-id": correlation_id},
        }
        if self.settings.email_reply_to:
            message["replyTo"] = [{"address": self.settings.email_reply_to}]
        poller = self.client.begin_send(message)
        result = poller.result()
        message_id = getattr(result, "message_id", None) or getattr(result, "id", None)
        if not message_id:
            message_id = correlation_id
        return str(message_id)
