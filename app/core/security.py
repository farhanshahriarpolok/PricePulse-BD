"""
Authentication and security dependencies for administrative API access.
"""

import secrets
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

API_KEY_HEADER_NAME = "X-API-Key"
api_key_header = APIKeyHeader(
    name=API_KEY_HEADER_NAME,
    auto_error=False,
    description="Administrative API Key required for mutation endpoints (e.g. manual spot reporting, system sync).",
)


def require_admin_api_key(
    provided_key: str = Security(api_key_header),
) -> str:
    """
    FastAPI dependency validating the X-API-Key header against PRICEPULSE_ADMIN_API_KEY.

    Invariants:
    1. Timing-safe comparison via secrets.compare_digest().
    2. Fail-closed: If PRICEPULSE_ADMIN_API_KEY is not configured or empty, all attempts return 401.
    3. Missing or incorrect header returns HTTP 401 Unauthorized with neutral message.
    4. Never leaks key material in error responses or logs.
    """
    configured_key = settings.admin_api_key

    # Fail closed if server has no administrative key configured
    if not configured_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrative access is not configured on this server.",
            headers={"WWW-Authenticate": API_KEY_HEADER_NAME},
        )

    # Missing header
    if not provided_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required administrative API key header.",
            headers={"WWW-Authenticate": API_KEY_HEADER_NAME},
        )

    # Timing-safe comparison
    if not secrets.compare_digest(provided_key, configured_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrative API key.",
            headers={"WWW-Authenticate": API_KEY_HEADER_NAME},
        )

    return provided_key
