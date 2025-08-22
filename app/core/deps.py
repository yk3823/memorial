"""
FastAPI dependencies for authentication, authorization, and database access.
Provides reusable dependency functions for securing API endpoints and managing sessions.
"""

import logging
from typing import Optional, List, Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database, create_session_factory, create_database_engine
from app.core.config import get_settings
from app.models.user import User, UserRole
from app.services.auth import AuthService, AuthenticationError, get_auth_service
from app.schemas.auth import UserResponse

logger = logging.getLogger(__name__)

# Security scheme for JWT Bearer tokens
security = HTTPBearer(auto_error=False)

# Initialize settings
settings = get_settings()


# Database Dependencies
async def get_db() -> AsyncSession:
    """
    Database dependency function.
    
    Returns:
        AsyncSession: Database session with automatic cleanup
    """
    async for session in get_database():
        yield session


# Enhanced Authentication Dependencies with Bulletproof Cookie Handling

async def get_current_user_optional(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> Optional[User]:
    """
    Get current user from JWT token with bulletproof authentication handling.
    
    This function implements multiple fallback mechanisms to ensure reliable
    authentication state detection and prevent redirect loops.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Authorization credentials
        db: Database session
        auth_service: Authentication service
        
    Returns:
        Optional[User]: Current user or None if not authenticated
    """
    # Multiple token source attempts for maximum reliability
    token = None
    token_source = None
    
    # Priority 1: Authorization header (API requests)
    if credentials and credentials.credentials:
        token = credentials.credentials.strip()
        token_source = "header"
        logger.debug("Token found in Authorization header")
    
    # Priority 2: HTTP-only access_token cookie (web requests)
    elif request.cookies.get('access_token'):
        token = request.cookies.get('access_token').strip()
        token_source = "cookie"
        logger.debug("Token found in access_token cookie")
    
    # Priority 3: Session-based token (fallback)
    elif hasattr(request, 'session') and request.session.get('access_token'):
        token = request.session.get('access_token').strip()
        token_source = "session"
        logger.debug("Token found in session")
    
    # No token found - return None (not authenticated)
    if not token:
        logger.debug("No authentication token found")
        return None
    
    # Validate token format (basic sanity check)
    if len(token) < 10 or '.' not in token:
        logger.warning(f"Invalid token format from {token_source}")
        return None
    
    try:
        # Attempt to get user from token with retry logic
        user = await _get_user_with_retry(auth_service, db, token, max_retries=2)
        
        if user:
            # Store authentication context in request state
            request.state.current_user = user
            request.state.auth_token_source = token_source
            request.state.auth_token = token
            
            logger.debug(f"User authenticated successfully: {user.id} (source: {token_source})")
            return user
        else:
            logger.warning(f"Token valid but user not found or inactive (source: {token_source})")
            return None
        
    except AuthenticationError as e:
        logger.warning(f"Authentication failed from {token_source}: {e}")
        # Clear invalid token from session if it was the source
        if token_source == "session" and hasattr(request, 'session'):
            request.session.pop('access_token', None)
        return None
    except Exception as e:
        logger.error(f"Unexpected authentication error from {token_source}: {e}")
        return None


async def _get_user_with_retry(
    auth_service: AuthService, 
    db: AsyncSession, 
    token: str, 
    max_retries: int = 2
) -> Optional[User]:
    """
    Get user from token with retry logic for database connection issues.
    
    Args:
        auth_service: Authentication service
        db: Database session
        token: JWT token
        max_retries: Maximum retry attempts
        
    Returns:
        Optional[User]: User object or None
    """
    for attempt in range(max_retries + 1):
        try:
            user = await auth_service.get_user_by_token(db, token)
            return user
        except Exception as e:
            if attempt == max_retries:
                raise
            logger.debug(f"Token validation retry {attempt + 1}/{max_retries}: {e}")
            # Brief delay before retry
            import asyncio
            await asyncio.sleep(0.1)
    
    return None


async def get_current_user(
    current_user: Annotated[Optional[User], Depends(get_current_user_optional)]
) -> User:
    """
    Get current authenticated user (required - raises exception if not authenticated).
    
    Args:
        current_user: Current user from optional dependency
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if not current_user:
        logger.warning("Authentication required but no valid credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return current_user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Get current active user (must be authenticated and active).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user attempted access: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    return current_user


async def get_current_verified_user(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    Get current verified user (must be authenticated, active, and email verified).
    
    Args:
        current_user: Current active user
        
    Returns:
        User: Current verified user
        
    Raises:
        HTTPException: If user email is not verified
    """
    if not current_user.is_verified:
        logger.warning(f"Unverified user attempted access: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    
    return current_user


# Authorization Dependencies
def require_roles(allowed_roles: List[UserRole]):
    """
    Create dependency that requires specific user roles.
    
    Args:
        allowed_roles: List of allowed user roles
        
    Returns:
        Dependency function that checks user roles
    """
    async def check_user_roles(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        """
        Check if current user has required roles.
        
        Args:
            current_user: Current active user
            
        Returns:
            User: Current user with required roles
            
        Raises:
            HTTPException: If user doesn't have required roles
        """
        if current_user.role not in allowed_roles:
            logger.warning(
                f"User {current_user.id} with role {current_user.role} "
                f"attempted access requiring roles: {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
            )
        
        return current_user
    
    return check_user_roles


# Admin-only access
require_admin = require_roles([UserRole.ADMIN])


def require_subscription():
    """
    Create dependency that requires active subscription.
    
    Returns:
        Dependency function that checks subscription status
    """
    async def check_subscription(
        current_user: Annotated[User, Depends(get_current_verified_user)]
    ) -> User:
        """
        Check if current user has active subscription.
        
        Args:
            current_user: Current verified user
            
        Returns:
            User: Current user with active subscription
            
        Raises:
            HTTPException: If user doesn't have active subscription
        """
        if not current_user.is_subscription_active():
            logger.warning(
                f"User {current_user.id} with subscription status "
                f"{current_user.subscription_status} attempted access requiring subscription"
            )
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Active subscription required"
            )
        
        return current_user
    
    return check_subscription


def require_memorial_access(memorial_id_param: str = "memorial_id"):
    """
    Create dependency that checks if user can access a specific memorial.
    
    Args:
        memorial_id_param: Name of the path parameter containing memorial ID
        
    Returns:
        Dependency function that checks memorial access
    """
    async def check_memorial_access(
        memorial_id: UUID,
        current_user: Annotated[User, Depends(get_current_verified_user)],
        auth_service: Annotated[AuthService, Depends(get_auth_service)]
    ) -> User:
        """
        Check if current user can access the specified memorial.
        
        Args:
            memorial_id: Memorial ID from path parameter
            current_user: Current verified user
            auth_service: Authentication service
            
        Returns:
            User: Current user with memorial access
            
        Raises:
            HTTPException: If user cannot access the memorial
        """
        # Admins can access all memorials
        if current_user.is_admin():
            return current_user
        
        # Check if user can access this memorial
        if not auth_service.can_access_memorial(current_user, str(memorial_id)):
            logger.warning(
                f"User {current_user.id} attempted unauthorized access to memorial {memorial_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this memorial"
            )
        
        return current_user
    
    return check_memorial_access


# Rate Limiting Dependencies
def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Client IP address
    """
    # Check for forwarded headers first
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Get first IP in case of multiple proxies
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    # Fallback to client IP
    if request.client:
        return request.client.host
    
    return "unknown"


# User Response Dependencies
async def get_user_response(
    current_user: Annotated[User, Depends(get_current_user)]
) -> UserResponse:
    """
    Convert User model to UserResponse schema.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserResponse: User response schema
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        full_name=current_user.full_name,
        hebrew_name=current_user.hebrew_name,
        display_name=current_user.display_name,
        phone_number=current_user.phone_number,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        role=current_user.role,
        subscription_status=current_user.subscription_status,
        subscription_end_date=current_user.subscription_end_date,
        trial_end_date=current_user.trial_end_date,
        last_login_at=current_user.last_login_at,
        login_count=current_user.login_count,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


# Context Dependencies for Logging
async def get_request_context(
    request: Request,
    current_user: Annotated[Optional[User], Depends(get_current_user_optional)]
) -> dict:
    """
    Get request context for logging and monitoring.
    
    Args:
        request: FastAPI request object
        current_user: Current user (optional)
        
    Returns:
        dict: Request context information
    """
    return {
        "request_id": getattr(request.state, "request_id", "unknown"),
        "method": request.method,
        "url": str(request.url),
        "user_id": str(current_user.id) if current_user else None,
        "user_email": current_user.email if current_user else None,
        "client_ip": get_client_ip(request),
        "user_agent": request.headers.get("user-agent", "unknown")
    }


# Session Dependencies
async def get_session_data(request: Request) -> Optional[dict]:
    """
    Get session data from request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Optional[dict]: Session data or None if no session
    """
    return request.session if hasattr(request, "session") else None


async def require_csrf_token(
    request: Request,
    session_data: Annotated[Optional[dict], Depends(get_session_data)]
) -> None:
    """
    Require valid CSRF token for state-changing operations.
    
    Args:
        request: FastAPI request object
        session_data: Session data
        
    Raises:
        HTTPException: If CSRF token is invalid or missing
    """
    if request.method in ["GET", "HEAD", "OPTIONS"]:
        return  # CSRF not required for safe methods
    
    # Get CSRF token from header
    csrf_token = request.headers.get("x-csrf-token")
    
    if not csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token required"
        )
    
    # Get session CSRF token
    session_csrf = session_data.get("csrf_token") if session_data else None
    
    if not session_csrf:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No CSRF token in session"
        )
    
    # Verify CSRF tokens match
    from app.core.security import verify_csrf_token
    if not verify_csrf_token(csrf_token, session_csrf):
        logger.warning("CSRF token validation failed")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token"
        )


# Pagination Dependencies
class PaginationParams:
    """Pagination parameters for list endpoints."""
    
    def __init__(self, skip: int = 0, limit: int = 20):
        self.skip = max(0, skip)
        self.limit = min(100, max(1, limit))  # Limit between 1 and 100


async def get_pagination(
    skip: int = 0,
    limit: int = 20
) -> PaginationParams:
    """
    Get pagination parameters with validation.
    
    Args:
        skip: Number of items to skip
        limit: Maximum number of items to return
        
    Returns:
        PaginationParams: Validated pagination parameters
    """
    return PaginationParams(skip, limit)