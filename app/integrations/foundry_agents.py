from __future__ import annotations

import httpx

from app.config import AGENTS, SecretProvider, Settings


class FoundryAgentsClient:
    def __init__(self, settings: Settings, secrets: SecretProvider):
        self.settings = settings
        self.endpoint = secrets.get(settings.foundry_endpoint_secret_name).rstrip("/")
        self.api_key = secrets.get(settings.foundry_api_key_secret_name)

    async def create_session(self, kind: str, contact_id: str, metadata: dict) -> str:
        agent_id = AGENTS[kind]
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{self.endpoint}/agents/{agent_id}/sessions", headers={"api-key": self.api_key}, json={"contact_id": contact_id, "metadata": metadata})
            response.raise_for_status()
            data = response.json()
            url = data.get("url")
            if not url:
                raise RuntimeError(f"Foundry session for {kind} did not return an url")
            return str(url)
