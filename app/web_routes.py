"""
Web routes for serving HTML templates
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_302_FOUND
from typing import Optional
import datetime
import logging

from app.models.user import User
from app.core.deps import get_current_user_optional, get_db
from sqlalchemy.ext.asyncio import AsyncSession

# Initialize templates
templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

# Initialize logger
logger = logging.getLogger(__name__)

# Template context processors
def get_template_context(request: Request, user: Optional[User] = None):
    """Get common template context variables"""
    return {
        "request": request,
        "current_user": user,
        "current_year": datetime.datetime.now().year,
    }

@router.get("/", response_class=HTMLResponse, name="home")
async def home(
    request: Request, 
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Home page - Hebrew RTL by default"""
    context = get_template_context(request, user)
    
    # If user is logged in, show Hebrew dashboard, otherwise show Hebrew landing page
    if user:
        return templates.TemplateResponse("dashboard_rtl.html", context)
    else:
        return templates.TemplateResponse("index_rtl.html", context)

@router.get("/dashboard", response_class=HTMLResponse, name="dashboard")
async def dashboard(
    request: Request, 
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Dashboard page for authenticated users - Hebrew RTL"""
    if not user:
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    
    context = get_template_context(request, user)
    return templates.TemplateResponse("dashboard_rtl.html", context)

# Auth routes - Hebrew RTL by default
@router.get("/login", response_class=HTMLResponse, name="login")
async def login_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Login page - Hebrew RTL"""
    # Redirect if already logged in
    if user:
        return RedirectResponse(url="/dashboard", status_code=HTTP_302_FOUND)
    
    context = get_template_context(request, user)
    return templates.TemplateResponse("auth/login_rtl.html", context)

@router.get("/register", response_class=HTMLResponse, name="register")
async def register_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Registration page - Hebrew RTL"""
    # Redirect if already logged in
    if user:
        return RedirectResponse(url="/dashboard", status_code=HTTP_302_FOUND)
    
    context = get_template_context(request, user)
    return templates.TemplateResponse("auth/register_rtl.html", context)

@router.get("/logout", response_class=HTMLResponse, name="logout")
async def logout_page(request: Request):
    """Logout page - redirect to home with logout message"""
    response = RedirectResponse(url="/", status_code=HTTP_302_FOUND)
    # In a real app, you would clear the JWT token here
    # For now, we rely on client-side JavaScript to clear localStorage
    return response

# Memorial routes - Hebrew RTL
@router.get("/memorials", response_class=HTMLResponse, name="memorials_list")
async def memorials_list(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Memorials list page - Hebrew RTL"""
    if not user:
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    
    context = get_template_context(request, user)
    return templates.TemplateResponse("memorial/list_rtl.html", context)

@router.get("/memorials/create", response_class=HTMLResponse, name="create_memorial")
async def create_memorial_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Create memorial page - Hebrew RTL"""
    if not user:
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    
    context = get_template_context(request, user)
    return templates.TemplateResponse("memorial/create_rtl.html", context)

@router.get("/memorials/{memorial_id}/edit", response_class=HTMLResponse, name="edit_memorial")
async def edit_memorial_page(
    memorial_id: str,
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Edit memorial page - Hebrew RTL"""
    if not user:
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    
    context = get_template_context(request, user)
    context["memorial_id"] = memorial_id
    return templates.TemplateResponse("memorial/create_rtl.html", context)  # Reuse create_rtl template for now

@router.get("/memorials/{slug}/public", response_class=HTMLResponse, name="public_memorial")
async def public_memorial_page(
    slug: str,
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Public memorial page - Hebrew RTL"""
    context = get_template_context(request, user)
    context["memorial_slug"] = slug
    return templates.TemplateResponse("memorial/public_rtl.html", context)

# Profile routes
@router.get("/profile", response_class=HTMLResponse, name="profile")
async def profile_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """User profile page - Hebrew RTL"""
    if not user:
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    
    context = get_template_context(request, user)
    return templates.TemplateResponse("auth/profile_rtl.html", context)

@router.get("/settings", response_class=HTMLResponse, name="settings")
async def settings_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """User settings page - Hebrew RTL"""
    if not user:
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    
    context = get_template_context(request, user)
    return templates.TemplateResponse("auth/settings_rtl.html", context)

# Search routes
@router.get("/search", response_class=HTMLResponse, name="search")
async def search_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Search memorials page - Hebrew RTL"""
    context = get_template_context(request, user)
    return templates.TemplateResponse("memorial/search_rtl.html", context)

# Help and info routes
@router.get("/help/{topic}", response_class=HTMLResponse, name="help")
async def help_page(
    topic: str,
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Help pages"""
    context = get_template_context(request, user)
    context["help_topic"] = topic
    
    # Try to render specific help template
    try:
        return templates.TemplateResponse(f"help/{topic}.html", context)
    except:
        # Fallback to generic help page
        return templates.TemplateResponse("help/index.html", context)

@router.get("/about", response_class=HTMLResponse, name="about")
async def about_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """About page"""
    context = get_template_context(request, user)
    return templates.TemplateResponse("static/about.html", context)

@router.get("/privacy", response_class=HTMLResponse, name="privacy")
async def privacy_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Privacy policy page"""
    context = get_template_context(request, user)
    return templates.TemplateResponse("static/privacy.html", context)

@router.get("/terms", response_class=HTMLResponse, name="terms")
async def terms_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Terms of service page"""
    context = get_template_context(request, user)
    return templates.TemplateResponse("static/terms.html", context)

# Demo route
@router.get("/demo", response_class=HTMLResponse, name="demo")
async def demo_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Demo page"""
    context = get_template_context(request, user)
    return templates.TemplateResponse("demo.html", context)

# Password reset routes
@router.get("/forgot-password", response_class=HTMLResponse, name="forgot_password")
async def forgot_password_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Forgot password page - Hebrew RTL"""
    if user:
        return RedirectResponse(url="/dashboard", status_code=HTTP_302_FOUND)
    
    context = get_template_context(request, user)
    return templates.TemplateResponse("auth/forgot_password_rtl.html", context)

@router.get("/reset-password", response_class=HTMLResponse, name="reset_password")
async def reset_password_page(
    request: Request,
    token: Optional[str] = None,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Reset password page - Hebrew RTL"""
    if user:
        return RedirectResponse(url="/dashboard", status_code=HTTP_302_FOUND)
    
    if not token:
        return RedirectResponse(url="/forgot-password", status_code=HTTP_302_FOUND)
    
    context = get_template_context(request, user)
    context["reset_token"] = token
    return templates.TemplateResponse("auth/reset_password_rtl.html", context)

# Email verification
@router.get("/verify-email", response_class=HTMLResponse, name="verify_email")
async def verify_email_page(
    request: Request,
    token: Optional[str] = None,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Email verification page - Hebrew RTL"""
    from app.services.auth import get_auth_service
    
    context = get_template_context(request, user)
    
    if token:
        try:
            # Process the email verification
            auth_service = get_auth_service()
            verified_user = await auth_service.verify_email(db, token)
            
            if verified_user:
                context["verification_success"] = True
                context["message"] = "כתובת האימייל שלך אומתה בהצלחה! אתה יכול כעת להתחבר."  # "Your email has been verified successfully! You can now login."
                context["user_name"] = verified_user.first_name
            else:
                context["verification_success"] = False
                context["error"] = "קישור האימות לא תקין או פג תוקפו. אנא בקש קישור חדש."  # "Verification link is invalid or expired. Please request a new link."
                
        except Exception as e:
            context["verification_success"] = False
            context["error"] = "אירעה שגיאה באימות האימייל. אנא נסה שוב."  # "An error occurred during email verification. Please try again."
    else:
        context["verification_success"] = None
        context["error"] = "לא הוזן טוקן אימות."  # "No verification token provided."
    
    context["verification_token"] = token
    return templates.TemplateResponse("auth/verify_email_rtl.html", context)

# Auth prefix email verification (for email links)
@router.get("/auth/verify-email", response_class=HTMLResponse, name="auth_verify_email")  
async def auth_verify_email_page(
    request: Request,
    token: Optional[str] = None,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Email verification page with /auth/ prefix - Hebrew RTL"""
    # Redirect to the main verify-email handler
    return await verify_email_page(request, token, user, db)

# Hebrew testing routes
@router.get("/test/hebrew", response_class=HTMLResponse, name="hebrew_test")
async def hebrew_test_page(request: Request):
    """
    Hebrew functionality testing page.
    
    This page provides comprehensive testing for all Hebrew features:
    - Hebrew name analysis
    - Psalm 119 verse selection
    - Hebrew alphabet display
    - Hebrew search functionality  
    - RTL layout testing
    - API health checks
    """
    context = get_template_context(request)
    return templates.TemplateResponse("test/hebrew_test.html", context)

# Hebrew RTL templates routes
@router.get("/hebrew", response_class=HTMLResponse, name="hebrew_home")
async def hebrew_home(
    request: Request, 
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Hebrew home page - RTL layout"""
    context = get_template_context(request, user)
    
    # If user is logged in, show Hebrew dashboard, otherwise show Hebrew landing page
    if user:
        return templates.TemplateResponse("dashboard_rtl.html", context)
    else:
        return templates.TemplateResponse("index_rtl.html", context)

@router.get("/hebrew/login", response_class=HTMLResponse, name="hebrew_login")
async def hebrew_login_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Hebrew login page - RTL"""
    # Redirect if already logged in
    if user:
        return RedirectResponse(url="/hebrew", status_code=HTTP_302_FOUND)
    
    context = get_template_context(request, user)
    return templates.TemplateResponse("auth/login_rtl.html", context)

@router.get("/hebrew/register", response_class=HTMLResponse, name="hebrew_register")
async def hebrew_register_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Hebrew registration page - RTL"""
    # Redirect if already logged in
    if user:
        return RedirectResponse(url="/hebrew", status_code=HTTP_302_FOUND)
    
    context = get_template_context(request, user)
    return templates.TemplateResponse("auth/register_rtl.html", context)

@router.get("/hebrew/memorials", response_class=HTMLResponse, name="hebrew_memorials_list")
async def hebrew_memorials_list(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Hebrew memorials list page - RTL"""
    if not user:
        return RedirectResponse(url="/hebrew/login", status_code=HTTP_302_FOUND)
    
    context = get_template_context(request, user)
    return templates.TemplateResponse("memorial/list_rtl.html", context)

@router.get("/hebrew/memorials/create", response_class=HTMLResponse, name="hebrew_create_memorial")
async def hebrew_create_memorial_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Hebrew create memorial page - RTL"""
    if not user:
        return RedirectResponse(url="/hebrew/login", status_code=HTTP_302_FOUND)
    
    context = get_template_context(request, user)
    return templates.TemplateResponse("memorial/create_rtl.html", context)

# Hebrew routes with /he/ prefix (matching template links)
@router.get("/he", response_class=HTMLResponse, name="he_home")
async def he_home_page(
    request: Request, 
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Hebrew home page - /he/ prefix"""
    context = get_template_context(request, user)
    
    # If user is logged in, show Hebrew dashboard, otherwise show Hebrew landing page
    if user:
        return templates.TemplateResponse("dashboard_rtl.html", context)
    else:
        return templates.TemplateResponse("index_rtl.html", context)

@router.get("/he/login", response_class=HTMLResponse, name="he_login")
async def he_login_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
    error: Optional[str] = None
):
    """Hebrew login page with comprehensive error handling"""
    from app.core.security import create_bulletproof_redirect
    
    # If user is already authenticated, redirect to dashboard
    if user:
        logger.info(f"Authenticated user {user.id} redirected from login to dashboard")
        return create_bulletproof_redirect("/he/dashboard")
    
    # Prepare context with error handling
    context = get_template_context(request, user)
    
    # Handle error messages
    error_messages = {
        "invalid_credentials": "כתובת הדוא״ל או הסיסמה שגויים. אנא נסו שוב.",
        "missing_credentials": "אנא מלאו את כתובת הדוא״ל והסיסמה.", 
        "account_inactive": "החשבון שלכם אינו פעיל. אנא צרו קשר עם התמיכה.",
        "session_expired": "הפעלה פגה. אנא התחברו מחדש.",
        "server_error": "אירעה שגיאה בשרת. אנא נסו שוב מאוחר יותר."
    }
    
    if error and error in error_messages:
        context["error_message"] = error_messages[error]
        context["error_code"] = error
        logger.info(f"Login page displayed with error: {error}")
    
    # Add debugging information in development
    if request.app.state.settings.DEBUG if hasattr(request.app.state, 'settings') else True:
        context["debug_info"] = {
            "has_access_token_cookie": bool(request.cookies.get('access_token')),
            "has_refresh_token_cookie": bool(request.cookies.get('refresh_token')),
            "has_session_token": bool(hasattr(request, 'session') and request.session.get('access_token')),
            "client_ip": request.client.host if request.client else "unknown"
        }
    
    response = templates.TemplateResponse("auth/login_rtl.html", context)
    
    # Ensure login page is not cached
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    
    return response

@router.post("/he/login", name="he_login_form")
async def he_login_form(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    remember_me: bool = Form(False),
    db: AsyncSession = Depends(get_db)
):
    """Hebrew login form handler with bulletproof cookie authentication"""
    from app.services.auth import get_auth_service
    from app.core.config import get_settings
    from app.core.security import set_secure_auth_cookie
    
    auth_service = get_auth_service()
    settings = get_settings()
    
    # Validation
    if not email or not password:
        return RedirectResponse(url="/he/login?error=missing_credentials", status_code=302)
    
    # Authenticate user
    user = await auth_service.authenticate_user(db=db, email=email.lower().strip(), password=password)
    
    if not user or not user.is_active:
        return RedirectResponse(url="/he/login?error=invalid_credentials", status_code=302)
    
    # Create tokens
    token_data = auth_service.create_token_pair(str(user.id))
    
    # Create redirect response
    response = RedirectResponse(url="/he/dashboard", status_code=302)
    
    # Set secure authentication cookies with proper configuration
    access_token_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    set_secure_auth_cookie(
        response=response,
        key="access_token",
        value=token_data["access_token"],
        max_age=access_token_max_age,
        httponly=True,
        secure=not settings.DEBUG,  # Use secure in production
        samesite="lax",
        path="/"
    )
    
    # Set refresh token if remember me is checked
    if remember_me:
        refresh_token_max_age = 7 * 24 * 60 * 60  # 7 days in seconds
        set_secure_auth_cookie(
            response=response,
            key="refresh_token",
            value=token_data["refresh_token"],
            max_age=refresh_token_max_age,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
            path="/"
        )
    
    logger.info(f"User {user.id} successfully logged in with secure cookies set")
    return response

@router.get("/he/register", response_class=HTMLResponse, name="he_register")
async def he_register_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Hebrew registration page - /he/ prefix"""
    if user:
        return RedirectResponse(url="/he", status_code=HTTP_302_FOUND)
    
    context = get_template_context(request, user)
    return templates.TemplateResponse("auth/register_rtl.html", context)

@router.get("/he/memorial/new", response_class=HTMLResponse, name="he_create_memorial")
async def he_create_memorial_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Hebrew create memorial page - /he/ prefix"""
    if not user:
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    
    context = get_template_context(request, user)
    return templates.TemplateResponse("memorial/create_rtl.html", context)

@router.get("/he/search", response_class=HTMLResponse, name="he_search")
async def he_search_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Hebrew search page - /he/ prefix"""
    context = get_template_context(request, user)
    return templates.TemplateResponse("memorial/list_rtl.html", context)  # Use list template for now

@router.get("/he/alphabet", response_class=HTMLResponse, name="he_alphabet")
async def he_alphabet_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Hebrew alphabet page - /he/ prefix"""
    context = get_template_context(request, user)
    return templates.TemplateResponse("test/hebrew_test.html", context)  # Use Hebrew test page

@router.get("/he/dashboard", response_class=HTMLResponse, name="he_dashboard")
async def he_dashboard_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Simple Hebrew dashboard page"""
    
    # Simple authentication check
    if not user:
        return RedirectResponse(url="/he/login", status_code=302)
    
    if not user.is_active:
        return RedirectResponse(url="/he/login?error=account_inactive", status_code=302)
    
    # User is authenticated and active - show dashboard
    context = get_template_context(request, user)
    return templates.TemplateResponse("dashboard_rtl.html", context)

@router.get("/he/memorials", response_class=HTMLResponse, name="he_memorials_list")
@router.get("/he/my-memorials", response_class=HTMLResponse, name="he_my_memorials")
async def he_memorials_list_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Hebrew memorials list page - /he/ prefix"""
    if not user:
        return RedirectResponse(url="/he/login", status_code=HTTP_302_FOUND)
    
    context = get_template_context(request, user)
    return templates.TemplateResponse("memorial/list_rtl.html", context)

# Memorial viewing routes (CRITICAL FIX)
@router.get("/memorial/{slug}", response_class=HTMLResponse, name="view_memorial")
async def view_memorial(
    slug: str,
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """View memorial page by slug - Hebrew RTL"""
    context = get_template_context(request, user)
    context["memorial_slug"] = slug
    return templates.TemplateResponse("memorial/view_rtl.html", context)

@router.get("/he/memorial/{slug}", response_class=HTMLResponse, name="he_view_memorial") 
async def he_view_memorial(
    slug: str,
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Hebrew view memorial page by slug - /he/ prefix"""
    context = get_template_context(request, user)
    context["memorial_slug"] = slug
    return templates.TemplateResponse("memorial/view_rtl.html", context)