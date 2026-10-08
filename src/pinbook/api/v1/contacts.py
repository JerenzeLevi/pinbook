"""Contact endpoints (v1)."""
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from pinbook.api.deps import AppSettings, Repository
from pinbook.errors import ContactNotFoundError
from pinbook.models import Contact
from pinbook.schemas import ContactIn, ContactOut, ContactPatch, NearbyContact, Page

router = APIRouter(prefix="/contacts", tags=["contacts"])

_NOT_FOUND = {404: {"description": "Contact not found"}}


async def _load(repo: Repository, contact_id: int) -> Contact:
    contact = await repo.get(contact_id)
    if contact is None:
        raise ContactNotFoundError(contact_id)
    return contact


@router.post("", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
async def create_contact(body: ContactIn, repo: Repository):
    """Store a new contact."""
    return await repo.create(body.model_dump())


@router.get("", response_model=Page[ContactOut])
async def list_contacts(
    repo: Repository,
    settings: AppSettings,
    limit: Annotated[int | None, Query(ge=1)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List contacts with offset pagination."""
    limit = min(limit or settings.max_page_size, settings.max_page_size)
    items, total = await repo.page(limit, offset)
    return Page[ContactOut](
        items=[ContactOut.model_validate(c) for c in items], total=total, limit=limit, offset=offset
    )


# Registered before "/{contact_id}" so the literal path wins over the int parameter.
@router.get("/search/nearby", response_model=list[NearbyContact])
async def search_nearby(
    repo: Repository,
    settings: AppSettings,
    lat: Annotated[float, Query(ge=-90, le=90, description="Centre latitude")],
    lon: Annotated[float, Query(ge=-180, le=180, description="Centre longitude")],
    radius_km: Annotated[float, Query(gt=0, description="Search radius in kilometres")],
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
):
    """Contacts within a radius of a point, closest first."""
    radius = min(radius_km, settings.max_search_radius_km)
    hits = await repo.nearby(lat, lon, radius, limit)
    return [
        NearbyContact(**ContactOut.model_validate(c).model_dump(), distance_km=round(d, 3))
        for c, d in hits
    ]


@router.get("/{contact_id}", response_model=ContactOut, responses=_NOT_FOUND)
async def get_contact(contact_id: int, repo: Repository):
    return await _load(repo, contact_id)


@router.put("/{contact_id}", response_model=ContactOut, responses=_NOT_FOUND)
async def replace_contact(contact_id: int, body: ContactIn, repo: Repository):
    """Replace every field of a contact."""
    return await repo.update(await _load(repo, contact_id), body.model_dump())


@router.patch("/{contact_id}", response_model=ContactOut, responses=_NOT_FOUND)
async def patch_contact(contact_id: int, body: ContactPatch, repo: Repository):
    """Change only the fields that are present in the request."""
    return await repo.update(await _load(repo, contact_id), body.model_dump(exclude_unset=True))


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT, responses=_NOT_FOUND)
async def delete_contact(contact_id: int, repo: Repository):
    await repo.delete(await _load(repo, contact_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
