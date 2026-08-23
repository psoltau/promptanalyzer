import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from app.application.ports import (
    LaufExecutionPorts,
    LaufStartPorts,
    ModelGatewayError,
    ModelRequest,
    ModelResult,
)
from app.domain.errors import (
    KeinModellGewaehlt,
    KeyFehlt,
    ProfilNichtGefunden,
    ToolsJsonUngueltig,
    WiederholungenUngueltig,
)
from app.domain.models import Arbeitsstand, Call, CallStatus, Lauf


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
    started = time.monotonic()
    try:
        result = ports.gateway.run(request)
    except ModelGatewayError as exc:
        return _fehler_call(job, started, exc)
    return _erfolg_call(job, started, result)


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


def _call_basis(job: _CallJob, started: float) -> Dict[str, Any]:
    return {
        "id": str(uuid4()),
        "lauf_id": job.lauf.id,
        "modell_name": job.modell_name,
        "wiederholung_index": job.wiederholung_index,
        "dauer_ms": _dauer_ms(started),
        "erstellt_am": datetime.now(timezone.utc),
    }


def _fehler_call(job: _CallJob, started: float, exc: ModelGatewayError) -> Call:
    return Call(
        **_call_basis(job, started),
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
    )


def _erfolg_call(job: _CallJob, started: float, result: ModelResult) -> Call:
    status = CallStatus.INCOMPLETE if result.incomplete_grund else CallStatus.COMPLETE
    return Call(
        **_call_basis(job, started),
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
    )
