import dataclasses
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from app.application.ports import (
    CallRepository,
    LaufRepository,
    ProfilDuplicationPorts,
    ProfilRepository,
)
from app.domain.errors import ProfilNichtGefunden
from app.domain.models import Arbeitsstand, Call, Lauf, Profil, ProfilUebersicht

_ABGELEITETER_NAME_ZUSATZ = " (Kopie)"


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


def rename_profile(profil_id: str, name: str, repo: ProfilRepository) -> Profil:
    profil = repo.get(profil_id)
    if profil is None:
        raise ProfilNichtGefunden()
    umbenannt = dataclasses.replace(profil, name=name)
    repo.update_name(profil_id, umbenannt.name)
    return umbenannt


def delete_profile(profil_id: str, repo: ProfilRepository) -> None:
    if repo.get(profil_id) is None:
        raise ProfilNichtGefunden()
    repo.delete(profil_id)


def duplicate_profile(
    profil_id: str, name: Optional[str], ports: ProfilDuplicationPorts
) -> Profil:
    original = ports.profil_repo.get(profil_id)
    if original is None:
        raise ProfilNichtGefunden()
    duplikat = _neues_duplikat(original, name)
    ports.profil_repo.add(duplikat)
    _dupliziere_historie(original.id, duplikat.id, ports)
    return duplikat


def _neues_duplikat(original: Profil, name: Optional[str]) -> Profil:
    now = datetime.now(timezone.utc)
    return Profil(
        id=str(uuid4()),
        name=name or _abgeleiteter_name(original.name),
        erstellt_am=now,
        arbeitsstand_geaendert_am=now,
        arbeitsstand=original.arbeitsstand,
    )


def _abgeleiteter_name(name: str) -> str:
    return name + _ABGELEITETER_NAME_ZUSATZ


def _dupliziere_historie(
    original_id: str, duplikat_id: str, ports: ProfilDuplicationPorts
) -> None:
    laeufe = ports.lauf_repo.list_for_profil(original_id)
    calls = ports.call_repo.list_for_profil(original_id)
    lauf_id_mapping = {
        lauf.id: _dupliziere_lauf(lauf, duplikat_id, ports.lauf_repo) for lauf in laeufe
    }
    for call in calls:
        _dupliziere_call(call, lauf_id_mapping[call.lauf_id], ports.call_repo)


def _dupliziere_lauf(original: Lauf, duplikat_profil_id: str, lauf_repo: LaufRepository) -> str:
    neue_id = str(uuid4())
    lauf_repo.add(dataclasses.replace(original, id=neue_id, profil_id=duplikat_profil_id))
    return neue_id


def _dupliziere_call(original: Call, neue_lauf_id: str, call_repo: CallRepository) -> None:
    call_repo.add(dataclasses.replace(original, id=str(uuid4()), lauf_id=neue_lauf_id))
