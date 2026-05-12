from __future__ import annotations

import httpx

from app.config import SecretProvider, Settings


class CompeakClient:
    def __init__(self, settings: Settings, secrets: SecretProvider):
        self.settings = settings
        self.token = secrets.get(settings.compeak_token_secret)
        self.base_url = "https://api.compeak.com"

    async def call(self, phone: str, script_id: str, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{self.base_url}/voice/calls", headers={"Authorization": f"Bearer {self.token}"}, json={"to": phone, "script_id": script_id, "payload": payload})
            response.raise_for_status()
            return response.json()
