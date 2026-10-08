"""Request and response models."""
from datetime import datetime
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Latitude = Annotated[float, Field(ge=-90, le=90, description="Degrees north (WGS 84)")]
Longitude = Annotated[float, Field(ge=-180, le=180, description="Degrees east (WGS 84)")]


def _text(max_length: int) -> type[str]:
    """A string trimmed of surrounding whitespace that must not end up empty."""
    return Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=max_length)
    ]


def _validate_country(value: str | None) -> str | None:
    if value is None:
        return value
    value = value.strip().upper()
    if len(value) != 2 or not value.isalpha():
        raise ValueError("must be a two-letter ISO 3166-1 country code")
    return value


class ContactIn(BaseModel):
    """Full contact payload, used for create and full replace."""

    label: _text(120) = Field(examples=["Warehouse"])
    line1: _text(200) = Field(examples=["12 Harbour Road"])
    line2: _text(200) | None = None
    city: _text(100) = Field(examples=["Lisbon"])
    region: _text(100) | None = None
    postal_code: _text(20) | None = None
    country_code: str = Field(examples=["PT"])
    latitude: Latitude = Field(examples=[38.7223])
    longitude: Longitude = Field(examples=[-9.1393])

    _normalise_country = field_validator("country_code")(_validate_country)


class ContactPatch(BaseModel):
    """Partial update: only the fields that are sent are changed."""

    label: _text(120) | None = None
    line1: _text(200) | None = None
    line2: _text(200) | None = None
    city: _text(100) | None = None
    region: _text(100) | None = None
    postal_code: _text(20) | None = None
    country_code: str | None = None
    latitude: Latitude | None = None
    longitude: Longitude | None = None

    _normalise_country = field_validator("country_code")(_validate_country)


class ContactOut(ContactIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class NearbyContact(ContactOut):
    distance_km: float


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
