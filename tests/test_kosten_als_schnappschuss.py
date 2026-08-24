import time
from typing import Any, Dict

from tests.fakes import VorbereiteteAntwort

STANDARD_ARBEITSSTAND: Dict[str, Any] = {
    "system_prompt": "Du bist hilfreich.",
    "user_prompt": "Sag hallo.",
    "tools_json": None,
    "modelle": ["gpt-5"],
    "max_output_tokens": 512,
    "reasoning_effort": None,
    "web_suche": False,
    "search_context_size": None,
    "wiederholungen": 1,
}

_VOLLE_PREISE = {
    "preis_input": 1.0,
    "preis_cached_input": 0.1,
    "preis_output": 10.0,
    "preis_suche": 25.0,
    "kontextfenster": 400000,
    "erlaubt_reasoning_effort": True,
    "erlaubt_web_suche": True,
    "unterstuetzt_prompt_caching": True,
}


def _erstelle_profil_mit_arbeitsstand(client, **arbeitsstand_overrides):
    profil = client.post("/api/v1/profile", json={"name": "Testprofil"}).json()
    body = {**STANDARD_ARBEITSSTAND, **arbeitsstand_overrides}
    client.put(f"/api/v1/profile/{profil['id']}/arbeitsstand", json=body)
    return profil


def _starte_lauf(client, profil_id):
    return client.post(
        f"/api/v1/profile/{profil_id}/laeufe", headers={"X-OpenAI-Key": "sk-test"}
    ).json()


def _warte_auf_lauf_ende(client, profil_id, lauf_id, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        daten = client.get(f"/api/v1/profile/{profil_id}/calls").json()
        lauf = next(l for l in daten["laeufe"] if l["lauf_id"] == lauf_id)
        if lauf["beendet_am"] is not None:
            return daten
        time.sleep(0.02)
    raise AssertionError("Lauf wurde nicht rechtzeitig beendet")


def _fuehre_lauf_aus(client, gateway, antwort, **arbeitsstand_overrides):
    profil = _erstelle_profil_mit_arbeitsstand(client, **arbeitsstand_overrides)
    gateway.setze_standard(antwort)
    lauf = _starte_lauf(client, profil["id"])
    daten = _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])
    zeile = daten["calls"][0]
    return profil, lauf, zeile


def test_kostenspalte_je_call_in_usd(client, gateway):
    client.put("/api/v1/modelle/gpt-5", json=_VOLLE_PREISE)
    antwort = VorbereiteteAntwort(
        input_tokens=1_000_000, cached_input_tokens=0, output_tokens=1_000_000
    )

    _, _, zeile = _fuehre_lauf_aus(client, gateway, antwort)

    assert zeile["kosten_usd"] == 1.0 + 10.0


def test_gecachter_anteil_zum_reduzierten_satz_der_rest_zum_input_satz(client, gateway):
    client.put("/api/v1/modelle/gpt-5", json=_VOLLE_PREISE)
    antwort = VorbereiteteAntwort(
        input_tokens=1_000_000, cached_input_tokens=200_000, output_tokens=0
    )

    _, _, zeile = _fuehre_lauf_aus(client, gateway, antwort)

    erwartet = 0.8 * _VOLLE_PREISE["preis_input"] + 0.2 * _VOLLE_PREISE["preis_cached_input"]
    assert zeile["kosten_usd"] == erwartet


def test_reasoning_tokens_nicht_doppelt_bepreist(client, gateway):
    client.put("/api/v1/modelle/gpt-5", json=_VOLLE_PREISE)
    # output_tokens ist die gemeldete Gesamtsumme inklusive Reasoning (SPEC.md) - die Kostenzahl
    # darf sich nicht ändern, ob reasoning_tokens hoch oder null ist.
    mit_reasoning = VorbereiteteAntwort(
        input_tokens=0, output_tokens=1_000_000, reasoning_tokens=900_000
    )
    ohne_reasoning = VorbereiteteAntwort(
        input_tokens=0, output_tokens=1_000_000, reasoning_tokens=0
    )

    _, _, zeile_mit = _fuehre_lauf_aus(client, gateway, mit_reasoning)
    _, _, zeile_ohne = _fuehre_lauf_aus(client, gateway, ohne_reasoning)

    assert zeile_mit["kosten_usd"] == zeile_ohne["kosten_usd"] == 10.0


def test_fehlender_preis_fuehrt_zu_leerer_spalte_statt_null(client, gateway):
    # Kein PUT ans Register: die Saatliste liefert gpt-5 ohne gepflegte Preise.
    antwort = VorbereiteteAntwort(input_tokens=100, output_tokens=50)

    _, _, zeile = _fuehre_lauf_aus(client, gateway, antwort)

    assert zeile["kosten_usd"] is None


def test_suchanfragen_werden_in_der_vergleichstabelle_gezaehlt(client, gateway):
    antwort = VorbereiteteAntwort(input_tokens=10, output_tokens=5, web_search_calls=3)

    _, _, zeile = _fuehre_lauf_aus(client, gateway, antwort, web_suche=True)

    assert zeile["web_search_calls"] == 3
    # Web-Suche wird serverseitig ausgeführt: pro Call bleibt es bei genau einem Request.
    assert len(gateway.aufrufe) == 1


