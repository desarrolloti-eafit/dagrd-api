"""
API-level dependencies (FastAPI Depends() interceptors).

This module provides:
- ``get_current_user_payload``: validates the JWT signature and extracts the
  payload WITHOUT touching the database (fully stateless).
- ``require_roles``: a factory that returns a dependency enforcing one or more
  allowed roles.
"""

from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.security import decode_access_token
from app.models.user import RoleEnum
from app.schemas.user import TokenPayload

_bearer_scheme = HTTPBearer(auto_error=True)


def get_current_user_payload(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> TokenPayload:
    """Extract and validate the JWT; return the payload as a typed object.

    The database is **never** consulted here — this is the stateless contract.
    """
    try:
        raw = decode_access_token(credentials.credentials)
        payload = TokenPayload(sub=raw["sub"], role=RoleEnum(raw["role"]))
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def require_roles(*allowed: RoleEnum) -> Callable:
    """Dependency factory that ensures the token's role is among ``allowed``.

    Usage::

        @router.get("/endpoint")
        def endpoint(payload: TokenPayload = Depends(require_roles(RoleEnum.Manager))):
            ...
    """

    def _check(payload: TokenPayload = Depends(get_current_user_payload)) -> TokenPayload:
        if payload.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{payload.role.value}' is not authorised to access this resource. "
                    f"Required: {[r.value for r in allowed]}"
                ),
            )
        return payload

    return _check
