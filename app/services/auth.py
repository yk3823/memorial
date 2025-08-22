"""
Comprehensive Authentication Service for Memorial Website.
Handles user authentication, JWT token management, session handling, and security operations.
"""

import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any, Union
from urllib.parse import urlencode

import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.security import validate_password_strength, sanitize_input
from app.models.user import User, UserRole, SubscriptionStatus
from app.services.email import EmailService

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass


class AuthorizationError(Exception):
    """Custom exception for authorization errors."""
    pass


class TokenBlacklist:
    """Simple in-memory token blacklist. For production with multiple servers, consider using PostgreSQL."""
    
    def __init__(self):
        self._blacklisted_tokens: Dict[str, datetime] = {}
    
    def add_token(self, jti: str, expires_at: datetime) -> None:
        """Add token to blacklist."""
        self._blacklisted_tokens[jti] = expires_at
        
        # Clean expired tokens periodically
        self._cleanup_expired_tokens()
    
    def is_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        if jti not in self._blacklisted_tokens:
            return False
        
        # Check if token has expired naturally
        if datetime.utcnow() > self._blacklisted_tokens[jti]:
            del self._blacklisted_tokens[jti]
            return False
        
        return True
    
    def _cleanup_expired_tokens(self) -> None:
        """Remove naturally expired tokens from blacklist."""
        current_time = datetime.utcnow()
        expired_tokens = [
            jti for jti, expires_at in self._blacklisted_tokens.items()
            if current_time > expires_at
        ]
        
        for jti in expired_tokens:
            del self._blacklisted_tokens[jti]


