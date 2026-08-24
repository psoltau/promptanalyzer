from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Protocol

from app.domain.kosten import PreisSchnappschuss
from app.domain.models import Arbeitsstand, Call, Lauf, Modell, Profil, ProfilUebersicht


class ModelGatewayError(Exception):
    """Raised by a ModelGateway on transport or API failure."""

    def __init__(self, message: str, request_json: str) -> None:
        super().__init__(message)
        self.request_json = request_json


@dataclass
class ModelRequest:
    system_prompt: str
    user_prompt: str
    tools_json: Optional[str]
    model: str
    max_output_tokens: Optional[int]
    reasoning_effort: Optional[str]
    web_suche: bool
    search_context_size: Optional[str]
    api_key: str


@dataclass
class ModelResult:
    incomplete_grund: Optional[str]
    input_tokens: int
    cached_input_tokens: int
    reasoning_tokens: int
    output_tokens: int
    total_tokens: int
    web_search_calls: int
    antwort_text: str
    request_json: str
    response_json: str


class ModelGateway(Protocol):
    def run(self, request: ModelRequest) -> ModelResult: ...


class ProfilRepository(Protocol):
    def add(self, profil: Profil) -> None: ...
    def get(self, profil_id: str) -> Optional[Profil]: ...
    def list_uebersicht(self) -> List[ProfilUebersicht]: ...

    def save_arbeitsstand(
        self, profil_id: str, arbeitsstand: Arbeitsstand, geaendert_am: datetime
    ) -> None: ...


class LaufRepository(Protocol):
    def add(self, lauf: Lauf) -> None: ...
    def get(self, lauf_id: str) -> Optional[Lauf]: ...
    def list_for_profil(self, profil_id: str) -> List[Lauf]: ...
    def next_nummer(self, profil_id: str) -> int: ...
    def mark_beendet(self, lauf_id: str, beendet_am: datetime) -> None: ...


class CallRepository(Protocol):
    def add(self, call: Call) -> None: ...
    def get(self, call_id: str) -> Optional[Call]: ...
    def list_for_profil(self, profil_id: str) -> List[Call]: ...
    def list_for_lauf(self, lauf_id: str) -> List[Call]: ...

    def update_kosten(
        self, call_id: str, preise: PreisSchnappschuss, kosten_usd: Optional[float]
    ) -> None: ...


class ModellRepository(Protocol):
    def add(self, modell: Modell) -> None: ...
    def get(self, name: str) -> Optional[Modell]: ...
    def list(self) -> List[Modell]: ...
    def update(self, modell: Modell) -> None: ...
    def delete(self, name: str) -> None: ...


class LaufRunner(Protocol):
    def start(self, lauf: Lauf, api_key: str) -> None: ...


@dataclass
class LaufExecutionPorts:
    gateway: ModelGateway
    call_repo: CallRepository
    lauf_repo: LaufRepository
    modell_repo: ModellRepository


@dataclass
class LaufStartPorts:
    profil_repo: ProfilRepository
    lauf_repo: LaufRepository
    runner: LaufRunner


@dataclass
class LaufKostenPorts:
    lauf_repo: LaufRepository
    call_repo: CallRepository
    modell_repo: ModellRepository
