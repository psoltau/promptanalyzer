from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from app.application.ports import ProfilRepository
from app.domain.errors import ProfilNichtGefunden
from app.domain.models import Arbeitsstand, Profil, ProfilUebersicht


def list_profiles(repo: ProfilRepository) -> List[ProfilUebersicht]:
    return repo.list_uebersicht()


def create_profile(name: str, repo: ProfilRepository) -> Profil:
    now = datetime.now(timezone.utc)
    profil = Profil(
        id=str(uuid4()),
        name=name,
        erstellt_am=now,
        arbeitsstand_geaendert_am=now,
        arbeitsstand=Arbeitsstand.leer(),
    )
    repo.add(profil)
    return profil


def get_profile(profil_id: str, repo: ProfilRepository) -> Profil:
    profil = repo.get(profil_id)
    if profil is None:
        raise ProfilNichtGefunden()
    return profil
