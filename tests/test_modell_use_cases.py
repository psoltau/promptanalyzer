import pytest

from app.application.modell_use_cases import (
    create_modell,
    delete_modell,
    list_modelle,
    update_modell,
)
from app.domain.errors import ModellNameVergeben, ModellNichtGefunden
from app.domain.models import Modell
from tests.fakes import FakeModellRepository


@pytest.fixture
def repo() -> FakeModellRepository:
    return FakeModellRepository()


def test_create_modell_braucht_nur_einen_namen_und_erlaubt_alles(repo: FakeModellRepository):
    modell = create_modell("gpt-5.1", repo)

    assert modell.name == "gpt-5.1"
    assert modell.preis_input is None
    assert modell.preis_cached_input is None
    assert modell.preis_output is None
    assert modell.preis_suche is None
    assert modell.kontextfenster is None
    assert modell.erlaubt_reasoning_effort is True
    assert modell.erlaubt_web_suche is True
    assert modell.unterstuetzt_prompt_caching is True


def test_create_modell_landet_im_register(repo: FakeModellRepository):
    create_modell("gpt-5.1", repo)

    assert [m.name for m in list_modelle(repo)] == ["gpt-5.1"]


def test_create_modell_mit_vergebenem_namen_wird_abgelehnt(repo: FakeModellRepository):
    create_modell("gpt-5.1", repo)

    with pytest.raises(ModellNameVergeben):
        create_modell("gpt-5.1", repo)


def test_update_modell_schreibt_preise_kontextfenster_und_faehigkeiten(
    repo: FakeModellRepository,
):
    create_modell("gpt-5.1", repo)
    aktualisiert = Modell(
        name="gpt-5.1",
        preis_input=1.25,
        preis_cached_input=0.125,
        preis_output=10.0,
        preis_suche=25.0,
        kontextfenster=400000,
        erlaubt_reasoning_effort=False,
        erlaubt_web_suche=False,
        unterstuetzt_prompt_caching=False,
    )

    ergebnis = update_modell(aktualisiert, repo)

    assert ergebnis == aktualisiert
    assert repo.get("gpt-5.1") == aktualisiert


def test_update_modell_aendert_keinen_anderen_eintrag(repo: FakeModellRepository):
    create_modell("gpt-5.1", repo)
    create_modell("o4-mini", repo)

    update_modell(
        Modell(
            name="gpt-5.1",
            preis_input=1.0,
            preis_cached_input=0.1,
            preis_output=5.0,
            preis_suche=None,
            kontextfenster=100000,
            erlaubt_reasoning_effort=True,
            erlaubt_web_suche=True,
            unterstuetzt_prompt_caching=True,
        ),
        repo,
    )

    assert repo.get("o4-mini").preis_input is None


def test_update_unbekanntes_modell_wird_abgelehnt(repo: FakeModellRepository):
    unbekannt = Modell(
        name="nicht-registriert",
        preis_input=None,
        preis_cached_input=None,
        preis_output=None,
        preis_suche=None,
        kontextfenster=None,
        erlaubt_reasoning_effort=True,
        erlaubt_web_suche=True,
        unterstuetzt_prompt_caching=True,
    )

    with pytest.raises(ModellNichtGefunden):
        update_modell(unbekannt, repo)


def test_delete_modell_entfernt_es_aus_dem_register(repo: FakeModellRepository):
    create_modell("gpt-5.1", repo)

    delete_modell("gpt-5.1", repo)

    assert list_modelle(repo) == []


def test_delete_unbekanntes_modell_wird_abgelehnt(repo: FakeModellRepository):
    with pytest.raises(ModellNichtGefunden):
        delete_modell("nicht-registriert", repo)
