"""Patient Database Model"""
from datetime import date
from typing import Optional, Dict, Any
import uuid
from sqlalchemy import Date, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin, TimestampMixin


class Patient(Base, TenantMixin, TimestampMixin):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    middle_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # male, female, other, unknown
    phone: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True, default=dict)

    # Relationships
    organization = relationship("Organization", back_populates="patients")
    fhir_resources = relationship("FHIRResource", back_populates="patient", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_patients_org_external_id", "organization_id", "external_id"),
        Index("ix_patients_org_name", "organization_id", "first_name", "last_name"),
    )
