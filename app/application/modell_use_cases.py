from typing import List

from app.application.ports import ModellRepository
from app.domain.errors import ModellNameVergeben, ModellNichtGefunden
from app.domain.models import Modell


def list_modelle(repo: ModellRepository) -> List[Modell]:
    return repo.list()


def create_modell(name: str, repo: ModellRepository) -> Modell:
    if repo.get(name) is not None:
        raise ModellNameVergeben()
    modell = Modell.neu(name)
    repo.add(modell)
    return modell


def update_modell(modell: Modell, repo: ModellRepository) -> Modell:
    if repo.get(modell.name) is None:
        raise ModellNichtGefunden()
    repo.update(modell)
    return modell


def delete_modell(name: str, repo: ModellRepository) -> None:
    if repo.get(name) is None:
        raise ModellNichtGefunden()
    repo.delete(name)
