from fastapi import APIRouter, Depends

from libful_api.api.deps import RolesCrudDep, require_permission
from libful_api.core.permissions import Permission
from libful_api.models.role import Role
from libful_api.schemas.role import RoleRead


router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get(
    "/",
    response_model=list[RoleRead],
    dependencies=[Depends(require_permission(Permission.READ_USERS))],
)
def list_roles(roles_crud: RolesCrudDep) -> list[Role]:
    return roles_crud.list_roles()
