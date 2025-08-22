"""
Test routes for Hebrew functionality testing.
Development and testing endpoints for the Hebrew memorial website.
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/test/hebrew", response_class=HTMLResponse)
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
    return templates.TemplateResponse("test/hebrew_test.html", {"request": request})


@router.get("/test/verse-selection", response_class=HTMLResponse)
async def verse_selection_test_page(request: Request, db: AsyncSession = Depends(get_database)):
    """
    Dedicated verse selection algorithm testing page.
    
    Focused testing page for the Hebrew name to verse selection algorithm
    with detailed debugging information and multiple test scenarios.
    """
    return templates.TemplateResponse("test/verse_selection_test.html", {
        "request": request,
        "title": "בדיקת אלגוריתם בחירת פסוקים"
    })


@router.get("/test/api-docs", response_class=HTMLResponse) 
async def api_documentation_test(request: Request):
    """
    Interactive API documentation and testing interface.
    
    Hebrew-language API documentation with live testing capabilities
    for all Hebrew-specific endpoints.
    """
    return templates.TemplateResponse("test/api_docs_test.html", {
        "request": request,
        "title": "תיעוד API עברי"
    })


@router.get("/test/rtl-layout", response_class=HTMLResponse)
async def rtl_layout_test(request: Request):
    """
    RTL layout and Hebrew typography testing page.
    
    Comprehensive testing of right-to-left layout, Hebrew fonts,
    text direction, and mixed Hebrew/English content display.
    """
    return templates.TemplateResponse("test/rtl_layout_test.html", {
        "request": request,
        "title": "בדיקת פריסת RTL"
    })