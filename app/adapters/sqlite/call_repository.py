import sqlite3
from typing import Any, Dict, List, Optional

from app.adapters.sqlite.time_codec import text_to_dt
from app.domain.models import Call, CallStatus

_SPALTEN = (
    "id, lauf_id, modell_name, wiederholung_index, status, incomplete_grund, fehlertext, "
    "dauer_ms, input_tokens, cached_input_tokens, reasoning_tokens, output_tokens, "
    "total_tokens, web_search_calls, antwort_text, request_json, response_json, erstellt_am"
)


class SqliteCallRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, call: Call) -> None:
        params = _call_to_params(call)
        self._connection.execute(
            f"INSERT INTO call ({_SPALTEN}) VALUES "
            "(:id, :lauf_id, :modell_name, :wiederholung_index, :status, :incomplete_grund, "
            ":fehlertext, :dauer_ms, :input_tokens, :cached_input_tokens, :reasoning_tokens, "
            ":output_tokens, :total_tokens, :web_search_calls, :antwort_text, :request_json, "
            ":response_json, :erstellt_am)",
            params,
        )
        self._connection.commit()

    def get(self, call_id: str) -> Optional[Call]:
        row = self._connection.execute(
            "SELECT * FROM call WHERE id = ?", (call_id,)
        ).fetchone()
        return _row_to_call(row) if row is not None else None

    def list_for_profil(self, profil_id: str) -> List[Call]:
        rows = self._connection.execute(
            "SELECT call.* FROM call "
            "JOIN lauf ON lauf.id = call.lauf_id "
            "WHERE lauf.profil_id = ? "
            "ORDER BY call.erstellt_am",
            (profil_id,),
        ).fetchall()
        return [_row_to_call(row) for row in rows]


def _call_to_params(call: Call) -> Dict[str, Any]:
    return {
        "id": call.id,
        "lauf_id": call.lauf_id,
        "modell_name": call.modell_name,
        "wiederholung_index": call.wiederholung_index,
        "status": call.status.value,
        "incomplete_grund": call.incomplete_grund,
        "fehlertext": call.fehlertext,
        "dauer_ms": call.dauer_ms,
        "antwort_text": call.antwort_text,
        "request_json": call.request_json,
        "response_json": call.response_json,
        "erstellt_am": call.erstellt_am.isoformat(),
        **_token_params(call),
    }


def _token_params(call: Call) -> Dict[str, Any]:
    return {
        "input_tokens": call.input_tokens,
        "cached_input_tokens": call.cached_input_tokens,
        "reasoning_tokens": call.reasoning_tokens,
        "output_tokens": call.output_tokens,
        "total_tokens": call.total_tokens,
        "web_search_calls": call.web_search_calls,
    }


def _row_to_call(row: sqlite3.Row) -> Call:
    return Call(
        id=row["id"],
        lauf_id=row["lauf_id"],
        modell_name=row["modell_name"],
        wiederholung_index=row["wiederholung_index"],
        status=CallStatus(row["status"]),
        incomplete_grund=row["incomplete_grund"],
        fehlertext=row["fehlertext"],
        dauer_ms=row["dauer_ms"],
        antwort_text=row["antwort_text"],
        request_json=row["request_json"],
        response_json=row["response_json"],
        erstellt_am=text_to_dt(row["erstellt_am"]),
        **_token_row(row),
    )


def _token_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "input_tokens": row["input_tokens"],
        "cached_input_tokens": row["cached_input_tokens"],
        "reasoning_tokens": row["reasoning_tokens"],
        "output_tokens": row["output_tokens"],
        "total_tokens": row["total_tokens"],
        "web_search_calls": row["web_search_calls"],
    }
