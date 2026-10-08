"""add processing status to document versions

Revision ID: abab968049ef
Revises: f89429046899
Create Date: 2026-09-17 22:30:22.832550

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision: str = "abab968049ef"
down_revision: Union[str, Sequence[str], None] = "f89429046899"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "document_versions",
        sa.Column(
            "processing_status",
            sa.String(length=20),
            nullable=False,
            server_default="UPLOADED",
        ),
    )

    op.add_column(
        "document_versions",
        sa.Column(
            "processing_error",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "document_versions",
        "processing_error",
    )

    op.drop_column(
        "document_versions",
        "processing_status",
    )