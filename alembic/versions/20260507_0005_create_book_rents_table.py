"""create book rents table

Revision ID: 20260507_0005
Revises: 20260506_0004
Create Date: 2026-05-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260507_0005"
down_revision: Union[str, Sequence[str], None] = "20260506_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "book_rents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_copy_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "rented_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("return_status", sa.String(length=30), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "return_status IS NULL OR return_status IN "
            "('available', 'damaged', 'lost')",
            name="ck_book_rents_return_status",
        ),
        sa.ForeignKeyConstraint(["book_copy_id"], ["book_copies.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("book_rents")
