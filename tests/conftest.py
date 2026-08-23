import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from tests.fakes import FakeModelGateway


@pytest.fixture
def gateway() -> FakeModelGateway:
    return FakeModelGateway()


@pytest.fixture
def client(tmp_path, gateway: FakeModelGateway, monkeypatch) -> TestClient:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    db_path = str(tmp_path / "test.db")
    app = create_app(db_path, gateway=gateway)
    with TestClient(app) as test_client:
        yield test_client
