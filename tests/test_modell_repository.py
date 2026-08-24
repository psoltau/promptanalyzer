import sqlite3

import pytest

from app.adapters.sqlite.modell_repository import SqliteModellRepository
from app.adapters.sqlite.schema import ensure_schema, seed_modell_register_if_empty
from app.domain.models import Modell


@pytest.fixture
def connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return conn


@pytest.fixture
def repo(connection: sqlite3.Connection) -> SqliteModellRepository:
    return SqliteModellRepository(connection)


def _neues_modell(name: str = "gpt-5.1") -> Modell:
    return Modell(
        name=name,
        preis_input=None,
        preis_cached_input=None,
        preis_output=None,
        preis_suche=None,
        kontextfenster=None,
        erlaubt_reasoning_effort=True,
        erlaubt_web_suche=True,
        unterstuetzt_prompt_caching=True,
    )


def test_add_und_get_liefern_dasselbe_modell(repo: SqliteModellRepository):
    modell = _neues_modell()

    repo.add(modell)

    assert repo.get("gpt-5.1") == modell


def test_get_unbekanntes_modell_liefert_none(repo: SqliteModellRepository):
    assert repo.get("nicht-registriert") is None


def test_list_liefert_alle_modelle_alphabetisch(repo: SqliteModellRepository):
    repo.add(_neues_modell("o4-mini"))
    repo.add(_neues_modell("gpt-5"))

    namen = [m.name for m in repo.list()]

    assert namen == ["gpt-5", "o4-mini"]


def test_update_schreibt_preise_kontextfenster_und_faehigkeiten(repo: SqliteModellRepository):
    repo.add(_neues_modell())
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

    repo.update(aktualisiert)

    assert repo.get("gpt-5.1") == aktualisiert


def test_delete_entfernt_das_modell(repo: SqliteModellRepository):
    repo.add(_neues_modell())

    repo.delete("gpt-5.1")

    assert repo.get("gpt-5.1") is None


def test_seed_befuellt_ein_leeres_register_mit_leeren_preisen(connection: sqlite3.Connection):
    seed_modell_register_if_empty(connection)

    modelle = SqliteModellRepository(connection).list()

    namen = {m.name for m in modelle}
    assert "gpt-5" in namen
    assert "o4-mini" in namen
    assert all(m.preis_input is None for m in modelle)
    assert all(m.preis_cached_input is None for m in modelle)
    assert all(m.preis_output is None for m in modelle)
    assert all(m.preis_suche is None for m in modelle)
    assert all(m.kontextfenster is None for m in modelle)


def test_seed_ueberspringt_ein_bereits_befuelltes_register(connection: sqlite3.Connection):
    repo = SqliteModellRepository(connection)
    repo.add(_neues_modell("von-hand-angelegt"))

    seed_modell_register_if_empty(connection)

    namen = [m.name for m in repo.list()]
    assert namen == ["von-hand-angelegt"]


def test_erneutes_schema_setup_dupliziert_und_ueberschreibt_vorhandene_saatdaten_nicht(
    connection: sqlite3.Connection,
):
    repo = SqliteModellRepository(connection)
    repo.add(_neues_modell("von-hand-angelegt"))
    seed_modell_register_if_empty(connection)
    assert [m.name for m in repo.list()] == ["von-hand-angelegt"]

    ensure_schema(connection)
    seed_modell_register_if_empty(connection)

    assert [m.name for m in repo.list()] == ["von-hand-angelegt"]
