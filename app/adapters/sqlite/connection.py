import sqlite3
from pathlib import Path


def create_connection(db_path: str) -> sqlite3.Connection:
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    # FastAPI/anyio may run a sync dependency's open and close in different
    # worker threads within the same request; the connection is still only
    # ever used by one request/thread at a time, never concurrently.
    connection = sqlite3.connect(db_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection
