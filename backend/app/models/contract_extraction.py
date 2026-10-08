
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ContractExtractionRecord(Base):
    __tablename__ = "contract_extractions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    document_version_id: Mapped[str] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    extraction_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    extraction_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EXTRACTED",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )