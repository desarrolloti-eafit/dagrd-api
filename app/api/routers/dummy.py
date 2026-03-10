from fastapi import APIRouter, Depends

from app.api.dependencies import require_roles
from app.models.user import RoleEnum
from app.schemas.user import TokenPayload

router = APIRouter(prefix="/api/dummy", tags=["Dummy"])


@router.get(
    "/community",
    summary="Endpoint accessible by Community and Manager",
)
def community_endpoint(
    payload: TokenPayload = Depends(require_roles(RoleEnum.Community, RoleEnum.Manager)),
) -> dict:
    """Returns a dummy payload for roles: **Community**, **Manager**."""
    return {
        "message": "Hello from /community",
        "accessed_by": payload.sub,
        "role": payload.role.value,
        "allowed_roles": [RoleEnum.Community.value, RoleEnum.Manager.value],
    }


@router.get(
    "/operational",
    summary="Endpoint accessible by Operational and Manager",
)
def operational_endpoint(
    payload: TokenPayload = Depends(require_roles(RoleEnum.Operational, RoleEnum.Manager)),
) -> dict:
    """Returns a dummy payload for roles: **Operational**, **Manager**."""
    return {
        "message": "Hello from /operational",
        "accessed_by": payload.sub,
        "role": payload.role.value,
        "allowed_roles": [RoleEnum.Operational.value, RoleEnum.Manager.value],
    }


@router.get(
    "/manager",
    summary="Endpoint exclusively for Manager",
)
def manager_endpoint(
    payload: TokenPayload = Depends(require_roles(RoleEnum.Manager)),
) -> dict:
    """Returns a dummy payload exclusively for role: **Manager**."""
    return {
        "message": "Hello from /manager",
        "accessed_by": payload.sub,
        "role": payload.role.value,
        "allowed_roles": [RoleEnum.Manager.value],
    }
