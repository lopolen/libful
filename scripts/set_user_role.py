#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from libful_api.core.database import SessionLocal
from libful_api.core.exceptions import PasswordRequiredForRole
from libful_api.core.permissions import RoleName
from libful_api.models.user import User
from libful_api.services.users_crud import UsersCrud


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assign admin or librarian role to a user by id.",
    )
    parser.add_argument(
        "user_id",
        type=int,
        help="ID of the user who should receive the role.",
    )
    parser.add_argument(
        "role",
        choices=[role.value for role in RoleName],
        help="Role to assign: admin or librarian.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    with SessionLocal() as db_session:
        user = db_session.get(User, args.user_id)
        if user is None:
            print(f"User with id={args.user_id} was not found.", file=sys.stderr)
            return 1

        users_crud = UsersCrud(db_session)
        try:
            updated_user = users_crud.assign_role_to_user(
                username=user.username,
                role_name=args.role,
            )
            if updated_user is None:
                print(f"User with id={args.user_id} was not found.", file=sys.stderr)
                return 1

            db_session.commit()
        except PasswordRequiredForRole as exc:
            db_session.rollback()
            print(str(exc), file=sys.stderr)
            return 1

        role_names = sorted(role.name for role in updated_user.roles)
        print(
            f"User id={updated_user.id} username={updated_user.username!r} "
            f"roles={role_names}"
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
