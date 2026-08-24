import logging
import sqlite3
import threading
from contextlib import contextmanager
from typing import Callable, Iterator

from app.adapters.sqlite.call_repository import SqliteCallRepository
from app.adapters.sqlite.lauf_repository import SqliteLaufRepository
from app.adapters.sqlite.modell_repository import SqliteModellRepository
from app.application.lauf_use_cases import execute_lauf
from app.application.ports import LaufExecutionPorts, ModelGateway
from app.domain.models import Lauf

logger = logging.getLogger(__name__)


class ThreadedLaufRunner:
    """Läuft in einem eigenen Hintergrund-Thread. `execute_lauf` fächert intern über die
    Modelle auf einen Thread je Modell auf; jeder dieser Threads bekommt hier über
    `_oeffne_ports` seine eigene, exklusive `sqlite3.Connection` — eine Connection wird nie
    zwischen gleichzeitig laufenden Threads geteilt."""

    def __init__(
        self, connection_factory: Callable[[], sqlite3.Connection], gateway: ModelGateway
    ) -> None:
        self._connection_factory = connection_factory
        self._gateway = gateway

    def start(self, lauf: Lauf, api_key: str) -> None:
        thread = threading.Thread(target=self._run, args=(lauf, api_key), daemon=True)
        thread.start()

    def _run(self, lauf: Lauf, api_key: str) -> None:
        try:
            execute_lauf(lauf, api_key, self._oeffne_ports)
        except Exception:
            logger.exception("Lauf %s fehlgeschlagen", lauf.id)

    @contextmanager
    def _oeffne_ports(self) -> Iterator[LaufExecutionPorts]:
        connection = self._connection_factory()
        try:
            yield LaufExecutionPorts(
                gateway=self._gateway,
                call_repo=SqliteCallRepository(connection),
                lauf_repo=SqliteLaufRepository(connection),
                modell_repo=SqliteModellRepository(connection),
            )
        finally:
            connection.close()
