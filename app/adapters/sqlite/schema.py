import sqlite3

_SCHEMA = """
CREATE TABLE IF NOT EXISTS profil (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    erstellt_am TEXT NOT NULL,
    arbeitsstand_geaendert_am TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    user_prompt TEXT NOT NULL,
    tools_json TEXT,
    modelle TEXT NOT NULL,
    max_output_tokens INTEGER,
    reasoning_effort TEXT,
    web_suche INTEGER NOT NULL,
    search_context_size TEXT,
    wiederholungen INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS lauf (
    id TEXT PRIMARY KEY,
    profil_id TEXT NOT NULL REFERENCES profil(id),
    nummer INTEGER NOT NULL,
    gestartet_am TEXT NOT NULL,
    beendet_am TEXT,
    system_prompt TEXT NOT NULL,
    user_prompt TEXT NOT NULL,
    tools_json TEXT,
    modelle TEXT NOT NULL,
    max_output_tokens INTEGER,
    reasoning_effort TEXT,
    web_suche INTEGER NOT NULL,
    search_context_size TEXT,
    wiederholungen INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS call (
    id TEXT PRIMARY KEY,
    lauf_id TEXT NOT NULL REFERENCES lauf(id),
    modell_name TEXT NOT NULL,
    wiederholung_index INTEGER NOT NULL,
    status TEXT NOT NULL,
    incomplete_grund TEXT,
    fehlertext TEXT,
    dauer_ms INTEGER NOT NULL,
    input_tokens INTEGER,
    cached_input_tokens INTEGER,
    reasoning_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    web_search_calls INTEGER,
    antwort_text TEXT,
    request_json TEXT NOT NULL,
    response_json TEXT,
    erstellt_am TEXT NOT NULL
);
"""


def ensure_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(_SCHEMA)
    connection.commit()
