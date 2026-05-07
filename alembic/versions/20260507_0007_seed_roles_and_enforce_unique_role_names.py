"""seed roles and enforce unique role names

Revision ID: 20260507_0007
Revises: 20260507_0006
Create Date: 2026-05-07
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260507_0007"
down_revision: Union[str, Sequence[str], None] = "20260507_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "INSERT INTO roles (name) "
        "SELECT 'admin' "
        "WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'admin')"
    )
    op.execute(
        "INSERT INTO roles (name) "
        "SELECT 'librarian' "
        "WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'librarian')"
    )
    op.create_index("ix_roles_name_unique", "roles", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_roles_name_unique", table_name="roles")
    op.execute(
        "DELETE FROM users_roles "
        "WHERE role_id IN (SELECT id FROM roles WHERE name IN ('admin', 'librarian'))"
    )
    op.execute("DELETE FROM roles WHERE name IN ('admin', 'librarian')")
