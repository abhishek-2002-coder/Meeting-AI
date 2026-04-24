"""Import Job and Record Database Models"""
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin, TimestampMixin


class ImportStatus:
    UPLOADED = "UPLOADED"
    PARSING = "PARSING"
    MAPPING_REQUIRED = "MAPPING_REQUIRED"
    PROCESSING = "PROCESSING"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    FAILED = "FAILED"


class RecordStatus:
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


class Import(Base, TenantMixin, TimestampMixin):
    __tablename__ = "imports"

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
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # csv, json
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=ImportStatus.UPLOADED, nullable=False, index=True)
    
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    detected_headers: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    suggested_mapping: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    active_mapping: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="imports")
    creator = relationship("User", back_populates="imports")
    records = relationship("ImportRecord", back_populates="import_job", cascade="all, delete-orphan")


class ImportRecord(Base, TimestampMixin):
    __tablename__ = "import_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    import_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("imports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    canonical_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=RecordStatus.SUCCESS, nullable=False)
    validation_errors: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Relationships
    import_job = relationship("Import", back_populates="records")
