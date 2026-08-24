from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from app.domain.models import Modell

# Preise im Register sind USD je Million Tokens (SPEC.md, "Kostenformel").
_PREIS_EINHEIT_TOKENS = 1_000_000


@dataclass(frozen=True)
class PreisSchnappschuss:
    """Die vier zum Ausführungszeitpunkt gültigen Preissätze eines Modells, unabhängig davon,
    ob ein Posten tatsächlich anfiel — damit jede Kostenzahl nachrechenbar bleibt."""

    preis_input: Optional[float]
    preis_cached_input: Optional[float]
    preis_output: Optional[float]
    preis_suche: Optional[float]


@dataclass(frozen=True)
class TokenNutzung:
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    web_search_calls: int


_LEERER_SCHNAPPSCHUSS = PreisSchnappschuss(None, None, None, None)


def schnappschuss_aus_modell(modell: Optional[Modell]) -> PreisSchnappschuss:
    if modell is None:
        return _LEERER_SCHNAPPSCHUSS
    return PreisSchnappschuss(
        preis_input=modell.preis_input,
        preis_cached_input=modell.preis_cached_input,
        preis_output=modell.preis_output,
        preis_suche=modell.preis_suche,
    )


def berechne_kosten(nutzung: TokenNutzung, preise: PreisSchnappschuss) -> Optional[float]:
    """Kostenformel aus SPEC.md: gemeldete Input-Tokens enthalten die gecachten, gemeldete
    Output-Tokens enthalten Reasoning — beides wird deshalb nicht gesondert bepreist. Fehlt ein
    für die tatsächliche Nutzung benötigter Preis, ist das Ergebnis `None` statt `0`."""
    nicht_gecacht = nutzung.input_tokens - nutzung.cached_input_tokens
    posten = (
        _anteil(nicht_gecacht, preise.preis_input, _PREIS_EINHEIT_TOKENS),
        _anteil(nutzung.cached_input_tokens, preise.preis_cached_input, _PREIS_EINHEIT_TOKENS),
        _anteil(nutzung.output_tokens, preise.preis_output, _PREIS_EINHEIT_TOKENS),
        _anteil(nutzung.web_search_calls, preise.preis_suche, 1),
    )
    if any(bekannt is False for _, bekannt in posten):
        return None
    return sum(betrag for betrag, _ in posten)


def _anteil(menge: int, preis: Optional[float], einheit: int) -> Tuple[float, bool]:
    """Ein Posten mit Menge 0 braucht keinen Preis: 0 Tokens kosten 0, ob der Preis gepflegt ist
    oder nicht. Erst eine Menge > 0 ohne gepflegten Preis macht die Kostenzahl unbekannt."""
    if menge <= 0:
        return 0.0, True
    if preis is None:
        return 0.0, False
    return menge / einheit * preis, True
