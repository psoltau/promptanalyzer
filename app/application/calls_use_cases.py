from dataclasses import dataclass
from typing import Callable, List, Optional

from app.application.ports import CallRepository, LaufRepository
from app.domain.errors import CallNichtGefunden
from app.domain.models import Call, Lauf


@dataclass
class LaufAggregat:
    anzahl_calls: int
    input_tokens: int
    cached_input_tokens: int
    reasoning_tokens: int
    output_tokens: int
    total_tokens: int
    web_search_calls: int
    dauer_ms_mittel: Optional[int]


@dataclass
class LaufUebersichtEintrag:
    lauf: Lauf
    erwartete_calls: int
    fertige_calls: int
    aggregat: LaufAggregat


@dataclass
class CallsView:
    laeufe: List[LaufUebersichtEintrag]
    calls: List[Call]


@dataclass
class CallDetailView:
    call: Call
    lauf: Lauf


def list_calls_view(
    profil_id: str, lauf_repo: LaufRepository, call_repo: CallRepository
) -> CallsView:
    laeufe = lauf_repo.list_for_profil(profil_id)
    calls = call_repo.list_for_profil(profil_id)
    eintraege = [_lauf_eintrag(lauf, calls) for lauf in laeufe]
    return CallsView(laeufe=eintraege, calls=calls)


def get_call_view(call_id: str, call_repo: CallRepository, lauf_repo: LaufRepository) -> CallDetailView:
    call = call_repo.get(call_id)
    if call is None:
        raise CallNichtGefunden()
    lauf = lauf_repo.get(call.lauf_id)
    assert lauf is not None
    return CallDetailView(call=call, lauf=lauf)


def _lauf_eintrag(lauf: Lauf, alle_calls: List[Call]) -> LaufUebersichtEintrag:
    calls = [c for c in alle_calls if c.lauf_id == lauf.id]
    erwartete_calls = len(lauf.arbeitsstand.modelle) * lauf.arbeitsstand.wiederholungen
    return LaufUebersichtEintrag(
        lauf=lauf,
        erwartete_calls=erwartete_calls,
        fertige_calls=len(calls),
        aggregat=_aggregiere(calls),
    )


def _aggregiere(calls: List[Call]) -> LaufAggregat:
    dauern = [c.dauer_ms for c in calls]
    mittel = round(sum(dauern) / len(dauern)) if dauern else None
    return LaufAggregat(
        anzahl_calls=len(calls),
        input_tokens=_summe(calls, lambda c: c.input_tokens),
        cached_input_tokens=_summe(calls, lambda c: c.cached_input_tokens),
        reasoning_tokens=_summe(calls, lambda c: c.reasoning_tokens),
        output_tokens=_summe(calls, lambda c: c.output_tokens),
        total_tokens=_summe(calls, lambda c: c.total_tokens),
        web_search_calls=_summe(calls, lambda c: c.web_search_calls),
        dauer_ms_mittel=mittel,
    )


def _summe(calls: List[Call], feld: Callable[[Call], Optional[int]]) -> int:
    return sum(feld(c) or 0 for c in calls)
