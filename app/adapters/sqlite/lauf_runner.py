import logging
import sqlite3
import threading
from typing import Callable

from app.adapters.sqlite.call_repository import SqliteCallRepository
from app.adapters.sqlite.lauf_repository import SqliteLaufRepository
from app.application.lauf_use_cases import execute_lauf
from app.application.ports import LaufExecutionPorts, ModelGateway
from app.domain.models import Lauf

logger = logging.getLogger(__name__)


class ThreadedLaufRunner:
    def __init__(
        self, connection_factory: Callable[[], sqlite3.Connection], gateway: ModelGateway
    ) -> None:
        self._connection_factory = connection_factory
        self._gateway = gateway

    def start(self, lauf: Lauf, api_key: str) -> None:
        thread = threading.Thread(target=self._run, args=(lauf, api_key), daemon=True)
        thread.start()

    def _run(self, lauf: Lauf, api_key: str) -> None:
        connection = self._connection_factory()
        try:
            ports = LaufExecutionPorts(
                gateway=self._gateway,
                call_repo=SqliteCallRepository(connection),
                lauf_repo=SqliteLaufRepository(connection),
            )
            execute_lauf(lauf, api_key, ports)
        except Exception:
            logger.exception("Lauf %s fehlgeschlagen", lauf.id)
        finally:
            connection.close()
