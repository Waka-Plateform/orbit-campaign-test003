from __future__ import annotations

from functools import lru_cache
from typing import Any

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    service_name: str = "orbit-campaign-test003"
    campaign_id: str = "4451dffd-e063-4cec-9105-d9ba3efde49b"
    campaign_name: str = "test003"
    campaign_slug: str = "test003"
    region: str = "francecentral"
    environment: str = Field(default="production", alias="ENVIRONMENT")

    resource_group: str = "rg-orbit-campaign-test003"
    container_app_name: str = "orbit-campaign-test003"
    container_app_url: str = ""
    key_vault_name: str = "kv-orbit-camp-test003"
    storage_account_name: str = "stcamptest003"
    managed_identity_name: str = "id-orbit-campaign-test003"
    github_repo: str = "Waka-Plateform/orbit-campaign-test003"
    shared_mailbox_address: str = "campaign-test003@wakacomvoice.onmicrosoft.com"

    artifacts_container: str = "artifacts"
    table_contacts: str = "contacts"
    legacy_table_prospects: str = "prospects"
    table_step_output: str = "stepoutput"
    table_events: str = "events"
    table_inbox: str = "inbox"
    table_audit_log: str = "auditlog"
    table_bounces: str = "bounces"
    table_optout: str = "optout"
    table_conversions: str = "conversions"
    table_state: str = "campaignstate"

    acs_endpoint: str = Field(default="https://orbit-acs.communication.azure.com/", alias="ACS_ENDPOINT")
    acs_email_connection_string_secret: str = "acs-email-connection-string"
    acs_sms_connection_string_secret: str = "acs-sms-connection-string"
    compeak_token_secret: str = "compeak-token"
    tracking_hmac_secret_name: str = "tracking-hmac-key"
    graph_client_secret_name: str = "graph-client-secret"
    foundry_endpoint_secret_name: str = "foundry-endpoint"
    foundry_api_key_secret_name: str = "foundry-api-key"

    email_sender_address: str = "DoNotReply@wakaorbit.com"
    email_sender_display_name: str = "Waka"
    email_reply_to: str = "campaign-test003@wakacomvoice.onmicrosoft.com"
    sms_from: str = "Waka"
    public_base_url: str = ""
    legal_url: str = "https://www.wakaorbit.com/legal"
    stop_number: str = "36180"
    agents_base_url: str = "https://wakaorbit.com/agents"

    scheduler_enabled: bool = True
    scheduler_interval_seconds: int = 60
    scheduler_batch_size: int = 50

    def kv_uri(self) -> str:
        return f"https://{self.key_vault_name}.vault.azure.net"


class SecretProvider:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        self._client = SecretClient(vault_url=settings.kv_uri(), credential=self._credential)
        self._cache: dict[str, str] = {}

    def get(self, name: str) -> str:
        if name not in self._cache:
            secret = self._client.get_secret(name)
            if not secret.value:
                raise RuntimeError(f"Key Vault secret {name} is empty")
            self._cache[name] = secret.value
        return self._cache[name]

    def optional(self, name: str) -> str | None:
        try:
            return self.get(name)
        except Exception as exc:
            raise RuntimeError(f"Required secret lookup failed for {name}: {exc}") from exc


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


CAMPAIGN_BRIEF: dict[str, Any] = {
    "objective": "Informer les 3 484 contacts des nouvelles conditions Waka via email template puis SMS de relance aux non-ouvreurs après 72h, avec liens vers les agents texte, voix et avatar pour les questions, et atteindre 90 % d’ouverture cumulée email + SMS.",
    "flow_graph": {"version": 1, "trigger": {"id": "trg", "kind": "manual", "config": {}}, "nodes": [], "edges": []},
    "audiences": [{"id": "aud_all_prospects", "label": "Toute la base prospects", "estimated_count": 3484, "filters": []}],
    "success_metrics": [{"id": "cumulative_open_rate", "label": "Ouverture cumulée email + SMS", "kind": "business", "format": "percentage", "target": 0.9, "window": {"value": 6, "unit": "day"}, "viz": "gauge"}],
}

ARTIFACTS: dict[str, dict[str, Any]] = {
    "art_email_A": {"action_id": "A", "kind": "email_template", "channel": "email", "mode": "templated", "blob_path": "artifacts/email/A/template.html", "subject": "Nouvelles conditions Waka"},
    "art_sms_B": {"action_id": "B", "kind": "sms_template", "channel": "sms", "mode": "templated", "blob_path": "artifacts/sms/B/template.txt"},
}

AGENTS: dict[str, str] = {
    "text": "11be752f-8ee8-4080-ade6-8a0bc4bc2636",
    "voice": "b156d452-eafd-46f4-907f-c51e32e72ccc",
    "avatar": "277098c3-aec4-46a9-a445-9beaa1835c2c",
}
