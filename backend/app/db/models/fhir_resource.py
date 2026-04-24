"""FHIR Resource Database Model"""
from typing import Any, Dict, Optional
import uuid
from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin, TimestampMixin


class FHIRResourceType:
    PATIENT = "Patient"
    CONDITION = "Condition"
    ENCOUNTER = "Encounter"
    OBSERVATION = "Observation"
    BUNDLE = "Bundle"

    ALL_TYPES = [PATIENT, CONDITION, ENCOUNTER, OBSERVATION, BUNDLE]


class FHIRResource(Base, TenantMixin, TimestampMixin):
    __tablename__ = "fhir_resources"

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
    patient_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), default="1", nullable=False)
    resource_json: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="fhir_resources")
    patient = relationship("Patient", back_populates="fhir_resources")

    __table_args__ = (
        Index("ix_fhir_org_resource_id", "organization_id", "resource_id", unique=True),
        Index("ix_fhir_org_type_patient", "organization_id", "resource_type", "patient_id"),
    )
