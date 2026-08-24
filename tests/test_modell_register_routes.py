import time
from typing import Any, Dict

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
    "preis_input": 1.25,
    "preis_cached_input": 0.125,
    "preis_output": 10.0,
    "preis_suche": None,
    "kontextfenster": 400000,
    "erlaubt_reasoning_effort": False,
    "erlaubt_web_suche": False,
    "unterstuetzt_prompt_caching": False,
}


def _warte_auf_lauf_ende(client, profil_id, lauf_id, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        daten = client.get(f"/api/v1/profile/{profil_id}/calls").json()
        lauf = next(l for l in daten["laeufe"] if l["lauf_id"] == lauf_id)
        if lauf["beendet_am"] is not None:
            return daten
        time.sleep(0.02)
    raise AssertionError("Lauf wurde nicht rechtzeitig beendet")


def test_register_hat_beim_ersten_start_die_saatliste_mit_leeren_preisen(client):
    response = client.get("/api/v1/modelle")

    assert response.status_code == 200
    modelle = response.json()
    assert len(modelle) >= 6
    namen = {m["name"] for m in modelle}
    assert "gpt-5" in namen
    assert "o4-mini" in namen
    for modell in modelle:
        assert modell["preis_input"] is None
        assert modell["preis_cached_input"] is None
        assert modell["preis_output"] is None
        assert modell["preis_suche"] is None
        assert modell["preise_vollstaendig"] is False


def test_seed_modell_erlaubt_alle_faehigkeiten(client):
    modelle = client.get("/api/v1/modelle").json()

    for modell in modelle:
        assert modell["erlaubt_reasoning_effort"] is True
        assert modell["erlaubt_web_suche"] is True
        assert modell["unterstuetzt_prompt_caching"] is True


def test_modell_anlegen_braucht_nur_einen_namen(client):
    response = client.post("/api/v1/modelle", json={"name": "gpt-5.1"})

    assert response.status_code == 201
    assert response.headers["location"] == "/api/v1/modelle/gpt-5.1"
    modell = response.json()
    assert modell["name"] == "gpt-5.1"
    assert modell["preis_input"] is None
    assert modell["kontextfenster"] is None
    assert modell["erlaubt_reasoning_effort"] is True
    assert modell["erlaubt_web_suche"] is True
    assert modell["unterstuetzt_prompt_caching"] is True


def test_modell_anlegen_mit_vergebenem_namen_wird_abgelehnt(client):
    client.post("/api/v1/modelle", json={"name": "gpt-5.1"})

    response = client.post("/api/v1/modelle", json={"name": "gpt-5.1"})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "MODELL_NAME_VERGEBEN"


def test_modell_aktualisieren_schreibt_preise_kontextfenster_und_faehigkeiten(client):
    client.post("/api/v1/modelle", json={"name": "gpt-5.1"})

    response = client.put("/api/v1/modelle/gpt-5.1", json=_VOLLE_PREISE)

    assert response.status_code == 200
    modell = response.json()
    assert modell["preis_input"] == 1.25
    assert modell["preis_cached_input"] == 0.125
    assert modell["preis_output"] == 10.0
    assert modell["kontextfenster"] == 400000
    assert modell["erlaubt_reasoning_effort"] is False
    assert modell["erlaubt_web_suche"] is False
    assert modell["unterstuetzt_prompt_caching"] is False
    assert modell["preise_vollstaendig"] is True

    geladen = client.get("/api/v1/modelle").json()
    persistiert = next(m for m in geladen if m["name"] == "gpt-5.1")
    assert persistiert == modell


def test_modell_aktualisieren_unbekannt_gibt_404(client):
    response = client.put("/api/v1/modelle/nicht-registriert", json=_VOLLE_PREISE)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MODELL_NICHT_GEFUNDEN"


def test_modell_loeschen_gibt_204_und_entfernt_es_aus_der_liste(client):
    client.post("/api/v1/modelle", json={"name": "gpt-5.1"})

    response = client.delete("/api/v1/modelle/gpt-5.1")

    assert response.status_code == 204
    namen = {m["name"] for m in client.get("/api/v1/modelle").json()}
    assert "gpt-5.1" not in namen


def test_modell_loeschen_unbekannt_gibt_404(client):
    response = client.delete("/api/v1/modelle/nicht-registriert")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MODELL_NICHT_GEFUNDEN"


def test_modell_loeschen_laesst_bestehende_calls_unveraendert(client):
    profil = client.post("/api/v1/profile", json={"name": "Testprofil"}).json()
    client.put(f"/api/v1/profile/{profil['id']}/arbeitsstand", json=STANDARD_ARBEITSSTAND)
    lauf = client.post(
        f"/api/v1/profile/{profil['id']}/laeufe", headers={"X-OpenAI-Key": "sk-test"}
    ).json()
    _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    response = client.delete("/api/v1/modelle/gpt-5")
    assert response.status_code == 204

    calls = client.get(f"/api/v1/profile/{profil['id']}/calls").json()["calls"]
    assert calls[0]["modell_name"] == "gpt-5"
