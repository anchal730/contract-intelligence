import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base



class Document(Base):

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentVersion(Base):

    __tablename__ = "document_versions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    processing_status: Mapped[str] = mapped_column(
        String(20),
        default="UPLOADED",
        nullable=False,
    )

    processing_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    document: Mapped["Document"] = relationship(
        back_populates="versions",
    )

    pages: Mapped[list["Page"]] = relationship(
        back_populates="document_version",
        cascade="all, delete-orphan",
    )

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document_version",
        cascade="all, delete-orphan",
    )
    
    


class Page(Base):

    __tablename__ = "pages"

    __table_args__ = (
        UniqueConstraint(
            "document_version_id",
            "page_number",
            name="uq_document_version_page_number",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    document_version_id: Mapped[str] = mapped_column(
        ForeignKey("document_versions.id"),
        nullable=False,
    )

    page_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    document_version: Mapped["DocumentVersion"] = relationship(
        back_populates="pages",
    )


class DocumentChunk(Base):

    __tablename__ = "document_chunks"

    __table_args__ = (
        UniqueConstraint(
            "document_version_id",
            "chunk_index",
            name="uq_document_version_chunk_index",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    document_version_id: Mapped[str] = mapped_column(
        ForeignKey("document_versions.id"),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    start_page: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    end_page: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    document_version: Mapped["DocumentVersion"] = relationship(
        back_populates="chunks",
    )
    
