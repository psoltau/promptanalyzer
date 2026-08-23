import sqlite3
from datetime import datetime
from typing import List, Optional

from app.adapters.sqlite.arbeitsstand_mapping import (
    ARBEITSSTAND_SPALTEN,
    arbeitsstand_row_to_domain,
    arbeitsstand_to_params,
)
from app.adapters.sqlite.time_codec import dt_to_text, text_to_dt
from app.domain.models import Arbeitsstand, Profil, ProfilUebersicht

_UEBERSICHT_SQL = """
SELECT p.id, p.name, p.erstellt_am, p.arbeitsstand_geaendert_am,
       COUNT(l.id) AS anzahl_laeufe, MAX(l.gestartet_am) AS zuletzt_benutzt_am
FROM profil p
LEFT JOIN lauf l ON l.profil_id = p.id
GROUP BY p.id
ORDER BY p.erstellt_am
"""


class SqliteProfilRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, profil: Profil) -> None:
        params = {
            "id": profil.id,
            "name": profil.name,
            "erstellt_am": dt_to_text(profil.erstellt_am),
            "arbeitsstand_geaendert_am": dt_to_text(profil.arbeitsstand_geaendert_am),
            **arbeitsstand_to_params(profil.arbeitsstand),
        }
        self._connection.execute(
            f"INSERT INTO profil (id, name, erstellt_am, arbeitsstand_geaendert_am, {ARBEITSSTAND_SPALTEN}) "
            f"VALUES (:id, :name, :erstellt_am, :arbeitsstand_geaendert_am, :system_prompt, :user_prompt, "
            f":tools_json, :modelle, :max_output_tokens, :reasoning_effort, :web_suche, "
            f":search_context_size, :wiederholungen)",
            params,
        )
        self._connection.commit()

    def get(self, profil_id: str) -> Optional[Profil]:
        row = self._connection.execute(
            "SELECT * FROM profil WHERE id = ?", (profil_id,)
        ).fetchone()
        return _row_to_profil(row) if row is not None else None

    def list_uebersicht(self) -> List[ProfilUebersicht]:
        rows = self._connection.execute(_UEBERSICHT_SQL).fetchall()
        return [_row_to_uebersicht(row) for row in rows]

    def save_arbeitsstand(
        self, profil_id: str, arbeitsstand: Arbeitsstand, geaendert_am: datetime
    ) -> None:
        params = {
            "id": profil_id,
            "geaendert_am": dt_to_text(geaendert_am),
            **arbeitsstand_to_params(arbeitsstand),
        }
        self._connection.execute(
            "UPDATE profil SET arbeitsstand_geaendert_am = :geaendert_am, "
            "system_prompt = :system_prompt, user_prompt = :user_prompt, tools_json = :tools_json, "
            "modelle = :modelle, max_output_tokens = :max_output_tokens, "
            "reasoning_effort = :reasoning_effort, web_suche = :web_suche, "
            "search_context_size = :search_context_size, wiederholungen = :wiederholungen "
            "WHERE id = :id",
            params,
        )
        self._connection.commit()


def _row_to_profil(row: sqlite3.Row) -> Profil:
    return Profil(
        id=row["id"],
        name=row["name"],
        erstellt_am=text_to_dt(row["erstellt_am"]),
        arbeitsstand_geaendert_am=text_to_dt(row["arbeitsstand_geaendert_am"]),
        arbeitsstand=arbeitsstand_row_to_domain(row),
    )


def _row_to_uebersicht(row: sqlite3.Row) -> ProfilUebersicht:
    return ProfilUebersicht(
        id=row["id"],
        name=row["name"],
        erstellt_am=text_to_dt(row["erstellt_am"]),
        arbeitsstand_geaendert_am=text_to_dt(row["arbeitsstand_geaendert_am"]),
        anzahl_laeufe=row["anzahl_laeufe"],
        zuletzt_benutzt_am=text_to_dt(row["zuletzt_benutzt_am"]),
    )
