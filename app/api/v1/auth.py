"""
Authentication API endpoints for Memorial Website.
Handles user registration, login, logout, password reset, and email verification.
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.deps import (
    get_db,
    get_current_user_optional,
    get_current_user,
    get_current_active_user,
    get_client_ip
)
from app.core.config import get_settings
from app.services.auth import AuthService, AuthenticationError, get_auth_service
from app.schemas.auth import (
    UserRegister,
    UserRegisterResponse,
    UserLogin,
    UserLoginResponse,
    UserResponse,
    UserMeResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    EmailVerificationRequest,
    ResendVerificationRequest,
    LogoutResponse,
    PasswordChangeRequest,
    UserProfileUpdate,
    BaseResponse,
    ErrorResponse
)
from app.models.user import User

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(tags=["Authentication"])

# Settings
settings = get_settings()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


# User Registration
@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user account",
    description="Create a new user account with email verification requirement."
)
@limiter.limit("5/minute")  # Limit registration attempts
async def register(
    request: Request,
    user_data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> UserRegisterResponse:
    """
    Register a new user account.
    
    - **email**: User's email address (must be unique)
    - **password**: Strong password (8+ chars, mixed case, numbers, symbols)
    - **confirm_password**: Password confirmation
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **hebrew_name**: Optional Hebrew name
    - **phone_number**: Optional phone number
    
    Returns user ID and verification requirements.
    """
    try:
        logger.info(f"Registration attempt for email: {user_data.email}")
        
        # Register user
        user, verification_token = await auth_service.register_user(
            db=db,
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            hebrew_name=user_data.hebrew_name,
            phone_number=user_data.phone_number
        )
        
        logger.info(f"User registered successfully: {user.id}")
        
        return UserRegisterResponse(
            success=True,
            message="User registered successfully. Please check your email to verify your account.",
            user_id=user.id,
            email=user.email,
            verification_required=True
        )
        
    except AuthenticationError as e:
        logger.warning(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


# User Login
@router.post(
    "/login",
    response_model=UserLoginResponse,
    summary="User login",
    description="Authenticate user and return JWT tokens."
)
@limiter.limit("10/minute")  # Limit login attempts
async def login(
    request: Request,
    response: Response,
    login_data: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> UserLoginResponse:
    """
    Authenticate user and return access tokens.
    
    - **email**: User's email address
    - **password**: User's password
    - **remember_me**: Whether to extend token lifetime
    
    Returns JWT access and refresh tokens with user information.
    """
    try:
        logger.info(f"Login attempt for email: {login_data.email}")
        
        # Authenticate user
        user = await auth_service.authenticate_user(
            db=db,
            email=login_data.email,
            password=login_data.password
        )
        
        if not user:
            logger.warning(f"Login failed for email: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Check if user is verified (allow login but show warning)
        if not user.is_verified:
            logger.info(f"Unverified user logged in: {user.id}")
        
        # Ensure user object is refreshed in the current session
        await db.refresh(user)
        
        # Create tokens
        token_data = auth_service.create_token_pair(str(user.id))
        
        # Set secure cookie for access token (for web routes authentication)
        response.set_cookie(
            key="access_token",
            value=token_data["access_token"],
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Same as token expiration
            httponly=False,  # Allow JavaScript access for API calls
            secure=False,  # Disable secure for localhost testing
            samesite="lax",
            path="/",  # Ensure cookie is available for all routes
            domain=None  # Let browser determine the domain
        )
        
        # Set secure cookie for refresh token if remember_me is true
        if login_data.remember_me:
            response.set_cookie(
                key="refresh_token",
                value=token_data["refresh_token"],
                max_age=7 * 24 * 60 * 60,  # 7 days
                httponly=True,
                secure=not settings.DEBUG,
                samesite="lax",
                path="/"  # Ensure cookie is available for all routes
            )
        
        # Convert user to response schema
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            hebrew_name=user.hebrew_name,
            display_name=user.display_name,
            phone_number=user.phone_number,
            is_active=user.is_active,
            is_verified=user.is_verified,
            role=user.role,
            subscription_status=user.subscription_status,
            subscription_end_date=user.subscription_end_date,
            trial_end_date=user.trial_end_date,
            last_login_at=user.last_login_at,
            login_count=user.login_count,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        logger.info(f"User logged in successfully: {user.id}")
        
        return UserLoginResponse(
            success=True,
            message="Login successful" + (" - Please verify your email" if not user.is_verified else ""),
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_type=token_data["token_type"],
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


# Token Refresh
@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh access token",
    description="Get new access token using refresh token."
)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    token_data: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> RefreshTokenResponse:
    """
    Refresh access token using valid refresh token.
    
    - **refresh_token**: Valid JWT refresh token
    
    Returns new access token.
    """
    try:
        # Decode refresh token
        payload = auth_service.decode_token(token_data.refresh_token)
        
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")
        
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token")
        
        # Verify user still exists and is active
        from sqlalchemy import select
        from app.models.user import User
        
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        
        # Create new access token
        new_access_token = auth_service.create_access_token(subject=user_id)
        
        logger.info(f"Token refreshed for user: {user_id}")
        
        return RefreshTokenResponse(
            success=True,
            message="Token refreshed successfully",
            access_token=new_access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except AuthenticationError as e:
        logger.warning(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


# User Logout
@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="User logout",
    description="Logout user and invalidate tokens."
)
async def logout(
    request: Request,
    response: Response,
    current_user: Annotated[Optional[User], Depends(get_current_user_optional)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> LogoutResponse:
    """
    Logout user and invalidate current tokens.
    
    Blacklists current access token and removes refresh token cookie.
    """
    try:
        # Get token from Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
            # Revoke the token
            auth_service.revoke_token(token)
            
            if current_user:
                logger.info(f"User logged out: {current_user.id}")
            else:
                logger.info("Anonymous logout (token revoked)")
        
        # Clear both access and refresh token cookies
        response.delete_cookie(
            key="access_token",
            httponly=False,  # Match the original cookie settings
            secure=False,    # Match the original cookie settings for localhost
            samesite="lax",
            path="/"
        )
        
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
            path="/"
        )
        
        return LogoutResponse(
            success=True,
            message="Logged out successfully"
        )
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        # Don't fail logout even if token revocation fails
        return LogoutResponse(
            success=True,
            message="Logged out successfully"
        )


# Get Current User
@router.get(
    "/me",
    response_model=UserMeResponse,
    summary="Get current user information",
    description="Get information about the currently authenticated user."
)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
) -> UserMeResponse:
    """
    Get current user information.
    
    Returns detailed information about the authenticated user.
    """
    user_response = UserResponse(
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
    
    return UserMeResponse(
        success=True,
        message="User information retrieved successfully",
        user=user_response
    )


# Email Verification
@router.get(
    "/verify-email",
    response_model=BaseResponse,
    summary="Verify user email",
    description="Verify user email address using verification token."
)
async def verify_email(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> BaseResponse:
    """
    Verify user email address.
    
    - **token**: Email verification token from email link
    
    Activates user account and marks email as verified.
    """
    try:
        logger.info(f"Email verification attempt with token: {token[:8]}...")
        
        # Verify email
        user = await auth_service.verify_email(db, token)
        
        if not user:
            logger.warning(f"Email verification failed: invalid token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        logger.info(f"Email verified for user: {user.id}")
        
        return BaseResponse(
            success=True,
            message="Email verified successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


# Resend Verification Email
@router.post(
    "/resend-verification",
    response_model=BaseResponse,
    summary="Resend verification email",
    description="Resend email verification link to user."
)
@limiter.limit("3/hour")  # Limit verification email requests
async def resend_verification(
    request: Request,
    email_data: ResendVerificationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> BaseResponse:
    """
    Resend email verification link.
    
    - **email**: User's email address
    
    Sends new verification email if user exists and is not verified.
    """
    try:
        logger.info(f"Verification email resend request for: {email_data.email}")
        
        # Resend verification email
        sent = await auth_service.resend_verification_email(db, email_data.email)
        
        # Always return success to prevent email enumeration
        return BaseResponse(
            success=True,
            message="If the email address is registered and not verified, a new verification email has been sent"
        )
        
    except Exception as e:
        logger.error(f"Resend verification error: {e}")
        # Don't reveal error details
        return BaseResponse(
            success=True,
            message="If the email address is registered and not verified, a new verification email has been sent"
        )


# Password Reset Request
@router.post(
    "/forgot-password",
    response_model=BaseResponse,
    summary="Request password reset",
    description="Request password reset email for user account."
)
@limiter.limit("3/hour")  # Limit password reset requests
async def forgot_password(
    request: Request,
    reset_data: PasswordResetRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> BaseResponse:
    """
    Request password reset.
    
    - **email**: User's email address
    
    Sends password reset email if user exists and is active.
    """
    try:
        logger.info(f"Password reset request for: {reset_data.email}")
        
        # Request password reset
        sent = await auth_service.request_password_reset(db, reset_data.email)
        
        # Always return success to prevent email enumeration
        return BaseResponse(
            success=True,
            message="If the email address is registered, a password reset email has been sent"
        )
        
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        # Don't reveal error details
        return BaseResponse(
            success=True,
            message="If the email address is registered, a password reset email has been sent"
        )


# Password Reset Confirmation
@router.post(
    "/reset-password",
    response_model=BaseResponse,
    summary="Reset password",
    description="Reset user password using reset token."
)
@limiter.limit("5/hour")  # Limit password reset attempts
async def reset_password(
    request: Request,
    reset_data: PasswordResetConfirm,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> BaseResponse:
    """
    Reset user password.
    
    - **token**: Password reset token from email
    - **new_password**: New strong password
    - **confirm_password**: Password confirmation
    
    Updates user password and invalidates reset token.
    """
    try:
        logger.info(f"Password reset attempt with token: {reset_data.token[:8]}...")
        
        # Reset password
        user = await auth_service.reset_password(
            db=db,
            token=reset_data.token,
            new_password=reset_data.new_password
        )
        
        if not user:
            logger.warning(f"Password reset failed: invalid token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        logger.info(f"Password reset successfully for user: {user.id}")
        
        return BaseResponse(
            success=True,
            message="Password reset successfully"
        )
        
    except AuthenticationError as e:
        logger.warning(f"Password reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


# Change Password (Authenticated)
@router.post(
    "/change-password",
    response_model=BaseResponse,
    summary="Change password",
    description="Change password for authenticated user."
)
@limiter.limit("5/hour")
async def change_password(
    request: Request,
    password_data: PasswordChangeRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> BaseResponse:
    """
    Change password for authenticated user.
    
    - **current_password**: Current password
    - **new_password**: New strong password
    - **confirm_password**: Password confirmation
    
    Requires current password verification.
    """
    try:
        logger.info(f"Password change request for user: {current_user.id}")
        
        # Verify current password
        if not auth_service.verify_password(password_data.current_password, current_user.password_hash):
            logger.warning(f"Password change failed: incorrect current password for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        password_validation = auth_service.validate_password(password_data.new_password)
        if not password_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password validation failed: {', '.join(password_validation['errors'])}"
            )
        
        # Update password
        current_user.password_hash = auth_service.hash_password(password_data.new_password)
        await db.commit()
        
        logger.info(f"Password changed successfully for user: {current_user.id}")
        
        return BaseResponse(
            success=True,
            message="Password changed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


# Update User Profile
@router.put(
    "/profile",
    response_model=UserMeResponse,
    summary="Update user profile",
    description="Update user profile information."
)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserMeResponse:
    """
    Update user profile information.
    
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **hebrew_name**: User's Hebrew name
    - **phone_number**: User's phone number
    
    Updates only provided fields.
    """
    try:
        logger.info(f"Profile update request for user: {current_user.id}")
        
        # Update provided fields
        if profile_data.first_name is not None:
            current_user.first_name = profile_data.first_name
        if profile_data.last_name is not None:
            current_user.last_name = profile_data.last_name
        if profile_data.hebrew_name is not None:
            current_user.hebrew_name = profile_data.hebrew_name
        if profile_data.phone_number is not None:
            current_user.phone_number = profile_data.phone_number
        
        await db.commit()
        await db.refresh(current_user)
        
        logger.info(f"Profile updated successfully for user: {current_user.id}")
        
        # Return updated user info
        user_response = UserResponse(
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
        
        return UserMeResponse(
            success=True,
            message="Profile updated successfully",
            user=user_response
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )