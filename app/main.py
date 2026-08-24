import logging
import os
import sqlite3
from pathlib import Path
from typing import Callable, Iterator, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.adapters.http.deps import (
    get_call_repo,
    get_connection,
    get_env_api_key,
    get_gateway,
    get_lauf_repo,
    get_lauf_runner,
    get_modell_repo,
    get_profil_repo,
)
from app.adapters.http.routes import router
from app.adapters.responses.client import OpenAiResponsesGateway
from app.adapters.sqlite.call_repository import SqliteCallRepository
from app.adapters.sqlite.connection import create_connection
from app.adapters.sqlite.lauf_repository import SqliteLaufRepository
from app.adapters.sqlite.lauf_runner import ThreadedLaufRunner
from app.adapters.sqlite.modell_repository import SqliteModellRepository
from app.adapters.sqlite.profil_repository import SqliteProfilRepository
from app.adapters.sqlite.schema import ensure_schema, seed_modell_register_if_empty
from app.application.ports import ModelGateway
from app.domain.errors import (
    CallNichtGefunden,
    KeinModellGewaehlt,
    KeyFehlt,
    ModellNameVergeben,
    ModellNichtGefunden,
    NameLeer,
    ProfilNichtGefunden,
    ToolsJsonUngueltig,
    WiederholungenUngueltig,
)

logger = logging.getLogger(__name__)

_ERROR_MAP = {
    ProfilNichtGefunden: (404, "PROFIL_NICHT_GEFUNDEN"),
    CallNichtGefunden: (404, "CALL_NICHT_GEFUNDEN"),
    ModellNichtGefunden: (404, "MODELL_NICHT_GEFUNDEN"),
    NameLeer: (422, "NAME_LEER"),
    KeinModellGewaehlt: (422, "KEIN_MODELL_GEWAEHLT"),
    WiederholungenUngueltig: (422, "WIEDERHOLUNGEN_UNGUELTIG"),
    ToolsJsonUngueltig: (422, "TOOLS_JSON_UNGUELTIG"),
    ModellNameVergeben: (409, "MODELL_NAME_VERGEBEN"),
    KeyFehlt: (400, "KEY_FEHLT"),
}


def create_app(db_path: str, gateway: Optional[ModelGateway] = None) -> FastAPI:
    _initialize_database(db_path)
    real_gateway = gateway or OpenAiResponsesGateway()
    runner = ThreadedLaufRunner(lambda: create_connection(db_path), real_gateway)

    app = FastAPI(title="Prompting Analyzer")
    app.include_router(router)
    _wire_dependencies(app, db_path, real_gateway, runner)
    _install_error_handlers(app)
    app.mount("/", StaticFiles(directory=_static_dir(), html=True), name="static")
    return app


def _wire_dependencies(
    app: FastAPI, db_path: str, gateway: ModelGateway, runner: ThreadedLaufRunner
) -> None:
    app.dependency_overrides[get_connection] = _connection_dependency(db_path)
    app.dependency_overrides[get_profil_repo] = _repo_dependency(SqliteProfilRepository)
    app.dependency_overrides[get_lauf_repo] = _repo_dependency(SqliteLaufRepository)
    app.dependency_overrides[get_call_repo] = _repo_dependency(SqliteCallRepository)
    app.dependency_overrides[get_modell_repo] = _repo_dependency(SqliteModellRepository)
    app.dependency_overrides[get_gateway] = lambda: gateway
    app.dependency_overrides[get_lauf_runner] = lambda: runner
    app.dependency_overrides[get_env_api_key] = lambda: os.environ.get("OPENAI_API_KEY")


def _initialize_database(db_path: str) -> None:
    connection = create_connection(db_path)
    ensure_schema(connection)
    seed_modell_register_if_empty(connection)
    connection.close()


def _connection_dependency(db_path: str) -> Callable[[], Iterator[sqlite3.Connection]]:
    def dependency() -> Iterator[sqlite3.Connection]:
        connection = create_connection(db_path)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    return dependency


def _repo_dependency(repo_cls: Callable[[sqlite3.Connection], object]) -> Callable:
    def dependency(connection: sqlite3.Connection = Depends(get_connection)) -> object:
        return repo_cls(connection)

    return dependency


def _static_dir() -> str:
    return str(Path(__file__).resolve().parent / "adapters" / "http" / "static")


def _install_error_handlers(app: FastAPI) -> None:
    for error_type, (status, code) in _ERROR_MAP.items():
        app.add_exception_handler(error_type, _domain_error_handler(status, code))

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unerwarteter Fehler bei %s", request.url)
        return _error_response(500, "INTERNER_FEHLER", "Unerwarteter Fehler")


def _domain_error_handler(status: int, code: str) -> Callable:
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        return _error_response(status, code, str(exc))

    return handler


def _error_response(status: int, code: str, message: str) -> JSONResponse:
    body = {"error": {"code": code, "message": message, "traceId": str(uuid4())}}
    return JSONResponse(status_code=status, content=body)


def _default_db_path() -> str:
    return os.environ.get("DATABASE_PATH", "data/promptanalyzer.db")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(create_app(_default_db_path()), host="127.0.0.1", port=8000)
