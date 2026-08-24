import sqlite3
from typing import Any, Dict, List, Optional

from app.adapters.sqlite.time_codec import text_to_dt
from app.domain.key_sanitizer import bereinige
from app.domain.kosten import PreisSchnappschuss
from app.domain.models import Call, CallStatus

_INSERT_SQL = (
    "INSERT INTO call ("
    "id, lauf_id, modell_name, wiederholung_index, status, incomplete_grund, fehlertext, "
    "dauer_ms, input_tokens, cached_input_tokens, reasoning_tokens, output_tokens, "
    "total_tokens, web_search_calls, antwort_text, request_json, response_json, erstellt_am, "
    "preis_input, preis_cached_input, preis_output, preis_suche, kosten_usd"
    ") VALUES ("
    ":id, :lauf_id, :modell_name, :wiederholung_index, :status, :incomplete_grund, "
    ":fehlertext, :dauer_ms, :input_tokens, :cached_input_tokens, :reasoning_tokens, "
    ":output_tokens, :total_tokens, :web_search_calls, :antwort_text, :request_json, "
    ":response_json, :erstellt_am, :preis_input, :preis_cached_input, :preis_output, "
    ":preis_suche, :kosten_usd)"
)

_UPDATE_KOSTEN_SQL = (
    "UPDATE call SET preis_input = :preis_input, preis_cached_input = :preis_cached_input, "
    "preis_output = :preis_output, preis_suche = :preis_suche, kosten_usd = :kosten_usd "
    "WHERE id = :id"
)


class SqliteCallRepository:
    # Writes commit immediately (unlike the "commit once per request" default):
    # a background Lauf writes one Call at a time over minutes, and the calls
    # endpoint polls the same table from other connections to show progress.
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, call: Call) -> None:
        self._connection.execute(_INSERT_SQL, _call_to_params(call))
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

    def list_for_lauf(self, lauf_id: str) -> List[Call]:
        rows = self._connection.execute(
            "SELECT * FROM call WHERE lauf_id = ? ORDER BY erstellt_am", (lauf_id,)
        ).fetchall()
        return [_row_to_call(row) for row in rows]

    def update_kosten(
        self, call_id: str, preise: PreisSchnappschuss, kosten_usd: Optional[float]
    ) -> None:
        self._connection.execute(
            _UPDATE_KOSTEN_SQL, {**_preise_to_params(preise), "kosten_usd": kosten_usd, "id": call_id}
        )
        self._connection.commit()


def _call_to_params(call: Call) -> Dict[str, Any]:
    return {
        "id": call.id,
        "lauf_id": call.lauf_id,
        "modell_name": call.modell_name,
        "wiederholung_index": call.wiederholung_index,
        "status": call.status.value,
        "incomplete_grund": call.incomplete_grund,
        "fehlertext": bereinige(call.fehlertext),
        "dauer_ms": call.dauer_ms,
        "antwort_text": bereinige(call.antwort_text),
        "request_json": bereinige(call.request_json),
        "response_json": bereinige(call.response_json),
        "erstellt_am": call.erstellt_am.isoformat(),
        **_token_params(call),
        **_preise_to_params(_call_preise(call)),
        "kosten_usd": call.kosten_usd,
    }


def _call_preise(call: Call) -> PreisSchnappschuss:
    return PreisSchnappschuss(
        preis_input=call.preis_input,
        preis_cached_input=call.preis_cached_input,
        preis_output=call.preis_output,
        preis_suche=call.preis_suche,
    )


def _preise_to_params(preise: PreisSchnappschuss) -> Dict[str, Optional[float]]:
    return {
        "preis_input": preise.preis_input,
        "preis_cached_input": preise.preis_cached_input,
        "preis_output": preise.preis_output,
        "preis_suche": preise.preis_suche,
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
        **_kosten_row(row),
    )


def _kosten_row(row: sqlite3.Row) -> Dict[str, Optional[float]]:
    return {
        "preis_input": row["preis_input"],
        "preis_cached_input": row["preis_cached_input"],
        "preis_output": row["preis_output"],
        "preis_suche": row["preis_suche"],
        "kosten_usd": row["kosten_usd"],
    }


def _token_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "input_tokens": row["input_tokens"],
        "cached_input_tokens": row["cached_input_tokens"],
        "reasoning_tokens": row["reasoning_tokens"],
        "output_tokens": row["output_tokens"],
        "total_tokens": row["total_tokens"],
        "web_search_calls": row["web_search_calls"],
    }
