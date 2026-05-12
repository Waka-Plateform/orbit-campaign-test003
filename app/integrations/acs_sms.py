from __future__ import annotations

from azure.communication.sms import SmsClient

from app.config import SecretProvider, Settings


class AcsSmsClient:
    def __init__(self, settings: Settings, secrets: SecretProvider):
        self.settings = settings
        self.client = SmsClient.from_connection_string(secrets.get(settings.acs_sms_connection_string_secret))

    def send(self, to_phone: str, body: str, correlation_id: str) -> str:
        result = self.client.send(from_=self.settings.sms_from, to=[to_phone], message=body, enable_delivery_report=True, tag=correlation_id)
        if not result:
            raise RuntimeError("ACS SMS returned an empty result")
        first = result[0]
        message_id = getattr(first, "message_id", None) or getattr(first, "sid", None) or correlation_id
        return str(message_id)
