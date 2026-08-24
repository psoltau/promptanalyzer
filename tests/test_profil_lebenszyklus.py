from tests.test_tracer_bullet import (
    _erstelle_profil,
    _setze_arbeitsstand,
    _starte_lauf,
    _warte_auf_lauf_ende,
)


def test_profil_umbenennen(client):
    profil = _erstelle_profil(client, "Alter Name")

    response = client.patch(f"/api/v1/profile/{profil['id']}", json={"name": "Neuer Name"})

    assert response.status_code == 200
    assert response.json()["name"] == "Neuer Name"
    geladen = client.get(f"/api/v1/profile/{profil['id']}").json()
    assert geladen["name"] == "Neuer Name"


def test_profil_umbenennen_beruehrt_keinen_lauf(client, gateway):
    profil = _erstelle_profil(client, "Alter Name")
    _setze_arbeitsstand(client, profil["id"])
    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    client.patch(f"/api/v1/profile/{profil['id']}", json={"name": "Neuer Name"})

    calls = client.get(f"/api/v1/profile/{profil['id']}/calls").json()
    call_id = calls["calls"][0]["id"]
    detail = client.get(f"/api/v1/call/{call_id}").json()
    assert detail["lauf_nummer"] == 1


def test_profil_umbenennen_mit_leerem_namen_wird_abgelehnt(client):
    profil = _erstelle_profil(client)

    response = client.patch(f"/api/v1/profile/{profil['id']}", json={"name": "   "})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "NAME_LEER"


def test_unbekanntes_profil_umbenennen(client):
    response = client.patch("/api/v1/profile/unbekannt", json={"name": "Irgendwas"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROFIL_NICHT_GEFUNDEN"


def test_profil_loeschen_entfernt_es_aus_der_liste(client):
    profil = _erstelle_profil(client, "Zum Löschen")

    response = client.delete(f"/api/v1/profile/{profil['id']}")

    assert response.status_code == 204
    namen = [p["name"] for p in client.get("/api/v1/profile").json()]
    assert "Zum Löschen" not in namen


def test_profil_loeschen_nimmt_laeufe_und_calls_mit(client, gateway):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"])
    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])
    calls = client.get(f"/api/v1/profile/{profil['id']}/calls").json()
    call_id = calls["calls"][0]["id"]

    client.delete(f"/api/v1/profile/{profil['id']}")

    assert client.get(f"/api/v1/profile/{profil['id']}").status_code == 404
    assert client.get(f"/api/v1/call/{call_id}").status_code == 404


def test_unbekanntes_profil_loeschen(client):
    response = client.delete("/api/v1/profile/unbekannt")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROFIL_NICHT_GEFUNDEN"


def test_profil_liste_zeigt_anzahl_laeufe_und_letzte_benutzung(client, gateway):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"])

    vor_lauf = next(p for p in client.get("/api/v1/profile").json() if p["id"] == profil["id"])
    assert vor_lauf["anzahl_laeufe"] == 0
    assert vor_lauf["zuletzt_benutzt_am"] is None

    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    nach_lauf = next(p for p in client.get("/api/v1/profile").json() if p["id"] == profil["id"])
    assert nach_lauf["anzahl_laeufe"] == 1
    assert nach_lauf["zuletzt_benutzt_am"] is not None


def test_profil_duplizieren_uebernimmt_arbeitsstand_und_historie(client, gateway):
    profil = _erstelle_profil(client, "Original")
    _setze_arbeitsstand(client, profil["id"], system_prompt="Wichtiger Systemtext")
    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    response = client.post(f"/api/v1/profile/{profil['id']}/duplikat")

    assert response.status_code == 201
    duplikat = response.json()
    assert response.headers["location"] == f"/api/v1/profile/{duplikat['id']}"
    assert duplikat["id"] != profil["id"]
    assert duplikat["arbeitsstand"]["system_prompt"] == "Wichtiger Systemtext"

    duplikat_calls = client.get(f"/api/v1/profile/{duplikat['id']}/calls").json()
    assert len(duplikat_calls["laeufe"]) == 1
    assert duplikat_calls["laeufe"][0]["nummer"] == 1
    assert len(duplikat_calls["calls"]) == 1

    original_calls = client.get(f"/api/v1/profile/{profil['id']}/calls").json()
    assert len(original_calls["calls"]) == 1
    assert duplikat_calls["calls"][0]["id"] != original_calls["calls"][0]["id"]


