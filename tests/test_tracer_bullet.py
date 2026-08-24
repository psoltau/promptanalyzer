import json
import time
from typing import Any, Dict

from tests.fakes import VorbereiteteAntwort

STANDARD_ARBEITSSTAND: Dict[str, Any] = {
    "system_prompt": "Du bist hilfreich.",
    "user_prompt": "Sag hallo.",
    "tools_json": None,
    "modelle": ["testmodell"],
    "max_output_tokens": 512,
    "reasoning_effort": None,
    "web_suche": False,
    "search_context_size": None,
    "wiederholungen": 1,
}


def _erstelle_profil(client, name="Testprofil"):
    response = client.post("/api/v1/profile", json={"name": name})
    assert response.status_code == 201
    assert response.headers["location"] == f"/api/v1/profile/{response.json()['id']}"
    return response.json()


def _setze_arbeitsstand(client, profil_id, **overrides):
    body = {**STANDARD_ARBEITSSTAND, **overrides}
    response = client.put(f"/api/v1/profile/{profil_id}/arbeitsstand", json=body)
    assert response.status_code == 200
    return response.json()


def _starte_lauf(client, profil_id, headers=None):
    response = client.post(f"/api/v1/profile/{profil_id}/laeufe", headers=headers or {})
    return response


def _warte_auf_lauf_ende(client, profil_id, lauf_id, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        daten = client.get(f"/api/v1/profile/{profil_id}/calls").json()
        lauf = next(l for l in daten["laeufe"] if l["lauf_id"] == lauf_id)
        if lauf["beendet_am"] is not None:
            return daten
        time.sleep(0.02)
    raise AssertionError("Lauf wurde nicht rechtzeitig beendet")


def test_profil_anlegen_und_auflisten(client):
    _erstelle_profil(client, "Zusammenfasser")

    response = client.get("/api/v1/profile")

    assert response.status_code == 200
    namen = [p["name"] for p in response.json()]
    assert "Zusammenfasser" in namen


def test_neues_profil_hat_leeren_arbeitsstand(client):
    profil = _erstelle_profil(client)

    detail = client.get(f"/api/v1/profile/{profil['id']}").json()

    assert detail["arbeitsstand"]["modelle"] == []
    assert detail["arbeitsstand"]["wiederholungen"] == 1
    assert detail["arbeitsstand"]["web_suche"] is False


def test_leerer_profilname_wird_abgelehnt(client):
    response = client.post("/api/v1/profile", json={"name": "   "})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "NAME_LEER"


def test_profil_nicht_gefunden(client):
    response = client.get("/api/v1/profile/unbekannt")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROFIL_NICHT_GEFUNDEN"


def test_arbeitsstand_ueberlebt_und_zeigt_speicherzeitpunkt(client):
    profil = _erstelle_profil(client)

    antwort = _setze_arbeitsstand(client, profil["id"], system_prompt="Neuer Systemtext")

    assert "arbeitsstand_geaendert_am" in antwort
    geladen = client.get(f"/api/v1/profile/{profil['id']}").json()
    assert geladen["arbeitsstand"]["system_prompt"] == "Neuer Systemtext"
    assert geladen["arbeitsstand_geaendert_am"] == antwort["arbeitsstand_geaendert_am"]


def test_max_output_tokens_und_reasoning_effort_teil_des_arbeitsstands(client):
    profil = _erstelle_profil(client)

    _setze_arbeitsstand(client, profil["id"], max_output_tokens=256, reasoning_effort="high")

    geladen = client.get(f"/api/v1/profile/{profil['id']}").json()
    assert geladen["arbeitsstand"]["max_output_tokens"] == 256
    assert geladen["arbeitsstand"]["reasoning_effort"] == "high"


def test_web_suche_und_search_context_size_teil_des_arbeitsstands(client):
    profil = _erstelle_profil(client)

    _setze_arbeitsstand(client, profil["id"], web_suche=True, search_context_size="high")

    geladen = client.get(f"/api/v1/profile/{profil['id']}").json()
    assert geladen["arbeitsstand"]["web_suche"] is True
    assert geladen["arbeitsstand"]["search_context_size"] == "high"


def test_web_suche_wird_mit_dem_lauf_eingefroren(client, gateway):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"], web_suche=True, search_context_size="high")

    start_antwort = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    _warte_auf_lauf_ende(client, profil["id"], start_antwort["lauf_id"])

    _setze_arbeitsstand(client, profil["id"], web_suche=False, search_context_size=None)

    calls = client.get(f"/api/v1/profile/{profil['id']}/calls").json()
    call_id = calls["calls"][0]["id"]
    detail = client.get(f"/api/v1/call/{call_id}").json()
    assert detail["schnappschuss"]["web_suche"] is True
    assert detail["schnappschuss"]["search_context_size"] == "high"

    geladenes_profil = client.get(f"/api/v1/profile/{profil['id']}").json()
    assert geladenes_profil["arbeitsstand"]["web_suche"] is False


def test_lauf_kehrt_sofort_zurueck_und_call_laeuft_im_hintergrund_weiter(client, gateway):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"])
    gateway.setze_standard(VorbereiteteAntwort(verzoegerung_s=0.3))

    start = time.monotonic()
    response = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"})
    dauer_bis_antwort = time.monotonic() - start

    assert response.status_code == 201
    assert dauer_bis_antwort < 0.3
    body = response.json()
    assert body["nummer"] == 1
    assert body["erwartete_calls"] == 1
    assert response.headers["location"] == f"/api/v1/lauf/{body['lauf_id']}"

    sofort = client.get(f"/api/v1/profile/{profil['id']}/calls").json()
    laufeintrag = sofort["laeufe"][0]
    assert laufeintrag["beendet_am"] is None
    assert laufeintrag["fertige_calls"] == 0

    fertig = _warte_auf_lauf_ende(client, profil["id"], body["lauf_id"])
    laufeintrag = fertig["laeufe"][0]
    assert laufeintrag["fertige_calls"] == 1
    assert laufeintrag["beendet_am"] is not None


def test_lauf_friert_prompt_und_einstellungen_ein(client, gateway):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"], system_prompt="Version A")

    start_antwort = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    _warte_auf_lauf_ende(client, profil["id"], start_antwort["lauf_id"])

    _setze_arbeitsstand(client, profil["id"], system_prompt="Version B")

    calls = client.get(f"/api/v1/profile/{profil['id']}/calls").json()
    call_id = calls["calls"][0]["id"]
    detail = client.get(f"/api/v1/call/{call_id}").json()
    assert detail["schnappschuss"]["system_prompt"] == "Version A"

    geladenes_profil = client.get(f"/api/v1/profile/{profil['id']}").json()
    assert geladenes_profil["arbeitsstand"]["system_prompt"] == "Version B"


def test_einstellungen_in_der_laufuebersicht_ohne_prompt_texte(client):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"], system_prompt="Geheimer Systemtext")

    _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"})

    laufeintrag = client.get(f"/api/v1/profile/{profil['id']}/calls").json()["laeufe"][0]
    assert set(laufeintrag["einstellungen"].keys()) == {
        "modelle",
        "max_output_tokens",
        "reasoning_effort",
        "web_suche",
        "search_context_size",
        "wiederholungen",
    }


def test_tokenposten_getrennt_gespeichert_und_antwort_lesbar(client, gateway):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"])
    gateway.setze_standard(
        VorbereiteteAntwort(
            input_tokens=100,
            cached_input_tokens=20,
            reasoning_tokens=30,
            output_tokens=40,
            total_tokens=170,
            antwort_text="Die gemessene Antwort.",
        )
    )

    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    calls = client.get(f"/api/v1/profile/{profil['id']}/calls").json()
    zeile = calls["calls"][0]
    assert zeile["status"] == "complete"
    assert zeile["input_tokens"] == 100
    assert zeile["cached_input_tokens"] == 20
    assert zeile["reasoning_tokens"] == 30
    assert zeile["output_tokens"] == 40
    assert zeile["total_tokens"] == 170

    detail = client.get(f"/api/v1/call/{zeile['id']}").json()
    assert detail["antwort_text"] == "Die gemessene Antwort."


def test_status_incomplete_mit_gespeichertem_grund(client, gateway):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"])
    gateway.setze_standard(VorbereiteteAntwort(incomplete_grund="max_output_tokens"))

    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    zeile = client.get(f"/api/v1/profile/{profil['id']}/calls").json()["calls"][0]
    assert zeile["status"] == "incomplete"
    assert zeile["incomplete_grund"] == "max_output_tokens"


def test_status_error_mit_fehlertext_und_andere_calls_unberuehrt(client, gateway):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"])
    gateway.setze_standard(VorbereiteteAntwort(fehler="Modell nicht freigeschaltet"))

    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    zeile = client.get(f"/api/v1/profile/{profil['id']}/calls").json()["calls"][0]
    assert zeile["status"] == "error"
    assert zeile["hat_fehler"] is True

    detail = client.get(f"/api/v1/call/{zeile['id']}").json()
    assert detail["fehlertext"] == "Modell nicht freigeschaltet"


def test_dauer_ist_gemessene_wanduhrzeit(client, gateway):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"])
    gateway.setze_standard(VorbereiteteAntwort(verzoegerung_s=0.2))

    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    zeile = client.get(f"/api/v1/profile/{profil['id']}/calls").json()["calls"][0]
    assert zeile["dauer_ms"] >= 190


def test_eingetragener_key_wird_verwendet(client, gateway):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"])

    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-vom-header"}).json()
    _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    assert gateway.verwendete_api_keys == ["sk-vom-header"]


def test_umgebungs_key_greift_wenn_header_fehlt(client, gateway, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-aus-umgebung")
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"])

    lauf = _starte_lauf(client, profil["id"]).json()
    _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    assert gateway.verwendete_api_keys == ["sk-aus-umgebung"]


def test_eingetragener_key_gewinnt_vor_umgebung(client, gateway, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-aus-umgebung")
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"])

    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-vom-header"}).json()
    _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    assert gateway.verwendete_api_keys == ["sk-vom-header"]


def test_key_fehlt_ohne_header_und_ohne_umgebung(client):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"])

    response = _starte_lauf(client, profil["id"])

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "KEY_FEHLT"


def test_kein_modell_gewaehlt(client):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"], modelle=[])

    response = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "KEIN_MODELL_GEWAEHLT"


def test_tools_json_ungueltig_beim_ausfuehren(client):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"], tools_json="{kaputtes json")

    response = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "TOOLS_JSON_UNGUELTIG"


def test_kaputtes_tools_json_wird_beim_speichern_nicht_abgelehnt(client):
    profil = _erstelle_profil(client)

    antwort = _setze_arbeitsstand(client, profil["id"], tools_json="{kaputtes json")

    assert "arbeitsstand_geaendert_am" in antwort


def test_call_nicht_gefunden(client):
    response = client.get("/api/v1/call/unbekannt")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CALL_NICHT_GEFUNDEN"


def test_fehlerantwort_hat_standard_envelope(client):
    response = client.get("/api/v1/profile/unbekannt")

    error = response.json()["error"]
    assert set(error.keys()) == {"code", "message", "traceId"}
    assert error["code"] == error["code"].upper()


def test_key_status_meldet_keinen_umgebungs_key_ohne_env(client):
    response = client.get("/api/v1/key-status")

    assert response.status_code == 200
    assert response.json() == {"umgebungs_key_vorhanden": False}


def test_key_status_meldet_umgebungs_key_wenn_gesetzt(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-aus-umgebung")

    response = client.get("/api/v1/key-status")

    assert response.json() == {"umgebungs_key_vorhanden": True}


# Key-Dichtheit (ADR 0008): darf nie ersatzlos gelöscht werden, siehe
# docs/adr/0008-key-dichtheit-als-dauerhafte-garantie.md.
def test_key_dichtheit_kein_key_in_irgendeiner_spalte(client, gateway):
    header_key = "sk-header-geheimnis-1234567890"
    prompt_key = "sk-im-prompt-getippt-abcdef123456"
    antwort_key = "sk-in-der-antwort-zurueckgegeben"
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"], user_prompt=f"Mein Key ist {prompt_key}. Sag hallo.")
    gateway.setze_standard(VorbereiteteAntwort(antwort_text=f"Verstanden: {antwort_key}"))

    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": header_key}).json()
    _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    calls = client.get(f"/api/v1/profile/{profil['id']}/calls").json()
    call_id = calls["calls"][0]["id"]
    detail = client.get(f"/api/v1/call/{call_id}").json()
    profil_detail = client.get(f"/api/v1/profile/{profil['id']}").json()

    for antwort in (calls, detail, profil_detail):
        text = json.dumps(antwort)
        assert header_key not in text
        assert prompt_key not in text
        assert antwort_key not in text
