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
    erstellt_am TEXT NOT NULL,
    preis_input REAL,
    preis_cached_input REAL,
    preis_output REAL,
    preis_suche REAL,
    kosten_usd REAL
);

CREATE TABLE IF NOT EXISTS modell (
    name TEXT PRIMARY KEY,
    preis_input REAL,
    preis_cached_input REAL,
    preis_output REAL,
    preis_suche REAL,
    kontextfenster INTEGER,
    erlaubt_reasoning_effort INTEGER NOT NULL,
    erlaubt_web_suche INTEGER NOT NULL,
    unterstuetzt_prompt_caching INTEGER NOT NULL
);
"""

# Plausible OpenAI-Responses-API-Modellnamen für die Saatliste. Keine Preise, kein
# Kontextfenster: nichts davon soll fälschlich für aktuell gehalten werden (Ticket 05).
_SEED_MODELLE = (
    "gpt-5",
    "gpt-5-mini",
    "gpt-5-nano",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4o",
    "gpt-4o-mini",
    "o4-mini",
    "o3",
    "o3-mini",
)

_SEED_INSERT_SQL = (
    "INSERT INTO modell ("
    "name, preis_input, preis_cached_input, preis_output, preis_suche, kontextfenster, "
    "erlaubt_reasoning_effort, erlaubt_web_suche, unterstuetzt_prompt_caching"
    ") VALUES (?, NULL, NULL, NULL, NULL, NULL, 1, 1, 1)"
)


def ensure_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(_SCHEMA)
    connection.commit()


def seed_modell_register_if_empty(connection: sqlite3.Connection) -> None:
    """Seedet die Saatliste nur, wenn das Register leer ist — ein Neustart gegen eine
    bestehende DB darf Zeilen weder verdoppeln noch zurücksetzen."""
    (anzahl,) = connection.execute("SELECT COUNT(*) FROM modell").fetchone()
    if anzahl > 0:
        return
    connection.executemany(_SEED_INSERT_SQL, [(name,) for name in _SEED_MODELLE])
    connection.commit()
