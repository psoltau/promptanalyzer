from typing import List, Optional

from fastapi import APIRouter, Depends, Response

from app.adapters.http.deps import (
    LaufStartDeps,
    get_call_repo,
    get_env_api_key,
    get_lauf_repo,
    get_lauf_start_deps,
    get_modell_repo,
    get_profil_repo,
)
from app.adapters.http.mappers import (
    body_to_arbeitsstand,
    call_detail_view_to_schema,
    calls_view_to_response,
    env_key_to_status,
    lauf_to_start_response,
    modell_to_item,
    modell_update_body_to_modell,
    profil_to_detail,
    profil_uebersicht_to_item,
    to_iso_z,
)
from app.adapters.http.schemas import (
    ArbeitsstandBody,
    ArbeitsstandSaveResponse,
    CallDetail,
    CallsResponse,
    KeyStatusResponse,
    KostenNeuberechnungResponse,
    LaufStartResponse,
    ModellCreateBody,
    ModellItem,
    ModellUpdateBody,
    ProfilCreateBody,
    ProfilDetail,
    ProfilListItem,
)
from app.application.arbeitsstand_use_cases import save_arbeitsstand
from app.application.calls_use_cases import get_call_view, list_calls_view
from app.application.lauf_use_cases import kosten_neu_berechnen, start_lauf
from app.application.modell_use_cases import (
    create_modell,
    delete_modell,
    list_modelle,
    update_modell,
)
from app.application.ports import (
    CallRepository,
    LaufKostenPorts,
    LaufRepository,
    ModellRepository,
    ProfilRepository,
)
from app.application.profile_use_cases import create_profile, get_profile, list_profiles

router = APIRouter(prefix="/api/v1")


@router.get("/key-status", response_model=KeyStatusResponse)
def key_status_route(env_key: Optional[str] = Depends(get_env_api_key)) -> KeyStatusResponse:
    return env_key_to_status(env_key)


@router.get("/profile", response_model=List[ProfilListItem])
def list_profile_route(repo: ProfilRepository = Depends(get_profil_repo)) -> List[ProfilListItem]:
    return [profil_uebersicht_to_item(p) for p in list_profiles(repo)]


@router.post("/profile", response_model=ProfilDetail, status_code=201)
def create_profile_route(
    body: ProfilCreateBody, response: Response, repo: ProfilRepository = Depends(get_profil_repo)
) -> ProfilDetail:
    profil = create_profile(body.name, repo)
    response.headers["Location"] = f"/api/v1/profile/{profil.id}"
    return profil_to_detail(profil)


@router.get("/profile/{profil_id}", response_model=ProfilDetail)
def get_profile_route(
    profil_id: str, repo: ProfilRepository = Depends(get_profil_repo)
) -> ProfilDetail:
    return profil_to_detail(get_profile(profil_id, repo))


@router.put("/profile/{profil_id}/arbeitsstand", response_model=ArbeitsstandSaveResponse)
def save_arbeitsstand_route(
    profil_id: str, body: ArbeitsstandBody, repo: ProfilRepository = Depends(get_profil_repo)
) -> ArbeitsstandSaveResponse:
    arbeitsstand = body_to_arbeitsstand(body)
    geaendert_am = save_arbeitsstand(profil_id, arbeitsstand, repo)
    return ArbeitsstandSaveResponse(arbeitsstand_geaendert_am=to_iso_z(geaendert_am))


@router.post("/profile/{profil_id}/laeufe", response_model=LaufStartResponse, status_code=201)
def start_lauf_route(
    profil_id: str, response: Response, deps: LaufStartDeps = Depends(get_lauf_start_deps)
) -> LaufStartResponse:
    lauf = start_lauf(profil_id, deps.api_key, deps.ports)
    response.headers["Location"] = f"/api/v1/lauf/{lauf.id}"
    return lauf_to_start_response(lauf)


@router.post("/lauf/{lauf_id}/kosten-neuberechnung", response_model=KostenNeuberechnungResponse)
def kosten_neuberechnung_route(
    lauf_id: str,
    lauf_repo: LaufRepository = Depends(get_lauf_repo),
    call_repo: CallRepository = Depends(get_call_repo),
    modell_repo: ModellRepository = Depends(get_modell_repo),
) -> KostenNeuberechnungResponse:
    ports = LaufKostenPorts(lauf_repo=lauf_repo, call_repo=call_repo, modell_repo=modell_repo)
    geaenderte_calls = kosten_neu_berechnen(lauf_id, ports)
    return KostenNeuberechnungResponse(geaenderte_calls=geaenderte_calls)


@router.get("/profile/{profil_id}/calls", response_model=CallsResponse)
def list_calls_route(
    profil_id: str,
    lauf_repo: LaufRepository = Depends(get_lauf_repo),
    call_repo: CallRepository = Depends(get_call_repo),
) -> CallsResponse:
    return calls_view_to_response(list_calls_view(profil_id, lauf_repo, call_repo))


@router.get("/call/{call_id}", response_model=CallDetail)
def get_call_route(
    call_id: str,
    call_repo: CallRepository = Depends(get_call_repo),
    lauf_repo: LaufRepository = Depends(get_lauf_repo),
) -> CallDetail:
    return call_detail_view_to_schema(get_call_view(call_id, call_repo, lauf_repo))


@router.get("/modelle", response_model=List[ModellItem])
def list_modelle_route(repo: ModellRepository = Depends(get_modell_repo)) -> List[ModellItem]:
    return [modell_to_item(m) for m in list_modelle(repo)]


@router.post("/modelle", response_model=ModellItem, status_code=201)
def create_modell_route(
    body: ModellCreateBody, response: Response, repo: ModellRepository = Depends(get_modell_repo)
) -> ModellItem:
    modell = create_modell(body.name, repo)
    response.headers["Location"] = f"/api/v1/modelle/{modell.name}"
    return modell_to_item(modell)


@router.put("/modelle/{name}", response_model=ModellItem)
def update_modell_route(
    name: str, body: ModellUpdateBody, repo: ModellRepository = Depends(get_modell_repo)
) -> ModellItem:
    modell = update_modell(modell_update_body_to_modell(name, body), repo)
    return modell_to_item(modell)


@router.delete("/modelle/{name}", status_code=204)
def delete_modell_route(name: str, repo: ModellRepository = Depends(get_modell_repo)) -> None:
    delete_modell(name, repo)
