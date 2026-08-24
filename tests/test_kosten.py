from app.domain.kosten import (
    PreisSchnappschuss,
    TokenNutzung,
    berechne_kosten,
    schnappschuss_aus_modell,
)
from app.domain.models import Modell

_VOLLE_PREISE = PreisSchnappschuss(
    preis_input=1.0, preis_cached_input=0.1, preis_output=10.0, preis_suche=25.0
)


def _nutzung(**overrides) -> TokenNutzung:
    basis = dict(input_tokens=1000, cached_input_tokens=0, output_tokens=1000, web_search_calls=0)
    basis.update(overrides)
    return TokenNutzung(**basis)


def test_input_und_output_werden_zum_jeweiligen_satz_bepreist():
    kosten = berechne_kosten(_nutzung(input_tokens=1_000_000, output_tokens=1_000_000), _VOLLE_PREISE)

    assert kosten == 1.0 + 10.0


def test_gecachter_anteil_wird_zum_reduzierten_satz_gerechnet_der_rest_zum_input_satz():
    # input_tokens enthält die gecachten (SPEC.md): 1_000_000 gemeldete Input-Tokens, davon
    # 200_000 gecacht -> 800_000 zum Input-Satz, 200_000 zum reduzierten Satz.
    nutzung = _nutzung(input_tokens=1_000_000, cached_input_tokens=200_000, output_tokens=0)

    kosten = berechne_kosten(nutzung, _VOLLE_PREISE)

    erwartet = 0.8 * _VOLLE_PREISE.preis_input + 0.2 * _VOLLE_PREISE.preis_cached_input
    assert kosten == erwartet


def test_reasoning_tokens_werden_nicht_gesondert_bepreist():
    # Reasoning steckt bereits in output_tokens (SPEC.md) - die Kostenformel kennt gar keinen
    # eigenen Reasoning-Posten, sie sieht nur output_tokens.
    ohne_reasoning = _nutzung(output_tokens=1_000_000)
    mit_reasoning_in_output = _nutzung(output_tokens=1_000_000)

    assert berechne_kosten(ohne_reasoning, _VOLLE_PREISE) == berechne_kosten(
        mit_reasoning_in_output, _VOLLE_PREISE
    )


def test_web_suche_wird_je_suchanfrage_addiert():
    nutzung = _nutzung(input_tokens=0, output_tokens=0, web_search_calls=3)

    kosten = berechne_kosten(nutzung, _VOLLE_PREISE)

    assert kosten == 3 * _VOLLE_PREISE.preis_suche


def test_fehlender_benoetigter_preis_fuehrt_zu_none_statt_null():
    ohne_such_preis = PreisSchnappschuss(
        preis_input=1.0, preis_cached_input=0.1, preis_output=10.0, preis_suche=None
    )
    nutzung = _nutzung(web_search_calls=1)

    kosten = berechne_kosten(nutzung, ohne_such_preis)

    assert kosten is None


def test_fehlender_preis_fuer_menge_null_ist_unschaedlich():
    # 0 Suchanfragen brauchen keinen Suchpreis - die Kostenzahl bleibt bekannt.
    ohne_such_preis = PreisSchnappschuss(
        preis_input=1.0, preis_cached_input=0.1, preis_output=10.0, preis_suche=None
    )
    nutzung = _nutzung(web_search_calls=0)

    kosten = berechne_kosten(nutzung, ohne_such_preis)

    assert kosten is not None


def test_komplett_leerer_schnappschuss_ohne_nutzung_ergibt_null_kosten():
    leer = PreisSchnappschuss(None, None, None, None)

    kosten = berechne_kosten(_nutzung(input_tokens=0, output_tokens=0), leer)

    assert kosten == 0.0


def test_schnappschuss_aus_modell_uebernimmt_die_vier_preise():
    modell = Modell(
        name="gpt-5",
        preis_input=1.25,
        preis_cached_input=0.125,
        preis_output=10.0,
        preis_suche=25.0,
        kontextfenster=400000,
        erlaubt_reasoning_effort=True,
        erlaubt_web_suche=True,
        unterstuetzt_prompt_caching=True,
    )

    schnappschuss = schnappschuss_aus_modell(modell)

    assert schnappschuss == PreisSchnappschuss(1.25, 0.125, 10.0, 25.0)


def test_schnappschuss_aus_fehlendem_modell_ist_komplett_leer():
    assert schnappschuss_aus_modell(None) == PreisSchnappschuss(None, None, None, None)
