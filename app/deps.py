from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.config import SecretProvider, Settings, get_settings
from app.storage.tables import TableStore


@lru_cache(maxsize=1)
def get_store_cached() -> TableStore:
    store = TableStore(get_settings())
    return store


@lru_cache(maxsize=1)
def get_secret_provider_cached() -> SecretProvider:
    return SecretProvider(get_settings())


def settings_dep() -> Settings:
    return get_settings()


def store_dep() -> TableStore:
    return get_store_cached()


def secrets_dep() -> SecretProvider:
    return get_secret_provider_cached()


def console_actor(x_orbit_actor: Annotated[str | None, Header()] = None) -> str:
    return x_orbit_actor or "console"


def require_internal_token(x_orbit_internal: Annotated[str | None, Header()] = None) -> None:
    settings = get_settings()
    if settings.environment == "development":
        return
    if x_orbit_internal != "true":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="internal token required")
