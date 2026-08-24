import sqlite3
from typing import Dict, List, Optional

from app.domain.models import Modell

_INSERT_SQL = (
    "INSERT INTO modell ("
    "name, preis_input, preis_cached_input, preis_output, preis_suche, kontextfenster, "
    "erlaubt_reasoning_effort, erlaubt_web_suche, unterstuetzt_prompt_caching"
    ") VALUES ("
    ":name, :preis_input, :preis_cached_input, :preis_output, :preis_suche, :kontextfenster, "
    ":erlaubt_reasoning_effort, :erlaubt_web_suche, :unterstuetzt_prompt_caching)"
)

_UPDATE_SQL = (
    "UPDATE modell SET preis_input = :preis_input, preis_cached_input = :preis_cached_input, "
    "preis_output = :preis_output, preis_suche = :preis_suche, kontextfenster = :kontextfenster, "
    "erlaubt_reasoning_effort = :erlaubt_reasoning_effort, "
    "erlaubt_web_suche = :erlaubt_web_suche, "
    "unterstuetzt_prompt_caching = :unterstuetzt_prompt_caching "
    "WHERE name = :name"
)


class SqliteModellRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, modell: Modell) -> None:
        self._connection.execute(_INSERT_SQL, _modell_to_params(modell))
        self._connection.commit()

    def get(self, name: str) -> Optional[Modell]:
        row = self._connection.execute(
            "SELECT * FROM modell WHERE name = ?", (name,)
        ).fetchone()
        return _row_to_modell(row) if row is not None else None

    def list(self) -> List[Modell]:
        rows = self._connection.execute("SELECT * FROM modell ORDER BY name").fetchall()
        return [_row_to_modell(row) for row in rows]

    def update(self, modell: Modell) -> None:
        self._connection.execute(_UPDATE_SQL, _modell_to_params(modell))
        self._connection.commit()

    def delete(self, name: str) -> None:
        self._connection.execute("DELETE FROM modell WHERE name = ?", (name,))
        self._connection.commit()


def _modell_to_params(modell: Modell) -> Dict[str, object]:
    return {
        "name": modell.name,
        "preis_input": modell.preis_input,
        "preis_cached_input": modell.preis_cached_input,
        "preis_output": modell.preis_output,
        "preis_suche": modell.preis_suche,
        "kontextfenster": modell.kontextfenster,
        "erlaubt_reasoning_effort": int(modell.erlaubt_reasoning_effort),
        "erlaubt_web_suche": int(modell.erlaubt_web_suche),
        "unterstuetzt_prompt_caching": int(modell.unterstuetzt_prompt_caching),
    }


def _row_to_modell(row: sqlite3.Row) -> Modell:
    return Modell(
        name=row["name"],
        preis_input=row["preis_input"],
        preis_cached_input=row["preis_cached_input"],
        preis_output=row["preis_output"],
        preis_suche=row["preis_suche"],
        kontextfenster=row["kontextfenster"],
        erlaubt_reasoning_effort=bool(row["erlaubt_reasoning_effort"]),
        erlaubt_web_suche=bool(row["erlaubt_web_suche"]),
        unterstuetzt_prompt_caching=bool(row["unterstuetzt_prompt_caching"]),
    )
