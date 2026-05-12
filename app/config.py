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
    "flow_graph": {
        "version": 1,
        "trigger": {"id": "trg", "kind": "manual", "config": {}},
        "nodes": [
            {"id": "A", "type": "send_email_template", "label": "Information nouvelles conditions Waka", "audience_ref": "aud_all_prospects", "config": {"legal_url": "https://www.wakaorbit.com/legal", "question_agent_links": ["web_text_session:T", "web_voice_session:V", "web_avatar_session:AV"]}},
            {"id": "W1", "type": "wait", "label": "Attente 72h après email", "config": {"duration": "PT72H"}},
            {"id": "X1", "type": "condition", "label": "Email ouvert ?", "config": {"expr": "event.email_opened == true", "window": "PT72H", "action_ref": "A"}},
            {"id": "END_OPEN", "type": "end", "label": "Fin — email ouvert"},
            {"id": "B", "type": "send_sms_template", "label": "Relance SMS non-ouvreurs", "audience_ref": "aud_email_non_openers_72h", "config": {"legal_url": "https://www.wakaorbit.com/legal", "question_agent_links": ["web_text_session:T", "web_voice_session:V", "web_avatar_session:AV"]}},
            {"id": "W2", "type": "wait", "label": "Mesure SMS à 72h", "config": {"duration": "PT72H"}},
            {"id": "END_SMS", "type": "end", "label": "Fin — SMS mesuré"},
            {"id": "T", "type": "web_text_session", "label": "Questions — agent texte", "agent_id": "11be752f-8ee8-4080-ade6-8a0bc4bc2636", "audience_ref": "aud_all_prospects"},
            {"id": "V", "type": "web_voice_session", "label": "Questions — agent voix web", "agent_id": "b156d452-eafd-46f4-907f-c51e32e72ccc", "audience_ref": "aud_all_prospects"},
            {"id": "AV", "type": "web_avatar_session", "label": "Questions — agent avatar", "agent_id": "277098c3-aec4-46a9-a445-9beaa1835c2c", "audience_ref": "aud_all_prospects"},
        ],
        "edges": [
            {"from": "trg", "to": "A"}, {"from": "A", "to": "W1"}, {"from": "W1", "to": "X1"},
            {"from": "X1", "to": "END_OPEN", "label": "yes"}, {"from": "X1", "to": "B", "label": "no"},
            {"from": "B", "to": "W2"}, {"from": "W2", "to": "END_SMS"},
        ],
    },
    "audiences": [
        {"id": "aud_all_prospects", "label": "Toute la base prospects", "estimated_count": 3484, "filters": []},
        {"id": "aud_email_non_openers_72h", "label": "Non-ouvreurs email après 72h", "estimated_count": None, "derived_from": "aud_all_prospects"},
    ],
    "success_metrics": [
        {"id": "cumulative_open_rate", "label": "Ouverture cumulée email + SMS", "description": "% des contacts ayant ouvert l’email A ou lu/ouvert le SMS B dans la fenêtre de mesure.", "kind": "business", "format": "percentage", "target": 0.9, "window": {"value": 6, "unit": "day"}, "viz": "gauge"},
        {"id": "open_rate_email_vs_sms", "label": "Comparaison ouverture email vs SMS", "description": "Deux barres comparant le taux d’ouverture email A et le taux de lecture/ouverture SMS B mesuré 72h après envoi SMS.", "kind": "business", "format": "percentage", "target": None, "window": {"value": 72, "unit": "hour"}, "viz": "breakdown_bar", "breakdown_by": "channel"},
        {"id": "open_rate_day_over_day", "label": "Progression des ouvertures day-over-day", "description": "Évolution quotidienne du taux d’ouverture cumulée email + SMS.", "kind": "business", "format": "percentage", "target": 0.9, "window": {"value": 6, "unit": "day"}, "viz": "timeseries"},
    ],
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