class AuthService:
    """Comprehensive authentication and authorization service."""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Password hashing context
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=self.settings.BCRYPT_ROUNDS
        )
        
        # Token blacklist
        self.token_blacklist = TokenBlacklist()
        
        # Email service
        self.email_service = EmailService()
    
    # Password Management
    
    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Stored password hash
            
        Returns:
            bool: True if password matches
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def validate_password(self, password: str) -> Dict[str, Any]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            dict: Validation result with is_valid and errors
        """
        return validate_password_strength(password)
    
    # JWT Token Management
    
    def create_access_token(
        self,
        subject: Union[str, Any],
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create JWT access token.
        
        Args:
            subject: Token subject (usually user ID)
            expires_delta: Token expiration time
            additional_claims: Additional JWT claims
            
        Returns:
            str: JWT access token
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Generate unique token ID for blacklisting
        jti = str(uuid.uuid4())
        
        payload = {
            "sub": str(subject),
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": jti,
            "type": "access"
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        try:
            encoded_jwt = jwt.encode(
                payload,
                self.settings.JWT_SECRET_KEY,
                algorithm=self.settings.JWT_ALGORITHM
            )
            
            logger.debug(f"Created access token for subject: {subject}")
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise AuthenticationError("Failed to create access token")
    
    def create_refresh_token(
        self,
        subject: Union[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT refresh token.
        
        Args:
            subject: Token subject (usually user ID)
            expires_delta: Token expiration time
            
        Returns:
            str: JWT refresh token
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=7)  # Refresh tokens last 7 days
        
        jti = str(uuid.uuid4())
        
        payload = {
            "sub": str(subject),
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": jti,
            "type": "refresh"
        }
        
        try:
            encoded_jwt = jwt.encode(
                payload,
                self.settings.JWT_SECRET_KEY,
                algorithm=self.settings.JWT_ALGORITHM
            )
            
            logger.debug(f"Created refresh token for subject: {subject}")
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise AuthenticationError("Failed to create refresh token")
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate JWT token.
        
        Args:
            token: JWT token to decode
            
        Returns:
            dict: Decoded token payload
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.JWT_SECRET_KEY,
                algorithms=[self.settings.JWT_ALGORITHM]
            )
            
            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti and self.token_blacklist.is_blacklisted(jti):
                raise AuthenticationError("Token has been revoked")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.JWTError as e:
            logger.warning(f"Invalid token: {e}")
            raise AuthenticationError("Invalid token")
        except Exception as e:
            logger.error(f"Token decode error: {e}")
            raise AuthenticationError("Token validation failed")
    
    def revoke_token(self, token: str) -> None:
        """
        Revoke (blacklist) a JWT token.
        
        Args:
            token: JWT token to revoke
        """
        try:
            payload = self.decode_token(token)
            jti = payload.get("jti")
            exp = payload.get("exp")
            
            if jti and exp:
                expires_at = datetime.fromtimestamp(exp)
                self.token_blacklist.add_token(jti, expires_at)
                logger.info(f"Token revoked: {jti}")
                
        except AuthenticationError:
            # Token is already invalid, no need to blacklist
            pass
    
    def create_token_pair(self, user_id: str) -> Dict[str, str]:
        """
        Create access and refresh token pair.
        
        Args:
            user_id: User ID for token subject
            
        Returns:
            dict: Access and refresh tokens
        """
        access_token = self.create_access_token(subject=user_id)
        refresh_token = self.create_refresh_token(subject=user_id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    # User Authentication
    
    async def authenticate_user(
        self,
        db: AsyncSession,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            db: Database session
            email: User email
            password: User password
            
        Returns:
            User: Authenticated user or None if authentication failed
        """
        try:
            # Sanitize email input
            email = sanitize_input(email.lower().strip())
            
            # Find user by email
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"Authentication failed: User not found for email {email}")
                return None
            
            # Verify password
            if not self.verify_password(password, user.password_hash):
                logger.warning(f"Authentication failed: Invalid password for user {user.id}")
                return None
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Authentication failed: User {user.id} is inactive")
                return None
            
            # Record successful login
            user.record_login()
            await db.commit()
            
            logger.info(f"User authenticated successfully: {user.id}")
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            await db.rollback()
            return None
    
    async def get_user_by_token(
        self,
        db: AsyncSession,
        token: str
    ) -> Optional[User]:
        """
        Get user from JWT token.
        
        Args:
            db: Database session
            token: JWT access token
            
        Returns:
            User: User object or None if token is invalid
        """
        try:
            payload = self.decode_token(token)
            user_id = payload.get("sub")
            token_type = payload.get("type")
            
            if not user_id or token_type != "access":
                return None
            
            # Get user from database
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user or not user.is_active:
                return None
            
            return user
            
        except AuthenticationError:
            return None
        except Exception as e:
            logger.error(f"Error getting user by token: {e}")
            return None
    
    # User Registration
    
    async def register_user(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        hebrew_name: Optional[str] = None,
        phone_number: Optional[str] = None
    ) -> Tuple[User, str]:
        """
        Register new user account.
        
        Args:
            db: Database session
            email: User email
            password: User password
            first_name: User first name
            last_name: User last name
            hebrew_name: Optional Hebrew name
            phone_number: Optional phone number
            
        Returns:
            Tuple[User, str]: Created user and verification token
            
        Raises:
            AuthenticationError: If registration fails
        """
        try:
            # Validate and sanitize inputs
            email = sanitize_input(email.lower().strip())
            first_name = sanitize_input(first_name.strip())
            last_name = sanitize_input(last_name.strip())
            
            if hebrew_name:
                hebrew_name = sanitize_input(hebrew_name.strip())
            if phone_number:
                phone_number = sanitize_input(phone_number.strip())
            
            # Validate password
            password_validation = self.validate_password(password)
            if not password_validation["is_valid"]:
                raise AuthenticationError(f"Password validation failed: {', '.join(password_validation['errors'])}")
            
            # Check if user already exists
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                raise AuthenticationError("User with this email already exists")
            
            # Create new user
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                hebrew_name=hebrew_name,
                phone_number=phone_number,
                is_active=True,
                is_verified=False,
                role="user",
                subscription_status="trial"
            )
            
            # Set password
            user.password_hash = self.hash_password(password)
            
            # Generate verification token
            verification_token = user.generate_verification_token()
            
            # Start trial period
            user.start_trial()
            
            # Save user to database
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            # Send verification email
            if self.settings.EMAIL_ENABLED:
                try:
                    await self._send_verification_email(user, verification_token)
                except Exception as e:
                    logger.error(f"Failed to send verification email: {e}")
                    # Don't fail registration if email fails
            
            logger.info(f"User registered successfully: {user.id}")
            return user, verification_token
            
        except AuthenticationError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Registration error: {e}")
            raise AuthenticationError("Registration failed")
    
    # Email Verification
    
    async def verify_email(
        self,
        db: AsyncSession,
        token: str
    ) -> Optional[User]:
        """
        Verify user email with verification token.
        
        Args:
            db: Database session
            token: Email verification token
            
        Returns:
            User: Verified user or None if token is invalid
        """
        try:
            # Find user by verification token
            stmt = select(User).where(User.verification_token == token)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"Invalid verification token: {token}")
                return None
            
            # Verify email
            user.verify_email()
            await db.commit()
            
            logger.info(f"Email verified for user: {user.id}")
            return user
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Email verification error: {e}")
            return None
    
    async def resend_verification_email(
        self,
        db: AsyncSession,
        email: str
    ) -> bool:
        """
        Resend verification email to user.
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            bool: True if email was sent successfully
        """
        try:
            # Find user by email
            stmt = select(User).where(User.email == email.lower().strip())
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            if user.is_verified:
                return False  # Already verified
            
            # Generate new verification token
            verification_token = user.generate_verification_token()
            await db.commit()
            
            # Send verification email
            if self.settings.EMAIL_ENABLED:
                await self._send_verification_email(user, verification_token)
            
            logger.info(f"Verification email resent to user: {user.id}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error resending verification email: {e}")
            return False
    
    # Password Reset
    
    async def request_password_reset(
        self,
        db: AsyncSession,
        email: str
    ) -> bool:
        """
        Request password reset for user.
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            bool: True if reset email was sent
        """
        try:
            # Find user by email
            stmt = select(User).where(User.email == email.lower().strip())
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                # Return True to prevent email enumeration
                return True
            
            if not user.is_active:
                return True
            
            # Generate password reset token
            reset_token = user.generate_reset_password_token()
            await db.commit()
            
            # Send password reset email
            if self.settings.EMAIL_ENABLED:
                await self._send_password_reset_email(user, reset_token)
            
            logger.info(f"Password reset requested for user: {user.id}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Password reset request error: {e}")
            return False
    
    async def reset_password(
        self,
        db: AsyncSession,
        token: str,
        new_password: str
    ) -> Optional[User]:
        """
        Reset user password with reset token.
        
        Args:
            db: Database session
            token: Password reset token
            new_password: New password
            
        Returns:
            User: User with reset password or None if token is invalid
        """
        try:
            # Find user by reset token
            stmt = select(User).where(
                and_(
                    User.reset_password_token == token,
                    User.reset_password_expires_at > datetime.utcnow()
                )
            )
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"Invalid or expired reset token: {token}")
                return None
            
            # Validate new password
            password_validation = self.validate_password(new_password)
            if not password_validation["is_valid"]:
                raise AuthenticationError(f"Password validation failed: {', '.join(password_validation['errors'])}")
            
            # Update password
            user.password_hash = self.hash_password(new_password)
            user.clear_reset_password_token()
            await db.commit()
            
            logger.info(f"Password reset successfully for user: {user.id}")
            return user
            
        except AuthenticationError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Password reset error: {e}")
            return None
    
    # Authorization Helpers
    
    def check_user_permissions(
        self,
        user: User,
        required_roles: Optional[list] = None,
        require_verified: bool = True,
        require_active_subscription: bool = False
    ) -> bool:
        """
        Check if user has required permissions.
        
        Args:
            user: User to check
            required_roles: List of required roles
            require_verified: Whether email verification is required
            require_active_subscription: Whether active subscription is required
            
        Returns:
            bool: True if user has permissions
        """
        if not user.is_active:
            return False
        
        if require_verified and not user.is_verified:
            return False
        
        if required_roles and user.role not in required_roles:
            return False
        
        if require_active_subscription and not user.is_subscription_active():
            return False
        
        return True
    
    def can_access_memorial(self, user: User, memorial_id: str) -> bool:
        """
        Check if user can access specific memorial.
        
        Args:
            user: User to check
            memorial_id: Memorial ID
            
        Returns:
            bool: True if user can access memorial
        """
        return user.can_edit_memorial(uuid.UUID(memorial_id))
    
    # Email Helper Methods
    
    async def _send_verification_email(self, user: User, token: str) -> None:
        """Send email verification email to user."""
        verification_url = f"{self.settings.FRONTEND_URL}/auth/verify-email?token={token}"
        
        subject = "Verify Your Email - Memorial Website"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50; text-align: center;">Welcome to Memorial Website</h2>
                
                <p>Hello {user.first_name},</p>
                
                <p>Thank you for registering with Memorial Website. To complete your registration, please verify your email address by clicking the button below:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background-color: #3498db; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                        Verify Email Address
                    </a>
                </div>
                
                <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #7f8c8d;">{verification_url}</p>
                
                <p>This verification link will expire in 24 hours for security reasons.</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <p style="font-size: 12px; color: #7f8c8d;">
                    If you did not create an account with Memorial Website, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        await self.email_service.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    async def _send_password_reset_email(self, user: User, token: str) -> None:
        """Send password reset email to user."""
        reset_url = f"{self.settings.FRONTEND_URL}/auth/reset-password?token={token}"
        
        subject = "Reset Your Password - Memorial Website"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #e74c3c; text-align: center;">Password Reset Request</h2>
                
                <p>Hello {user.first_name},</p>
                
                <p>We received a request to reset your password for your Memorial Website account. If you made this request, click the button below to reset your password:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #e74c3c; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                        Reset Password
                    </a>
                </div>
                
                <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #7f8c8d;">{reset_url}</p>
                
                <p><strong>Important:</strong> This password reset link will expire in 1 hour for security reasons.</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <p style="font-size: 12px; color: #7f8c8d;">
                    If you did not request a password reset, please ignore this email. Your password will remain unchanged.
                </p>
            </div>
        </body>
        </html>
        """
        
        await self.email_service.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )


# Global auth service instance
auth_service = AuthService()


def get_auth_service() -> AuthService:
    """Get authentication service instance."""
    return auth_service