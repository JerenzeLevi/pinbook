"""Persistence for contacts. Each public method is one atomic unit of work."""
import logging
from collections.abc import Mapping
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from pinbook.geometry import BoundingBox, haversine_km
from pinbook.models import Contact

logger = logging.getLogger(__name__)


class ContactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, contact_id: int) -> Contact | None:
        return await self._session.get(Contact, contact_id)

    async def page(self, limit: int, offset: int) -> tuple[list[Contact], int]:
        total = await self._session.scalar(select(func.count()).select_from(Contact))
        rows = await self._session.scalars(
            select(Contact).order_by(Contact.id).limit(limit).offset(offset)
        )
        return list(rows), total or 0

    async def create(self, values: Mapping[str, Any]) -> Contact:
        contact = Contact(**values)
        self._session.add(contact)
        await self._commit(contact)
        logger.info("contact created id=%s", contact.id)
        return contact

    async def update(self, contact: Contact, values: Mapping[str, Any]) -> Contact:
        for field, value in values.items():
            setattr(contact, field, value)
        await self._commit(contact)
        logger.info("contact updated id=%s fields=%s", contact.id, sorted(values))
        return contact

    async def delete(self, contact: Contact) -> None:
        contact_id = contact.id
        await self._session.delete(contact)
        await self._session.commit()
        logger.info("contact deleted id=%s", contact_id)

    async def nearby(
        self, lat: float, lon: float, radius_km: float, limit: int
    ) -> list[tuple[Contact, float]]:
        """Contacts within ``radius_km`` of a point, closest first."""
        box = BoundingBox.around(lat, lon, radius_km)
        stmt = select(Contact).where(
            Contact.latitude.between(box.min_lat, box.max_lat),
            or_(*(Contact.longitude.between(lo, hi) for lo, hi in box.lon_spans)),
        )
        hits = []
        for contact in await self._session.scalars(stmt):
            distance = haversine_km(lat, lon, contact.latitude, contact.longitude)
            if distance <= radius_km:
                hits.append((contact, distance))
        hits.sort(key=lambda hit: hit[1])
        logger.info("proximity search lat=%s lon=%s r=%skm hits=%d", lat, lon, radius_km, len(hits))
        return hits[:limit]

    async def _commit(self, contact: Contact) -> None:
        await self._session.commit()
        # Re-read server-generated columns (timestamps) after the write.
        await self._session.refresh(contact)
