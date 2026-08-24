from datetime import datetime, timezone

from app.application.ports import ArbeitsstandUebernahmePorts, ProfilRepository
from app.domain.errors import LaufNichtGefunden, ProfilNichtGefunden
from app.domain.models import Arbeitsstand


def save_arbeitsstand(
    profil_id: str, arbeitsstand: Arbeitsstand, repo: ProfilRepository
) -> datetime:
    if repo.get(profil_id) is None:
        raise ProfilNichtGefunden()
    geaendert_am = datetime.now(timezone.utc)
    repo.save_arbeitsstand(profil_id, arbeitsstand, geaendert_am)
    return geaendert_am


def uebernehme_arbeitsstand_aus_lauf(
    profil_id: str, lauf_id: str, ports: ArbeitsstandUebernahmePorts
) -> Arbeitsstand:
    if ports.profil_repo.get(profil_id) is None:
        raise ProfilNichtGefunden()
    lauf = ports.lauf_repo.get(lauf_id)
    if lauf is None or lauf.profil_id != profil_id:
        raise LaufNichtGefunden()
    geaendert_am = datetime.now(timezone.utc)
    ports.profil_repo.save_arbeitsstand(profil_id, lauf.arbeitsstand, geaendert_am)
    return lauf.arbeitsstand
