from enum import Enum


class RoleName(str, Enum):
    ADMIN = "admin"
    LIBRARIAN = "librarian"


class Permission(str, Enum):
    READ_USERS = "read_users"
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    READ_CATALOG = "read_catalog"
    MANAGE_CATALOG = "manage_catalog"
    MANAGE_CHECK_INS = "manage_check_ins"
    MANAGE_BOOK_RENTS = "manage_book_rents"
    MANAGE_FINES = "manage_fines"


DEFAULT_ROLE_NAMES = tuple(role.value for role in RoleName)

ROLE_PERMISSIONS: dict[RoleName, frozenset[Permission]] = {
    RoleName.ADMIN: frozenset(Permission),
    RoleName.LIBRARIAN: frozenset(
        {
            Permission.READ_USERS,
            Permission.READ_CATALOG,
            Permission.MANAGE_CATALOG,
            Permission.MANAGE_CHECK_INS,
            Permission.MANAGE_BOOK_RENTS,
            Permission.MANAGE_FINES,
        }
    ),
}


def normalize_role_name(role_name: str | RoleName) -> str:
    return RoleName(role_name).value


def permissions_for_roles(role_names: set[str]) -> set[Permission]:
    permissions: set[Permission] = set()
    for role_name in role_names:
        try:
            role = RoleName(role_name)
        except ValueError:
            continue
        permissions.update(ROLE_PERMISSIONS[role])

    return permissions
