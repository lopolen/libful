"""make check in datetime required

Revision ID: 20260506_0003
Revises: 20260506_0002
Create Date: 2026-05-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260506_0003"
down_revision: Union[str, Sequence[str], None] = "20260506_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("check_in_history") as batch_op:
        batch_op.alter_column(
            "check_in_datetime",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )


def downgrade() -> None:
    with op.batch_alter_table("check_in_history") as batch_op:
        batch_op.alter_column(
            "check_in_datetime",
            existing_type=sa.DateTime(timezone=True),
            nullable=True,
            server_default=None,
        )
