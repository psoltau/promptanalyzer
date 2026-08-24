from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Tuple

from app.domain.errors import NameLeer


class CallStatus(str, Enum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    ERROR = "error"


@dataclass(frozen=True)
class Arbeitsstand:
    system_prompt: str
    user_prompt: str
    tools_json: Optional[str]
    modelle: Tuple[str, ...]
    max_output_tokens: Optional[int]
    reasoning_effort: Optional[str]
    web_suche: bool
    search_context_size: Optional[str]
    wiederholungen: int

    @staticmethod
    def leer() -> "Arbeitsstand":
        return Arbeitsstand(
            system_prompt="",
            user_prompt="",
            tools_json=None,
            modelle=(),
            max_output_tokens=None,
            reasoning_effort=None,
            web_suche=False,
            search_context_size=None,
            wiederholungen=1,
        )


@dataclass(frozen=True)
class Profil:
    id: str
    name: str
    erstellt_am: datetime
    arbeitsstand_geaendert_am: datetime
    arbeitsstand: Arbeitsstand

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise NameLeer()


@dataclass(frozen=True)
class ProfilUebersicht:
    id: str
    name: str
    erstellt_am: datetime
    arbeitsstand_geaendert_am: datetime
    anzahl_laeufe: int
    zuletzt_benutzt_am: Optional[datetime]


@dataclass(frozen=True)
class Lauf:
    id: str
    profil_id: str
    nummer: int
    gestartet_am: datetime
    beendet_am: Optional[datetime]
    arbeitsstand: Arbeitsstand


@dataclass(frozen=True)
class Modell:
    name: str
    preis_input: Optional[float]
    preis_cached_input: Optional[float]
    preis_output: Optional[float]
    preis_suche: Optional[float]
    kontextfenster: Optional[int]
    erlaubt_reasoning_effort: bool
    erlaubt_web_suche: bool
    unterstuetzt_prompt_caching: bool

    @staticmethod
    def neu(name: str) -> "Modell":
        return Modell(
            name=name,
            preis_input=None,
            preis_cached_input=None,
            preis_output=None,
            preis_suche=None,
            kontextfenster=None,
            erlaubt_reasoning_effort=True,
            erlaubt_web_suche=True,
            unterstuetzt_prompt_caching=True,
        )

    @property
    def preise_vollstaendig(self) -> bool:
        return (
            self.preis_input is not None
            and self.preis_cached_input is not None
            and self.preis_output is not None
        )


@dataclass(frozen=True)
class Call:
    id: str
    lauf_id: str
    modell_name: str
    wiederholung_index: int
    status: CallStatus
    incomplete_grund: Optional[str]
    fehlertext: Optional[str]
    dauer_ms: int
    input_tokens: Optional[int]
    cached_input_tokens: Optional[int]
    reasoning_tokens: Optional[int]
    output_tokens: Optional[int]
    total_tokens: Optional[int]
    web_search_calls: Optional[int]
    antwort_text: Optional[str]
    request_json: str
    response_json: Optional[str]
    erstellt_am: datetime
    preis_input: Optional[float]
    preis_cached_input: Optional[float]
    preis_output: Optional[float]
    preis_suche: Optional[float]
    kosten_usd: Optional[float]
