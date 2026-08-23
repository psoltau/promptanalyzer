from datetime import datetime, timezone

from app.application.ports import ProfilRepository
from app.domain.errors import ProfilNichtGefunden
from app.domain.models import Arbeitsstand


def save_arbeitsstand(
    profil_id: str, arbeitsstand: Arbeitsstand, repo: ProfilRepository
) -> datetime:
    if repo.get(profil_id) is None:
        raise ProfilNichtGefunden()
    geaendert_am = datetime.now(timezone.utc)
    repo.save_arbeitsstand(profil_id, arbeitsstand, geaendert_am)
    return geaendert_am
