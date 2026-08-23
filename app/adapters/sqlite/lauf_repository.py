import sqlite3
from datetime import datetime
from typing import List, Optional

from app.adapters.sqlite.arbeitsstand_mapping import (
    ARBEITSSTAND_SPALTEN,
    arbeitsstand_row_to_domain,
    arbeitsstand_to_params,
)
from app.adapters.sqlite.time_codec import dt_to_text, text_to_dt
from app.domain.models import Lauf


class SqliteLaufRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, lauf: Lauf) -> None:
        params = {
            "id": lauf.id,
            "profil_id": lauf.profil_id,
            "nummer": lauf.nummer,
            "gestartet_am": dt_to_text(lauf.gestartet_am),
            "beendet_am": dt_to_text(lauf.beendet_am) if lauf.beendet_am else None,
            **arbeitsstand_to_params(lauf.arbeitsstand),
        }
        self._connection.execute(
            "INSERT INTO lauf (id, profil_id, nummer, gestartet_am, beendet_am, "
            f"{ARBEITSSTAND_SPALTEN}) "
            "VALUES (:id, :profil_id, :nummer, :gestartet_am, :beendet_am, :system_prompt, "
            ":user_prompt, :tools_json, :modelle, :max_output_tokens, :reasoning_effort, "
            ":web_suche, :search_context_size, :wiederholungen)",
            params,
        )
        self._connection.commit()

    def get(self, lauf_id: str) -> Optional[Lauf]:
        row = self._connection.execute(
            "SELECT * FROM lauf WHERE id = ?", (lauf_id,)
        ).fetchone()
        return _row_to_lauf(row) if row is not None else None

    def list_for_profil(self, profil_id: str) -> List[Lauf]:
        rows = self._connection.execute(
            "SELECT * FROM lauf WHERE profil_id = ? ORDER BY nummer", (profil_id,)
        ).fetchall()
        return [_row_to_lauf(row) for row in rows]

    def next_nummer(self, profil_id: str) -> int:
        row = self._connection.execute(
            "SELECT COALESCE(MAX(nummer), 0) + 1 AS naechste FROM lauf WHERE profil_id = ?",
            (profil_id,),
        ).fetchone()
        return row["naechste"]

    def mark_beendet(self, lauf_id: str, beendet_am: datetime) -> None:
        self._connection.execute(
            "UPDATE lauf SET beendet_am = ? WHERE id = ?",
            (dt_to_text(beendet_am), lauf_id),
        )
        self._connection.commit()


def _row_to_lauf(row: sqlite3.Row) -> Lauf:
    return Lauf(
        id=row["id"],
        profil_id=row["profil_id"],
        nummer=row["nummer"],
        gestartet_am=text_to_dt(row["gestartet_am"]),
        beendet_am=text_to_dt(row["beendet_am"]),
        arbeitsstand=arbeitsstand_row_to_domain(row),
    )
