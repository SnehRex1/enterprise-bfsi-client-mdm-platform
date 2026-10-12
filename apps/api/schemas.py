from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class MasterClient(BaseModel):
    """Current Golden Record."""

    master_client_id: str

    name: str | None = None
    dob: date | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None

    tax_id: str | None = None
    lei: str | None = None

    segment: str | None = None
    kyc_status: str | None = None

    verification_date: date | None = None

    aum: Decimal | None = None

    risk_profile: str | None = None
    relationship_manager: str | None = None


class SourceRecord(BaseModel):
    """Canonical trusted source record."""

    record_key: str

    source_system: str
    source_id: str

    name: str | None = None
    normalized_name: str | None = None

    dob: date | None = None
    normalized_dob: date | None = None

    phone: str | None = None
    normalized_phone: str | None = None

    email: str | None = None
    normalized_email: str | None = None

    address: str | None = None
    normalized_address: str | None = None

    tax_id: str | None = None
    lei: str | None = None

    account_id: str | None = None
    branch_id: str | None = None

    segment: str | None = None
    kyc_status: str | None = None

    verification_date: date | None = None
    normalized_verification_date: date | None = None

    aum: Decimal | None = None

    risk_profile: str | None = None
    relationship_manager: str | None = None


class MatchDecisionRequest(BaseModel):
    steward_id: str = Field(min_length=1)
    decision_reason: str = Field(min_length=1)


class HealthResponse(BaseModel):
    status: str