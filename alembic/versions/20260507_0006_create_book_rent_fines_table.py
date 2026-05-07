"""create book rent fines table

Revision ID: 20260507_0006
Revises: 20260507_0005
Create Date: 2026-05-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260507_0006"
down_revision: Union[str, Sequence[str], None] = "20260507_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "book_rent_fines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_rent_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("fine_type", sa.String(length=30), nullable=False),
        sa.Column("amount_uah", sa.Integer(), nullable=False),
        sa.Column("days_overdue", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "fine_type IN ('overdue', 'damage')",
            name="ck_book_rent_fines_fine_type",
        ),
        sa.CheckConstraint("amount_uah >= 0", name="ck_book_rent_fines_amount_uah"),
        sa.CheckConstraint(
            "days_overdue IS NULL OR days_overdue >= 0",
            name="ck_book_rent_fines_days_overdue",
        ),
        sa.ForeignKeyConstraint(["book_rent_id"], ["book_rents.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_rent_id", "fine_type"),
    )


def downgrade() -> None:
    op.drop_table("book_rent_fines")
