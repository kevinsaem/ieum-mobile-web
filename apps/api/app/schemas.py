from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OfferCreate(BaseModel):
    category: str = Field(min_length=1, max_length=30)
    title: str = Field(min_length=2, max_length=120)
    quantity: int = Field(ge=1, le=100000)
    unit: str = Field(min_length=1, max_length=20)
    available_until: date
    delivery_method: str = Field(min_length=1, max_length=30)
    description: str = Field(min_length=1, max_length=2000)

    @field_validator("available_until")
    @classmethod
    def availability_must_not_be_expired(cls, value: date) -> date:
        if value < date.today():
            raise ValueError("제공 기한은 오늘 이후여야 합니다.")
        return value


class OfferRevision(OfferCreate):
    expected_version: int = Field(ge=1)


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    action: str
    from_status: str | None
    to_status: str
    actor_id: str
    reason: str | None
    created_at: datetime


class OfferReview(BaseModel):
    action: Literal["APPROVE", "REQUEST_REVISION", "REJECT"]
    reason: str = Field(min_length=2, max_length=1000)
    expected_version: int = Field(ge=1)


class OfferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    title: str
    quantity: int
    remaining_quantity: int
    unit: str
    status: str
    version: int
    organization_id: str
    organization_name: str
    available_until: date
    delivery_method: str
    description: str
    review_reason: str | None
