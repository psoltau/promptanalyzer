from typing import List, Optional

from pydantic import BaseModel


class ArbeitsstandBody(BaseModel):
    system_prompt: str
    user_prompt: str
    tools_json: Optional[str] = None
    modelle: List[str] = []
    max_output_tokens: Optional[int] = None
    reasoning_effort: Optional[str] = None
    web_suche: bool = False
    search_context_size: Optional[str] = None
    wiederholungen: int = 1


class ProfilListItem(BaseModel):
    id: str
    name: str
    erstellt_am: str
    arbeitsstand_geaendert_am: str
    anzahl_laeufe: int
    zuletzt_benutzt_am: Optional[str]


class ProfilCreateBody(BaseModel):
    name: str


class ProfilDetail(BaseModel):
    id: str
    name: str
    erstellt_am: str
    arbeitsstand_geaendert_am: str
    arbeitsstand: ArbeitsstandBody


class ArbeitsstandSaveResponse(BaseModel):
    arbeitsstand_geaendert_am: str


class LaufStartResponse(BaseModel):
    lauf_id: str
    nummer: int
    erwartete_calls: int
    gestartet_am: str


class LaufAggregatBody(BaseModel):
    anzahl_calls: int
    input_tokens: int
    cached_input_tokens: int
    reasoning_tokens: int
    output_tokens: int
    total_tokens: int
    web_search_calls: int
    kosten_usd: Optional[float]
    dauer_ms_mittel: Optional[int]


class LaufSummary(BaseModel):
    lauf_id: str
    nummer: int
    gestartet_am: str
    beendet_am: Optional[str]
    erwartete_calls: int
    fertige_calls: int
    einstellungen: ArbeitsstandBody
    aggregat: LaufAggregatBody


class CallRow(BaseModel):
    id: str
    lauf_id: str
    lauf_nummer: int
    modell_name: str
    wiederholung_index: int
    status: str
    incomplete_grund: Optional[str]
    hat_fehler: bool
    max_output_tokens: Optional[int]
    reasoning_effort: Optional[str]
    web_suche: bool
    search_context_size: Optional[str]
    input_tokens: Optional[int]
    cached_input_tokens: Optional[int]
    reasoning_tokens: Optional[int]
    output_tokens: Optional[int]
    total_tokens: Optional[int]
    web_search_calls: Optional[int]
    kosten_usd: Optional[float]
    dauer_ms: int
    erstellt_am: str


class CallsResponse(BaseModel):
    laeufe: List[LaufSummary]
    calls: List[CallRow]


class PreiseBody(BaseModel):
    preis_input: Optional[float]
    preis_cached_input: Optional[float]
    preis_output: Optional[float]
    preis_suche: Optional[float]


class CallDetail(BaseModel):
    id: str
    lauf_id: str
    lauf_nummer: int
    modell_name: str
    wiederholung_index: int
    status: str
    incomplete_grund: Optional[str]
    fehlertext: Optional[str]
    antwort_text: Optional[str]
    schnappschuss: ArbeitsstandBody
    preise: PreiseBody
    request_json: dict
    response_json: Optional[dict]