def test_suchkosten_sind_teil_der_kostenzahl(client, gateway):
    client.put("/api/v1/modelle/gpt-5", json=_VOLLE_PREISE)
    antwort = VorbereiteteAntwort(input_tokens=0, output_tokens=0, web_search_calls=3)

    _, _, zeile = _fuehre_lauf_aus(client, gateway, antwort, web_suche=True)

    assert zeile["web_search_calls"] == 3
    assert zeile["kosten_usd"] == 3 * _VOLLE_PREISE["preis_suche"]


def test_fehlender_suchpreis_laesst_kostenspalte_leer_bei_suchlauf(client, gateway):
    ohne_suchpreis = {**_VOLLE_PREISE, "preis_suche": None}
    client.put("/api/v1/modelle/gpt-5", json=ohne_suchpreis)
    antwort = VorbereiteteAntwort(input_tokens=10, output_tokens=5, web_search_calls=2)

    _, _, zeile = _fuehre_lauf_aus(client, gateway, antwort, web_suche=True)

    assert zeile["web_search_calls"] == 2
    assert zeile["kosten_usd"] is None


def test_vier_preissaetze_je_call_gespeichert_und_im_detail_sichtbar(client, gateway):
    client.put("/api/v1/modelle/gpt-5", json=_VOLLE_PREISE)
    antwort = VorbereiteteAntwort(input_tokens=10, output_tokens=5)

    profil, _, zeile = _fuehre_lauf_aus(client, gateway, antwort)

    detail = client.get(f"/api/v1/call/{zeile['id']}").json()
    assert detail["preise"] == {
        "preis_input": 1.0,
        "preis_cached_input": 0.1,
        "preis_output": 10.0,
        "preis_suche": 25.0,
    }


def test_preisaenderung_im_register_laesst_kosten_und_preisfelder_alter_calls_unveraendert(
    client, gateway
):
    client.put("/api/v1/modelle/gpt-5", json=_VOLLE_PREISE)
    antwort = VorbereiteteAntwort(input_tokens=1_000_000, output_tokens=0)

    _, _, zeile = _fuehre_lauf_aus(client, gateway, antwort)
    urspruengliche_kosten = zeile["kosten_usd"]

    geaenderte_preise = {**_VOLLE_PREISE, "preis_input": 99.0}
    client.put("/api/v1/modelle/gpt-5", json=geaenderte_preise)

    detail_nach_preisaenderung = client.get(f"/api/v1/call/{zeile['id']}").json()
    assert detail_nach_preisaenderung["preise"]["preis_input"] == 1.0
    assert urspruengliche_kosten == 1.0


def test_kosten_neuberechnen_ueberschreibt_preise_und_kosten_aus_aktuellem_register(
    client, gateway
):
    client.put("/api/v1/modelle/gpt-5", json=_VOLLE_PREISE)
    antwort = VorbereiteteAntwort(input_tokens=1_000_000, output_tokens=0)
    profil, lauf, zeile = _fuehre_lauf_aus(client, gateway, antwort)
    assert zeile["kosten_usd"] == 1.0

    korrigierte_preise = {**_VOLLE_PREISE, "preis_input": 2.0}
    client.put("/api/v1/modelle/gpt-5", json=korrigierte_preise)

    response = client.post(f"/api/v1/lauf/{lauf['lauf_id']}/kosten-neuberechnung")

    assert response.status_code == 200
    assert response.json() == {"geaenderte_calls": 1}
    detail = client.get(f"/api/v1/call/{zeile['id']}").json()
    assert detail["preise"]["preis_input"] == 2.0
    neue_zeile = client.get(f"/api/v1/profile/{profil['id']}/calls").json()["calls"][0]
    assert neue_zeile["kosten_usd"] == 2.0


def test_kosten_neuberechnen_auf_unbekanntem_lauf_gibt_404(client):
    response = client.post("/api/v1/lauf/unbekannt/kosten-neuberechnung")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "LAUF_NICHT_GEFUNDEN"


def test_kosten_neuberechnen_auf_laufendem_lauf_wird_abgelehnt(client, gateway):
    profil = _erstelle_profil_mit_arbeitsstand(client)
    gateway.setze_standard(VorbereiteteAntwort(verzoegerung_s=0.3))

    lauf = _starte_lauf(client, profil["id"])
    response = client.post(f"/api/v1/lauf/{lauf['lauf_id']}/kosten-neuberechnung")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "LAUF_LAEUFT_NOCH"
    _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])


def test_aggregat_kosten_summiert_ueber_die_calls_des_laufs(client, gateway):
    client.put("/api/v1/modelle/gpt-5", json=_VOLLE_PREISE)
    profil = _erstelle_profil_mit_arbeitsstand(client, wiederholungen=2)
    gateway.setze_standard(VorbereiteteAntwort(input_tokens=1_000_000, output_tokens=0))

    lauf = _starte_lauf(client, profil["id"])
    daten = _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    laufeintrag = daten["laeufe"][0]
    assert laufeintrag["aggregat"]["kosten_usd"] == 2.0


def test_aggregat_kosten_ist_null_wenn_ein_call_kosten_unbekannt_hat(client, gateway):
    # Kein Preis im Register gepflegt: jeder Call hat kosten_usd None, das Aggregat auch.
    profil = _erstelle_profil_mit_arbeitsstand(client, wiederholungen=2)
    gateway.setze_standard(VorbereiteteAntwort(input_tokens=10, output_tokens=5))

    lauf = _starte_lauf(client, profil["id"])
    daten = _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    laufeintrag = daten["laeufe"][0]
    assert laufeintrag["aggregat"]["kosten_usd"] is None
