"""
Security configuration and utilities for Memorial Website.
Implements security headers, authentication helpers, and security middleware.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Union

from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from app.core.config import get_settings


async def setup_security_headers(request: Request, call_next):
    """
    Middleware to add security headers to all responses.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware function
        
    Returns:
        Response with security headers added
    """
    response = await call_next(request)
    
    # Add security headers
    add_security_headers(response)
    
    return response


def add_security_headers(response: Union[Response, StarletteResponse]) -> None:
    """
    Add comprehensive security headers to response.
    
    Args:
        response: FastAPI or Starlette response object
    """
    settings = get_settings()
    
    # Content Security Policy
    csp_directives = [
        "default-src 'self' https://cdn.jsdelivr.net https://fonts.googleapis.com https://fonts.gstatic.com",
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com https://fonts.gstatic.com",
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net",
        "connect-src 'self' https://cdn.jsdelivr.net https://fonts.googleapis.com https://fonts.gstatic.com",
        "img-src 'self' data: https: blob:",
        "media-src 'self' blob:",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "upgrade-insecure-requests" if not settings.DEBUG else "",
    ]
    
    # Remove empty directives
    csp_directives = [directive for directive in csp_directives if directive]
    csp_header = "; ".join(csp_directives)
    
    # Security headers
    security_headers = {
        # Content Security Policy
        "Content-Security-Policy": csp_header,
        
        # Prevent MIME type sniffing
        "X-Content-Type-Options": "nosniff",
        
        # Enable XSS protection
        "X-XSS-Protection": "1; mode=block",
        
        # Prevent clickjacking
        "X-Frame-Options": "DENY",
        
        # Referrer policy
        "Referrer-Policy": "strict-origin-when-cross-origin",
        
        # Permissions policy (formerly Feature Policy)
        "Permissions-Policy": (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=(), "
            "accelerometer=(), ambient-light-sensor=(), autoplay=(), "
            "encrypted-media=(), fullscreen=(self), picture-in-picture=()"
        ),
        
        # Remove server information
        "Server": settings.PROJECT_NAME,
        
        # Cache control for sensitive pages
        "Cache-Control": "no-store, no-cache, must-revalidate, private",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    
    # HTTPS-only headers (only in production)
    if not settings.DEBUG:
        security_headers.update({
            # HTTP Strict Transport Security (HSTS)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # Expect Certificate Transparency
            "Expect-CT": "max-age=86400, enforce",
        })
    
    # Add headers to response
    for header, value in security_headers.items():
        response.headers[header] = value


def generate_csrf_token() -> str:
    """
    Generate a secure CSRF token.
    
    Returns:
        str: Random CSRF token
    """
    return secrets.token_urlsafe(32)


def verify_csrf_token(provided_token: str, session_token: str) -> bool:
    """
    Verify CSRF token using constant-time comparison.
    
    Args:
        provided_token: Token provided by client
        session_token: Token stored in session
        
    Returns:
        bool: True if tokens match, False otherwise
    """
    return secrets.compare_digest(provided_token, session_token)


def generate_request_id() -> str:
    """
    Generate a unique request ID for tracing.
    
    Returns:
        str: Unique request identifier
    """
    return str(uuid.uuid4())


def generate_secure_filename(filename: str) -> str:
    """
    Generate a secure filename by sanitizing input.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    import os
    import re
    
    # Extract file extension
    name, ext = os.path.splitext(filename)
    
    # Remove non-alphanumeric characters except hyphens and underscores
    name = re.sub(r'[^a-zA-Z0-9_-]', '', name)
    
    # Limit length
    name = name[:50]
    
    # Add timestamp to ensure uniqueness
    timestamp = int(datetime.utcnow().timestamp())
    
    # Generate random suffix
    suffix = secrets.token_hex(4)
    
    return f"{name}_{timestamp}_{suffix}{ext}"


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    from passlib.context import CryptContext
    
    settings = get_settings()
    pwd_context = CryptContext(
        schemes=["bcrypt"], 
        deprecated="auto",
        bcrypt__rounds=settings.BCRYPT_ROUNDS
    )
    
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        bool: True if password matches, False otherwise
    """
    from passlib.context import CryptContext
    
    settings = get_settings()
    pwd_context = CryptContext(
        schemes=["bcrypt"], 
        deprecated="auto",
        bcrypt__rounds=settings.BCRYPT_ROUNDS
    )
    
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> Dict[str, Union[bool, str]]:
    """
    Validate password strength against security requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        dict: Validation result with is_valid flag and error message
    """
    settings = get_settings()
    errors = []
    
    # Check minimum length
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
    
    # Check for uppercase letter
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    # Check for lowercase letter
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    # Check for digit
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    
    # Check for special character
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        errors.append("Password must contain at least one special character")
    
    # Check for common passwords (basic check)
    common_passwords = {
        "password", "123456", "password123", "admin", "qwerty",
        "letmein", "welcome", "monkey", "dragon", "master"
    }
    if password.lower() in common_passwords:
        errors.append("Password is too common, please choose a more secure password")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }


def generate_api_key() -> str:
    """
    Generate a secure API key.
    
    Returns:
        str: Random API key
    """
    return f"mk_{secrets.token_urlsafe(32)}"  # mk = memorial key


def hash_api_key(api_key: str) -> str:
    """
    Hash API key for secure storage.
    
    Args:
        api_key: Plain API key
        
    Returns:
        str: SHA-256 hash of API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


