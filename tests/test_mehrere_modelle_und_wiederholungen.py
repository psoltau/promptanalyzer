import time

from tests.fakes import VorbereiteteAntwort
from tests.test_tracer_bullet import (
    _erstelle_profil,
    _setze_arbeitsstand,
    _starte_lauf,
    _warte_auf_lauf_ende,
)


def test_wiederholungen_erzeugen_calls_mit_fortlaufendem_index_ab_eins(client, gateway):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"], modelle=["gpt-5"], wiederholungen=3)

    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    assert lauf["erwartete_calls"] == 3
    daten = _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    indizes = sorted(call["wiederholung_index"] for call in daten["calls"])
    assert indizes == [1, 2, 3]
    assert all(call["modell_name"] == "gpt-5" for call in daten["calls"])


def test_modelle_mal_wiederholungen_ergibt_richtige_call_anzahl_und_indizes(client, gateway):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(
        client, profil["id"], modelle=["gpt-5", "o4-mini"], wiederholungen=2
    )

    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    assert lauf["erwartete_calls"] == 4
    daten = _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    laufeintrag = daten["laeufe"][0]
    assert laufeintrag["fertige_calls"] == 4
    assert laufeintrag["aggregat"]["anzahl_calls"] == 4

    def indizes_fuer(modell_name):
        return sorted(
            call["wiederholung_index"] for call in daten["calls"] if call["modell_name"] == modell_name
        )

    assert indizes_fuer("gpt-5") == [1, 2]
    assert indizes_fuer("o4-mini") == [1, 2]


def test_verschiedene_modelle_werden_gleichzeitig_angefragt(client, gateway):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"], modelle=["gpt-5", "o4-mini"], wiederholungen=1)
    gateway.setze_standard(VorbereiteteAntwort(verzoegerung_s=0.25))

    start = time.monotonic()
    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])
    dauer = time.monotonic() - start

    # Liefen beide Modelle nacheinander, bräuchte es mindestens 0.5s; überlappend deutlich
    # darunter. Das ist die einzige über HTTP beobachtbare Art, Überlappung zu belegen.
    assert dauer < 0.45
    assert gateway.max_gleichzeitige_modelle >= 2


def test_wiederholungen_eines_modells_laufen_streng_seriell_auch_neben_anderen_modellen(
    client, gateway
):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(
        client, profil["id"], modelle=["gpt-5", "o4-mini"], wiederholungen=4
    )
    gateway.setze_standard(VorbereiteteAntwort(verzoegerung_s=0.02))

    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    daten = _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"], timeout=5.0)

    assert daten["laeufe"][0]["fertige_calls"] == 8
    assert gateway.wiederholung_ueberlappung is False


def test_fehler_in_einem_modell_erzeugt_error_zeile_andere_modelle_unberuehrt(client, gateway):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(
        client, profil["id"], modelle=["gpt-5", "kaputtes-modell"], wiederholungen=2
    )
    gateway.antworte_mit("kaputtes-modell", VorbereiteteAntwort(fehler="Modell nicht freigeschaltet"))
    gateway.antworte_mit("kaputtes-modell", VorbereiteteAntwort(fehler="Modell nicht freigeschaltet"))
    gateway.setze_standard(VorbereiteteAntwort(antwort_text="ok"))

    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    daten = _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    laufeintrag = daten["laeufe"][0]
    assert laufeintrag["beendet_am"] is not None
    assert laufeintrag["fertige_calls"] == 4

    kaputte_calls = [c for c in daten["calls"] if c["modell_name"] == "kaputtes-modell"]
    gute_calls = [c for c in daten["calls"] if c["modell_name"] == "gpt-5"]
    assert len(kaputte_calls) == 2
    assert all(c["status"] == "error" and c["hat_fehler"] for c in kaputte_calls)
    assert len(gute_calls) == 2
    assert all(c["status"] == "complete" for c in gute_calls)

    fehler_call_id = kaputte_calls[0]["id"]
    detail = client.get(f"/api/v1/call/{fehler_call_id}").json()
    assert detail["fehlertext"] == "Modell nicht freigeschaltet"


def test_aggregatzeile_summiert_ueber_alle_modelle_und_wiederholungen_eines_laufs(client, gateway):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"], modelle=["gpt-5", "o4-mini"], wiederholungen=2)
    gateway.setze_standard(
        VorbereiteteAntwort(input_tokens=100, cached_input_tokens=0, output_tokens=50, total_tokens=150)
    )

    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    daten = _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    aggregat = daten["laeufe"][0]["aggregat"]
    assert aggregat["anzahl_calls"] == 4
    assert aggregat["input_tokens"] == 400
    assert aggregat["output_tokens"] == 200
    assert aggregat["total_tokens"] == 600
