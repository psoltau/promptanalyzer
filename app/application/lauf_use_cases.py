import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

from app.application.ports import (
    LaufExecutionPorts,
    LaufKostenPorts,
    LaufStartPorts,
    ModelGatewayError,
    ModelRequest,
    ModelResult,
    ModellRepository,
)
from app.domain.errors import (
    KeinModellGewaehlt,
    KeyFehlt,
    LaufLaeuftNoch,
    LaufNichtGefunden,
    ProfilNichtGefunden,
    ToolsJsonUngueltig,
    WiederholungenUngueltig,
)
from app.domain.kosten import (
    PreisSchnappschuss,
    TokenNutzung,
    berechne_kosten,
    schnappschuss_aus_modell,
)
from app.domain.models import Arbeitsstand, Call, CallStatus, Lauf, Modell


def start_lauf(profil_id: str, api_key: Optional[str], ports: LaufStartPorts) -> Lauf:
    profil = ports.profil_repo.get(profil_id)
    if profil is None:
        raise ProfilNichtGefunden()
    arbeitsstand = profil.arbeitsstand
    _validiere_lauf_start(arbeitsstand, api_key)
    lauf = Lauf(
        id=str(uuid4()),
        profil_id=profil.id,
        nummer=ports.lauf_repo.next_nummer(profil.id),
        gestartet_am=datetime.now(timezone.utc),
        beendet_am=None,
        arbeitsstand=arbeitsstand,
    )
    ports.lauf_repo.add(lauf)
    assert api_key is not None
    ports.runner.start(lauf, api_key)
    return lauf


def _validiere_lauf_start(arbeitsstand: Arbeitsstand, api_key: Optional[str]) -> None:
    if not arbeitsstand.modelle:
        raise KeinModellGewaehlt()
    if arbeitsstand.wiederholungen < 1:
        raise WiederholungenUngueltig()
    if api_key is None:
        raise KeyFehlt()
    _validiere_tools_json(arbeitsstand.tools_json)


def _validiere_tools_json(tools_json: Optional[str]) -> None:
    if tools_json is None:
        return
    try:
        json.loads(tools_json)
    except json.JSONDecodeError as exc:
        raise ToolsJsonUngueltig() from exc


@dataclass
class _CallJob:
    lauf: Lauf
    modell_name: str
    wiederholung_index: int


@dataclass
class _AusfuehrungsKontext:
    job: _CallJob
    started: float
    modell_repo: ModellRepository


def execute_lauf(lauf: Lauf, api_key: str, ports: LaufExecutionPorts) -> None:
    arbeitsstand = lauf.arbeitsstand
    for modell_name in arbeitsstand.modelle:
        for wiederholung_index in range(1, arbeitsstand.wiederholungen + 1):
            job = _CallJob(lauf, modell_name, wiederholung_index)
            call = _run_single_call(job, api_key, ports)
            ports.call_repo.add(call)
    ports.lauf_repo.mark_beendet(lauf.id, datetime.now(timezone.utc))


def _run_single_call(job: _CallJob, api_key: str, ports: LaufExecutionPorts) -> Call:
    request = _build_request(job, api_key)
    kontext = _AusfuehrungsKontext(job=job, started=time.monotonic(), modell_repo=ports.modell_repo)
    try:
        result = ports.gateway.run(request)
    except ModelGatewayError as exc:
        return _fehler_call(kontext, exc)
    return _erfolg_call(kontext, result)


def _build_request(job: _CallJob, api_key: str) -> ModelRequest:
    arbeitsstand = job.lauf.arbeitsstand
    return ModelRequest(
        system_prompt=arbeitsstand.system_prompt,
        user_prompt=arbeitsstand.user_prompt,
        tools_json=arbeitsstand.tools_json,
        model=job.modell_name,
        max_output_tokens=arbeitsstand.max_output_tokens,
        reasoning_effort=arbeitsstand.reasoning_effort,
        web_suche=arbeitsstand.web_suche,
        search_context_size=arbeitsstand.search_context_size,
        api_key=api_key,
    )


def _dauer_ms(started: float) -> int:
    return round((time.monotonic() - started) * 1000)