class SecurityMiddleware(BaseHTTPMiddleware):
    """Custom security middleware for additional security measures."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security middleware."""
        
        # Generate request ID for tracing
        request_id = generate_request_id()
        request.state.request_id = request_id
        
        # Add request start time for performance monitoring
        request.state.start_time = datetime.utcnow()
        
        # Check for suspicious patterns in headers
        if self._is_suspicious_request(request):
            from app.core.logging import log_security_event
            log_security_event(
                "suspicious_request",
                {
                    "path": str(request.url.path),
                    "method": request.method,
                    "user_agent": request.headers.get("user-agent", ""),
                    "headers": dict(request.headers)
                },
                ip_address=self._get_client_ip(request)
            )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        add_security_headers(response)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Add processing time header (for monitoring)
        if hasattr(request.state, "start_time"):
            processing_time = (datetime.utcnow() - request.state.start_time).total_seconds()
            response.headers["X-Processing-Time"] = f"{processing_time:.3f}"
        
        return response
    
    def _is_suspicious_request(self, request: Request) -> bool:
        """
        Check if request exhibits suspicious patterns.
        
        Args:
            request: FastAPI request object
            
        Returns:
            bool: True if request appears suspicious
        """
        # Check for SQL injection patterns in URL
        suspicious_patterns = [
            "union select", "drop table", "exec(", "script>",
            "../", "etc/passwd", "cmd.exe", "powershell"
        ]
        
        url_str = str(request.url).lower()
        for pattern in suspicious_patterns:
            if pattern in url_str:
                return True
        
        # Check for suspicious user agents
        user_agent = request.headers.get("user-agent", "").lower()
        suspicious_agents = [
            "sqlmap", "nikto", "nmap", "masscan", 
            "dirb", "dirbuster", "gobuster"
        ]
        
        for agent in suspicious_agents:
            if agent in user_agent:
                return True
        
        # Check for too many unusual headers
        unusual_headers = [
            header for header in request.headers.keys() 
            if header.lower().startswith('x-') and 
            header.lower() not in ['x-requested-with', 'x-forwarded-for', 'x-real-ip']
        ]
        
        if len(unusual_headers) > 5:
            return True
        
        return False
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            str: Client IP address
        """
        # Check for forwarded headers (common in proxy setups)
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


def create_session_token() -> dict:
    """
    Create a secure session token with expiration.
    
    Returns:
        dict: Session token data
    """
    settings = get_settings()
    
    return {
        "token": secrets.token_urlsafe(32),
        "expires_at": datetime.utcnow() + timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES),
        "created_at": datetime.utcnow()
    }


def is_session_valid(session_data: dict) -> bool:
    """
    Check if session token is still valid.
    
    Args:
        session_data: Session data dictionary
        
    Returns:
        bool: True if session is valid, False otherwise
    """
    if not session_data or "expires_at" not in session_data:
        return False
    
    expires_at = session_data["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    
    return datetime.utcnow() < expires_at


def set_secure_auth_cookie(
    response: Union[Response, StarletteResponse],
    key: str,
    value: str,
    max_age: int,
    httponly: bool = True,
    secure: Optional[bool] = None,
    samesite: str = "lax",
    path: str = "/",
    domain: Optional[str] = None
) -> None:
    """
    Set a secure authentication cookie with bulletproof configuration.
    
    Args:
        response: Response object to set cookie on
        key: Cookie name
        value: Cookie value
        max_age: Cookie expiration in seconds
        httponly: Whether cookie should be HTTP-only
        secure: Whether to require HTTPS (auto-detected if None)
        samesite: SameSite policy
        path: Cookie path
        domain: Cookie domain (auto-detected if None)
    """
    settings = get_settings()
    
    # Auto-detect secure flag based on environment
    if secure is None:
        secure = not settings.DEBUG
    
    # Set the cookie with explicit configuration
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        httponly=httponly,
        secure=secure,
        samesite=samesite,
        path=path,
        domain=domain
    )
    
    # Add cache control headers for authentication responses
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"


def clear_auth_cookies(
    response: Union[Response, StarletteResponse],
    path: str = "/",
    domain: Optional[str] = None
) -> None:
    """
    Clear all authentication-related cookies.
    
    Args:
        response: Response object to clear cookies on
        path: Cookie path
        domain: Cookie domain
    """
    settings = get_settings()
    
    # Clear access token cookie
    response.delete_cookie(
        key="access_token",
        path=path,
        domain=domain,
        secure=not settings.DEBUG,
        samesite="lax"
    )
    
    # Clear refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        path=path,
        domain=domain,
        secure=not settings.DEBUG,
        samesite="lax",
        httponly=True
    )
    
    # Clear any session cookies
    response.delete_cookie(
        key="memorial_session",
        path=path,
        domain=domain,
        secure=not settings.DEBUG,
        samesite="lax",
        httponly=True
    )


def create_bulletproof_redirect(
    url: str,
    status_code: int = 302,
    clear_cookies: bool = False
) -> RedirectResponse:
    """
    Create a bulletproof redirect response with proper headers.
    
    Args:
        url: URL to redirect to
        status_code: HTTP status code for redirect
        clear_cookies: Whether to clear authentication cookies
        
    Returns:
        RedirectResponse: Configured redirect response
    """
    response = RedirectResponse(url=url, status_code=status_code)
    
    # Add cache control headers to prevent caching of redirects
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    # Clear cookies if requested
    if clear_cookies:
        clear_auth_cookies(response)
    
    return response


def sanitize_input(input_string: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent XSS and other injection attacks.
    
    Args:
        input_string: Raw input string
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized input string
    """
    import html
    import re
    
    # Limit length
    sanitized = input_string[:max_length]
    
    # HTML escape
    sanitized = html.escape(sanitized)
    
    # Remove potential script tags and javascript
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
    
    return sanitized.strip()