def test_profil_duplizieren_mit_eigenem_namen(client):
    profil = _erstelle_profil(client, "Original")

    response = client.post(
        f"/api/v1/profile/{profil['id']}/duplikat", json={"name": "Zweite Richtung"}
    )

    assert response.json()["name"] == "Zweite Richtung"


def test_profil_duplizieren_ohne_namen_leitet_einen_ab(client):
    profil = _erstelle_profil(client, "Original")

    response = client.post(f"/api/v1/profile/{profil['id']}/duplikat")

    assert response.json()["name"] != "Original"
    assert "Original" in response.json()["name"]


def test_original_bleibt_nach_duplizieren_unveraendert(client, gateway):
    profil = _erstelle_profil(client, "Original")
    _setze_arbeitsstand(client, profil["id"], system_prompt="Version A")
    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    client.post(f"/api/v1/profile/{profil['id']}/duplikat", json={"name": "Kopie"})

    original = client.get(f"/api/v1/profile/{profil['id']}").json()
    assert original["name"] == "Original"
    assert original["arbeitsstand"]["system_prompt"] == "Version A"
    original_calls = client.get(f"/api/v1/profile/{profil['id']}/calls").json()
    assert len(original_calls["calls"]) == 1


def test_unbekanntes_profil_duplizieren(client):
    response = client.post("/api/v1/profile/unbekannt/duplikat")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROFIL_NICHT_GEFUNDEN"


def test_aus_lauf_uebernehmen_kopiert_schnappschuss_in_arbeitsstand(client, gateway):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"], system_prompt="Version A")
    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])
    _setze_arbeitsstand(client, profil["id"], system_prompt="Version B (aktueller Entwurf)")

    response = client.post(
        f"/api/v1/profile/{profil['id']}/arbeitsstand/aus-lauf/{lauf['lauf_id']}"
    )

    assert response.status_code == 200
    assert response.json()["system_prompt"] == "Version A"
    geladen = client.get(f"/api/v1/profile/{profil['id']}").json()
    assert geladen["arbeitsstand"]["system_prompt"] == "Version A"


def test_aus_lauf_uebernehmen_laesst_den_lauf_unveraendert(client, gateway):
    profil = _erstelle_profil(client)
    _setze_arbeitsstand(client, profil["id"], system_prompt="Version A")
    lauf = _starte_lauf(client, profil["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    _warte_auf_lauf_ende(client, profil["id"], lauf["lauf_id"])

    client.post(f"/api/v1/profile/{profil['id']}/arbeitsstand/aus-lauf/{lauf['lauf_id']}")
    _setze_arbeitsstand(client, profil["id"], system_prompt="Version C")
    client.post(f"/api/v1/profile/{profil['id']}/arbeitsstand/aus-lauf/{lauf['lauf_id']}")

    calls = client.get(f"/api/v1/profile/{profil['id']}/calls").json()
    call_id = calls["calls"][0]["id"]
    detail = client.get(f"/api/v1/call/{call_id}").json()
    assert detail["schnappschuss"]["system_prompt"] == "Version A"


def test_aus_unbekanntem_lauf_uebernehmen(client):
    profil = _erstelle_profil(client)

    response = client.post(
        f"/api/v1/profile/{profil['id']}/arbeitsstand/aus-lauf/unbekannt"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "LAUF_NICHT_GEFUNDEN"


def test_aus_lauf_eines_anderen_profils_uebernehmen_schlaegt_fehl(client, gateway):
    profil_a = _erstelle_profil(client, "Profil A")
    _setze_arbeitsstand(client, profil_a["id"])
    lauf = _starte_lauf(client, profil_a["id"], headers={"X-OpenAI-Key": "sk-test"}).json()
    _warte_auf_lauf_ende(client, profil_a["id"], lauf["lauf_id"])
    profil_b = _erstelle_profil(client, "Profil B")

    response = client.post(
        f"/api/v1/profile/{profil_b['id']}/arbeitsstand/aus-lauf/{lauf['lauf_id']}"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "LAUF_NICHT_GEFUNDEN"


def test_aus_lauf_uebernehmen_fuer_unbekanntes_profil(client):
    response = client.post("/api/v1/profile/unbekannt/arbeitsstand/aus-lauf/auch-unbekannt")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROFIL_NICHT_GEFUNDEN"