def _call_basis(kontext: _AusfuehrungsKontext) -> Dict[str, Any]:
    job = kontext.job
    return {
        "id": str(uuid4()),
        "lauf_id": job.lauf.id,
        "modell_name": job.modell_name,
        "wiederholung_index": job.wiederholung_index,
        "dauer_ms": _dauer_ms(kontext.started),
        "erstellt_am": datetime.now(timezone.utc),
    }


def _leere_kosten_felder() -> Dict[str, Optional[float]]:
    return {
        "preis_input": None,
        "preis_cached_input": None,
        "preis_output": None,
        "preis_suche": None,
        "kosten_usd": None,
    }


def _fehler_call(kontext: _AusfuehrungsKontext, exc: ModelGatewayError) -> Call:
    return Call(
        **_call_basis(kontext),
        status=CallStatus.ERROR,
        incomplete_grund=None,
        fehlertext=str(exc),
        input_tokens=None,
        cached_input_tokens=None,
        reasoning_tokens=None,
        output_tokens=None,
        total_tokens=None,
        web_search_calls=None,
        antwort_text=None,
        request_json=exc.request_json,
        response_json=None,
        **_leere_kosten_felder(),
    )


def _erfolg_call(kontext: _AusfuehrungsKontext, result: ModelResult) -> Call:
    status = CallStatus.INCOMPLETE if result.incomplete_grund else CallStatus.COMPLETE
    modell = kontext.modell_repo.get(kontext.job.modell_name)
    preise, kosten_usd = _preise_und_kosten(modell, _nutzung_aus_result(result))
    return Call(
        **_call_basis(kontext),
        status=status,
        incomplete_grund=result.incomplete_grund,
        fehlertext=None,
        input_tokens=result.input_tokens,
        cached_input_tokens=result.cached_input_tokens,
        reasoning_tokens=result.reasoning_tokens,
        output_tokens=result.output_tokens,
        total_tokens=result.total_tokens,
        web_search_calls=result.web_search_calls,
        antwort_text=result.antwort_text,
        request_json=result.request_json,
        response_json=result.response_json,
        preis_input=preise.preis_input,
        preis_cached_input=preise.preis_cached_input,
        preis_output=preise.preis_output,
        preis_suche=preise.preis_suche,
        kosten_usd=kosten_usd,
    )


def _preise_und_kosten(
    modell: Optional[Modell], nutzung: TokenNutzung
) -> Tuple[PreisSchnappschuss, Optional[float]]:
    preise = schnappschuss_aus_modell(modell)
    return preise, berechne_kosten(nutzung, preise)


def _nutzung_aus_result(result: ModelResult) -> TokenNutzung:
    return TokenNutzung(
        input_tokens=result.input_tokens,
        cached_input_tokens=result.cached_input_tokens,
        output_tokens=result.output_tokens,
        web_search_calls=result.web_search_calls,
    )


def kosten_neu_berechnen(lauf_id: str, ports: LaufKostenPorts) -> int:
    lauf = ports.lauf_repo.get(lauf_id)
    if lauf is None:
        raise LaufNichtGefunden()
    if lauf.beendet_am is None:
        raise LaufLaeuftNoch()
    calls = ports.call_repo.list_for_lauf(lauf_id)
    for call in calls:
        _kosten_neu_fuer_call(call, ports)
    return len(calls)


def _kosten_neu_fuer_call(call: Call, ports: LaufKostenPorts) -> None:
    if call.input_tokens is None:
        return  # Kein Verbrauch gemeldet (z. B. status=error) — nichts zu bepreisen.
    modell = ports.modell_repo.get(call.modell_name)
    preise, kosten_usd = _preise_und_kosten(modell, _nutzung_aus_call(call))
    ports.call_repo.update_kosten(call.id, preise, kosten_usd)


def _nutzung_aus_call(call: Call) -> TokenNutzung:
    return TokenNutzung(
        input_tokens=call.input_tokens,
        cached_input_tokens=call.cached_input_tokens,
        output_tokens=call.output_tokens,
        web_search_calls=call.web_search_calls,
    )
