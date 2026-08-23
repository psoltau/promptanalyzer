import sqlite3
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Header

from app.application.ports import (
    CallRepository,
    LaufRepository,
    LaufRunner,
    LaufStartPorts,
    ModelGateway,
    ProfilRepository,
)

_NICHT_VERDRAHTET = "Dependency wurde nicht in main.py verdrahtet"


def get_connection() -> sqlite3.Connection:
    raise RuntimeError(_NICHT_VERDRAHTET)


def get_profil_repo(connection: sqlite3.Connection = Depends(get_connection)) -> ProfilRepository:
    raise RuntimeError(_NICHT_VERDRAHTET)


def get_lauf_repo(connection: sqlite3.Connection = Depends(get_connection)) -> LaufRepository:
    raise RuntimeError(_NICHT_VERDRAHTET)


def get_call_repo(connection: sqlite3.Connection = Depends(get_connection)) -> CallRepository:
    raise RuntimeError(_NICHT_VERDRAHTET)


def get_gateway() -> ModelGateway:
    raise RuntimeError(_NICHT_VERDRAHTET)


def get_lauf_runner() -> LaufRunner:
    raise RuntimeError(_NICHT_VERDRAHTET)


def get_env_api_key() -> Optional[str]:
    raise RuntimeError(_NICHT_VERDRAHTET)


def resolve_api_key(
    x_openai_key: Optional[str] = Header(default=None, alias="X-OpenAI-Key"),
    env_key: Optional[str] = Depends(get_env_api_key),
) -> Optional[str]:
    return x_openai_key or env_key


@dataclass
class LaufStartDeps:
    ports: LaufStartPorts
    api_key: Optional[str]


def get_lauf_start_deps(
    profil_repo: ProfilRepository = Depends(get_profil_repo),
    lauf_repo: LaufRepository = Depends(get_lauf_repo),
    runner: LaufRunner = Depends(get_lauf_runner),
    api_key: Optional[str] = Depends(resolve_api_key),
) -> LaufStartDeps:
    return LaufStartDeps(LaufStartPorts(profil_repo, lauf_repo, runner), api_key)
