import json
from datetime import datetime
from typing import Dict, Optional

from app.adapters.http.schemas import (
    ArbeitsstandBody,
    CallDetail,
    CallRow,
    CallsResponse,
    KeyStatusResponse,
    LaufAggregatBody,
    LaufEinstellungen,
    LaufStartResponse,
    LaufSummary,
    PreiseBody,
    ProfilDetail,
    ProfilListItem,
)
from app.application.calls_use_cases import CallDetailView, CallsView, LaufUebersichtEintrag
from app.domain.models import Arbeitsstand, Call, Lauf, Profil, ProfilUebersicht


def to_iso_z(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _to_iso_z_optional(dt: Optional[datetime]) -> Optional[str]:
    return to_iso_z(dt) if dt is not None else None


def arbeitsstand_to_body(arbeitsstand: Arbeitsstand) -> ArbeitsstandBody:
    return ArbeitsstandBody(
        system_prompt=arbeitsstand.system_prompt,
        user_prompt=arbeitsstand.user_prompt,
        tools_json=arbeitsstand.tools_json,
        modelle=list(arbeitsstand.modelle),
        max_output_tokens=arbeitsstand.max_output_tokens,
        reasoning_effort=arbeitsstand.reasoning_effort,
        web_suche=arbeitsstand.web_suche,
        search_context_size=arbeitsstand.search_context_size,
        wiederholungen=arbeitsstand.wiederholungen,
    )


def body_to_arbeitsstand(body: ArbeitsstandBody) -> Arbeitsstand:
    return Arbeitsstand(
        system_prompt=body.system_prompt,
        user_prompt=body.user_prompt,
        tools_json=body.tools_json,
        modelle=tuple(body.modelle),
        max_output_tokens=body.max_output_tokens,
        reasoning_effort=body.reasoning_effort,
        web_suche=body.web_suche,
        search_context_size=body.search_context_size,
        wiederholungen=body.wiederholungen,
    )


def profil_uebersicht_to_item(profil: ProfilUebersicht) -> ProfilListItem:
    return ProfilListItem(
        id=profil.id,
        name=profil.name,
        erstellt_am=to_iso_z(profil.erstellt_am),
        arbeitsstand_geaendert_am=to_iso_z(profil.arbeitsstand_geaendert_am),
        anzahl_laeufe=profil.anzahl_laeufe,
        zuletzt_benutzt_am=_to_iso_z_optional(profil.zuletzt_benutzt_am),
    )


def profil_to_detail(profil: Profil) -> ProfilDetail:
    return ProfilDetail(
        id=profil.id,
        name=profil.name,
        erstellt_am=to_iso_z(profil.erstellt_am),
        arbeitsstand_geaendert_am=to_iso_z(profil.arbeitsstand_geaendert_am),
        arbeitsstand=arbeitsstand_to_body(profil.arbeitsstand),
    )


def env_key_to_status(env_key: Optional[str]) -> KeyStatusResponse:
    return KeyStatusResponse(umgebungs_key_vorhanden=env_key is not None)


def lauf_to_start_response(lauf: Lauf) -> LaufStartResponse:
    erwartete_calls = len(lauf.arbeitsstand.modelle) * lauf.arbeitsstand.wiederholungen
    return LaufStartResponse(
        lauf_id=lauf.id,
        nummer=lauf.nummer,
        erwartete_calls=erwartete_calls,
        gestartet_am=to_iso_z(lauf.gestartet_am),
    )


def calls_view_to_response(view: CallsView) -> CallsResponse:
    laeufe_by_id: Dict[str, Lauf] = {eintrag.lauf.id: eintrag.lauf for eintrag in view.laeufe}
    return CallsResponse(
        laeufe=[_lauf_eintrag_to_summary(eintrag) for eintrag in view.laeufe],
        calls=[_call_to_row(call, laeufe_by_id[call.lauf_id]) for call in view.calls],
    )


def _lauf_eintrag_to_summary(eintrag: LaufUebersichtEintrag) -> LaufSummary:
    lauf = eintrag.lauf
    return LaufSummary(
        lauf_id=lauf.id,
        nummer=lauf.nummer,
        gestartet_am=to_iso_z(lauf.gestartet_am),
        beendet_am=_to_iso_z_optional(lauf.beendet_am),
        erwartete_calls=eintrag.erwartete_calls,
        fertige_calls=eintrag.fertige_calls,
        einstellungen=_einstellungen(lauf.arbeitsstand),
        aggregat=_aggregat_to_body(eintrag),
    )


def _einstellungen(arbeitsstand: Arbeitsstand) -> LaufEinstellungen:
    return LaufEinstellungen(
        modelle=list(arbeitsstand.modelle),
        max_output_tokens=arbeitsstand.max_output_tokens,
        reasoning_effort=arbeitsstand.reasoning_effort,
        web_suche=arbeitsstand.web_suche,
        search_context_size=arbeitsstand.search_context_size,
        wiederholungen=arbeitsstand.wiederholungen,
    )


def _aggregat_to_body(eintrag: LaufUebersichtEintrag) -> LaufAggregatBody:
    aggregat = eintrag.aggregat
    return LaufAggregatBody(
        anzahl_calls=aggregat.anzahl_calls,
        input_tokens=aggregat.input_tokens,
        cached_input_tokens=aggregat.cached_input_tokens,
        reasoning_tokens=aggregat.reasoning_tokens,
        output_tokens=aggregat.output_tokens,
        total_tokens=aggregat.total_tokens,
        web_search_calls=aggregat.web_search_calls,
        kosten_usd=None,
        dauer_ms_mittel=aggregat.dauer_ms_mittel,
    )


def _call_to_row(call: Call, lauf: Lauf) -> CallRow:
    arbeitsstand = lauf.arbeitsstand
    return CallRow(
        id=call.id,
        lauf_id=call.lauf_id,
        lauf_nummer=lauf.nummer,
        modell_name=call.modell_name,
        wiederholung_index=call.wiederholung_index,
        status=call.status.value,
        incomplete_grund=call.incomplete_grund,
        hat_fehler=call.fehlertext is not None,
        max_output_tokens=arbeitsstand.max_output_tokens,
        reasoning_effort=arbeitsstand.reasoning_effort,
        web_suche=arbeitsstand.web_suche,
        search_context_size=arbeitsstand.search_context_size,
        kosten_usd=None,
        dauer_ms=call.dauer_ms,
        erstellt_am=to_iso_z(call.erstellt_am),
        **_call_tokens(call),
    )


def _call_tokens(call: Call) -> Dict[str, Optional[int]]:
    return {
        "input_tokens": call.input_tokens,
        "cached_input_tokens": call.cached_input_tokens,
        "reasoning_tokens": call.reasoning_tokens,
        "output_tokens": call.output_tokens,
        "total_tokens": call.total_tokens,
        "web_search_calls": call.web_search_calls,
    }


def call_detail_view_to_schema(view: CallDetailView) -> CallDetail:
    call = view.call
    return CallDetail(
        id=call.id,
        lauf_id=call.lauf_id,
        lauf_nummer=view.lauf.nummer,
        modell_name=call.modell_name,
        wiederholung_index=call.wiederholung_index,
        status=call.status.value,
        incomplete_grund=call.incomplete_grund,
        fehlertext=call.fehlertext,
        antwort_text=call.antwort_text,
        schnappschuss=arbeitsstand_to_body(view.lauf.arbeitsstand),
        preise=PreiseBody(
            preis_input=None, preis_cached_input=None, preis_output=None, preis_suche=None
        ),
        request_json=json.loads(call.request_json),
        response_json=json.loads(call.response_json) if call.response_json else None,
    )
