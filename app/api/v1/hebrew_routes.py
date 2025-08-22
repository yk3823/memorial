"""
Hebrew Memorial API Routes
Handles Hebrew name to Psalm 119 verse mapping and Hebrew-specific functionality.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from pydantic import BaseModel, Field, validator
import logging

from app.core.database import get_db
from app.models.psalm_119 import Psalm119Letter, Psalm119Verse
from app.models.memorial import Memorial
from app.services.hebrew_name_service import get_hebrew_name_service, HebrewNameService
from app.services.hebrew_calendar import get_hebrew_calendar_service
from app.schemas.memorial import MemorialCreate, MemorialResponse

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/hebrew", tags=["Hebrew Memorial"])

# Pydantic models for requests and responses
class HebrewNameRequest(BaseModel):
    """Request model for Hebrew name processing."""
    name: str = Field(..., description="Hebrew name to process")
    verses_per_letter: int = Field(default=1, ge=1, le=8, description="Number of verses per letter")
    include_neshama: bool = Field(default=True, description="Include נשמה (soul) verses")
    selection_method: str = Field(default="balanced", regex="^(balanced|sequential|random)$", description="Verse selection method")
    
    @validator('name')
    def validate_hebrew_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Hebrew name cannot be empty')
        
        # Basic Hebrew character validation
        import re
        if not re.search(r'[\u05D0-\u05EA]', v):
            raise ValueError('Name must contain Hebrew letters')
        
        return v.strip()

class VerseResponse(BaseModel):
    """Response model for verse data."""
    id: int
    verse_number: int
    hebrew_text: str
    english_text: str
    transliteration: str
    verse_reference: str
    section_info: str
    letter: Dict[str, Any]
    selection_reason: Optional[str] = None

class NameVerseResponse(BaseModel):
    """Response model for name-to-verse mapping."""
    original_name: str
    normalized_name: str
    letter_positions: List[int]
    verse_selections: List[VerseResponse]
    special_verses: List[VerseResponse]
    total_verses: int
    summary: Dict[str, int]

class HebrewLetterResponse(BaseModel):
    """Response model for Hebrew letter data."""
    id: int
    hebrew_letter: str
    hebrew_name: str
    english_name: str
    position: int
    numeric_value: int
    usage_count: int
    verse_count: int

class HebrewDateResponse(BaseModel):
    """Response model for Hebrew date."""
    day: int
    month_name: str
    year: int
    formatted: str

# API Endpoints

@router.get("/name-verses", response_model=NameVerseResponse, summary="Get Psalm verses for Hebrew name")
async def get_verses_for_hebrew_name(
    name: str = Query(..., description="Hebrew name"),
    verses_per_letter: int = Query(default=1, ge=1, le=8, description="Verses per letter"),
    include_neshama: bool = Query(default=True, description="Include נשמה verses"),
    selection_method: str = Query(default="balanced", regex="^(balanced|sequential|random)$", description="Selection method"),
    db: AsyncSession = Depends(get_db)
) -> NameVerseResponse:
    """
    Get Psalm 119 verses for a Hebrew name.
    
    This endpoint maps each Hebrew letter in a name to corresponding verses from Psalm 119,
    following traditional Jewish memorial practices.
    """
    try:
        hebrew_service = get_hebrew_name_service()
        
        # Get verse mapping for the name
        verse_mapping = await hebrew_service.get_verses_for_name(
            name, 
            verses_per_letter=verses_per_letter,
            include_neshama=include_neshama,
            selection_method=selection_method
        )
        
        # Convert to response format
        verse_selections = []
        for verse_data in verse_mapping.verse_selections:
            verse_selections.append(VerseResponse(**verse_data))
        
        special_verses = []
        for verse_data in verse_mapping.special_verses:
            special_verses.append(VerseResponse(**verse_data))
        
        response = NameVerseResponse(
            original_name=verse_mapping.original_name,
            normalized_name=verse_mapping.normalized_name,
            letter_positions=verse_mapping.letter_positions,
            verse_selections=verse_selections,
            special_verses=special_verses,
            total_verses=verse_mapping.total_verses,
            summary={
                "name_length": len(verse_mapping.normalized_name),
                "unique_letters": len(set(verse_mapping.letter_positions)),
                "total_selected_verses": len(verse_selections) + len(special_verses)
            }
        )
        
        logger.info(f"Successfully processed Hebrew name: {name}")
        return response
        
    except ValueError as e:
        logger.warning(f"Invalid Hebrew name: {name}, error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing Hebrew name {name}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error processing Hebrew name")

@router.post("/validate-name", summary="Validate Hebrew name")
async def validate_hebrew_name(
    request: HebrewNameRequest
) -> Dict[str, Any]:
    """
    Validate a Hebrew name and return validation results.
    """
    try:
        hebrew_service = get_hebrew_name_service()
        
        is_valid, error_message = hebrew_service.validate_hebrew_name(request.name)
        
        response = {
            "name": request.name,
            "is_valid": is_valid,
            "error_message": error_message,
            "normalized_name": hebrew_service.normalize_hebrew_name(request.name) if is_valid else None
        }
        
        if is_valid:
            # Add letter analysis
            normalized = hebrew_service.normalize_hebrew_name(request.name)
            letter_positions = hebrew_service.get_letter_positions(normalized)
            
            response.update({
                "letter_count": len(normalized),
                "unique_letters": len(set(letter_positions)),
                "letter_positions": letter_positions,
                "estimated_verses": len(set(letter_positions)) * request.verses_per_letter
            })
        
        return response
        
    except Exception as e:
        logger.error(f"Error validating Hebrew name: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error validating Hebrew name")

@router.get("/alphabet", response_model=List[HebrewLetterResponse], summary="Get Hebrew alphabet with Psalm 119 mapping")
async def get_hebrew_alphabet(
    include_usage_stats: bool = Query(default=True, description="Include usage statistics"),
    db: AsyncSession = Depends(get_db)
) -> List[HebrewLetterResponse]:
    """
    Get the Hebrew alphabet with Psalm 119 letter mappings and usage statistics.
    """
    try:
        query = select(Psalm119Letter).order_by(Psalm119Letter.position)
        result = await db.execute(query)
        letters = result.scalars().all()
        
        alphabet_data = []
        for letter in letters:
            # Count verses for this letter
            verse_count_query = select(func.count(Psalm119Verse.id)).where(
                Psalm119Verse.letter_id == letter.id
            )
            verse_count_result = await db.execute(verse_count_query)
            verse_count = verse_count_result.scalar()
            
            alphabet_data.append(HebrewLetterResponse(
                id=letter.id,
                hebrew_letter=letter.hebrew_letter,
                hebrew_name=letter.hebrew_name,
                english_name=letter.english_name,
                position=letter.position,
                numeric_value=letter.numeric_value,
                usage_count=letter.usage_count if include_usage_stats else 0,
                verse_count=verse_count
            ))
        
        logger.info(f"Retrieved Hebrew alphabet with {len(alphabet_data)} letters")
        return alphabet_data
        
    except Exception as e:
        logger.error(f"Error retrieving Hebrew alphabet: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving Hebrew alphabet")

@router.get("/letter/{letter_id}/verses", summary="Get verses for specific Hebrew letter")
async def get_verses_for_letter(
    letter_id: int,
    limit: int = Query(default=8, ge=1, le=8, description="Number of verses to return"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get Psalm 119 verses for a specific Hebrew letter.
    """
    try:
        # Get the letter
        letter_query = select(Psalm119Letter).where(Psalm119Letter.id == letter_id)
        letter_result = await db.execute(letter_query)
        letter = letter_result.scalar_one_or_none()
        
        if not letter:
            raise HTTPException(status_code=404, detail=f"Hebrew letter with ID {letter_id} not found")
        
        # Get verses for this letter
        verses_query = (
            select(Psalm119Verse)
            .where(Psalm119Verse.letter_id == letter_id)
            .order_by(Psalm119Verse.verse_in_section)
            .limit(limit)
        )
        verses_result = await db.execute(verses_query)
        verses = verses_result.scalars().all()
        
        verses_data = []
        for verse in verses:
            verse_dict = verse.to_dict(include_letter=True, language_preference="hebrew")
            verses_data.append(verse_dict)
        
        response = {
            "letter": letter.to_dict(),
            "verses": verses_data,
            "total_verses": len(verses),
            "verse_range": f"{letter.position * 8 - 7}-{letter.position * 8}"
        }
        
        logger.info(f"Retrieved {len(verses)} verses for Hebrew letter {letter.hebrew_letter}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving verses for letter {letter_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving verses for letter")

@router.get("/popular-names", summary="Get popular Hebrew names with statistics")
async def get_popular_hebrew_names(
    limit: int = Query(default=20, ge=1, le=100, description="Number of names to return"),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get popular Hebrew names and their verse statistics.
    """
    try:
        hebrew_service = get_hebrew_name_service()
        popular_names = await hebrew_service.get_popular_name_patterns(limit)
        
        logger.info(f"Retrieved {len(popular_names)} popular Hebrew names")
        return popular_names
        
    except Exception as e:
        logger.error(f"Error retrieving popular names: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving popular Hebrew names")

@router.get("/date/convert", response_model=HebrewDateResponse, summary="Convert date to Hebrew calendar")
async def convert_to_hebrew_date(
    year: int = Query(..., ge=1, description="Gregorian year"),
    month: int = Query(..., ge=1, le=12, description="Gregorian month"),
    day: int = Query(..., ge=1, le=31, description="Gregorian day")
) -> HebrewDateResponse:
    """
    Convert a Gregorian date to Hebrew calendar date.
    """
    try:
        hebrew_calendar_service = get_hebrew_calendar_service()
        hebrew_date = hebrew_calendar_service.gregorian_to_hebrew(year, month, day)
        
        response = HebrewDateResponse(
            day=hebrew_date["day"],
            month_name=hebrew_date["month_name"],
            year=hebrew_date["year"],
            formatted=f"{hebrew_date['day']} {hebrew_date['month_name']} {hebrew_date['year']}"
        )
        
        logger.info(f"Converted {year}-{month}-{day} to Hebrew date: {response.formatted}")
        return response
        
    except ValueError as e:
        logger.warning(f"Invalid date conversion: {year}-{month}-{day}, error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error converting date: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error converting date to Hebrew calendar")

@router.get("/statistics", summary="Get Hebrew memorial statistics")
async def get_hebrew_statistics(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive statistics about Hebrew names and verses usage.
    """
    try:
        hebrew_service = get_hebrew_name_service()
        
        # Get letter usage statistics
        letter_stats = await hebrew_service.get_letter_usage_statistics()
        
        # Get total counts
        total_letters_query = select(func.count(Psalm119Letter.id))
        total_letters_result = await db.execute(total_letters_query)
        total_letters = total_letters_result.scalar()
        
        total_verses_query = select(func.count(Psalm119Verse.id))
        total_verses_result = await db.execute(total_verses_query)
        total_verses = total_verses_result.scalar()
        
        # Get memorial count (if Memorial model exists)
        try:
            total_memorials_query = select(func.count(Memorial.id))
            total_memorials_result = await db.execute(total_memorials_query)
            total_memorials = total_memorials_result.scalar()
        except:
            total_memorials = 0
        
        # Most used verses
        most_used_verses_query = (
            select(Psalm119Verse)
            .order_by(Psalm119Verse.usage_count.desc())
            .limit(5)
        )
        most_used_result = await db.execute(most_used_verses_query)
        most_used_verses = most_used_result.scalars().all()
        
        statistics = {
            "totals": {
                "hebrew_letters": total_letters,
                "psalm_verses": total_verses,
                "memorials_created": total_memorials
            },
            "letter_statistics": letter_stats,
            "most_used_verses": [
                {
                    "verse_number": verse.verse_number,
                    "hebrew_text": verse.hebrew_text[:100] + "..." if len(verse.hebrew_text) > 100 else verse.hebrew_text,
                    "usage_count": verse.usage_count,
                    "letter": verse.letter.hebrew_letter if verse.letter else None
                }
                for verse in most_used_verses
            ],
            "psalm_119_info": {
                "total_verses": 176,
                "letters_per_section": 22,
                "verses_per_letter": 8,
                "description": "תהילים קיט - הפרק הארוך ביותר בתנ\"ך"
            }
        }
        
        logger.info("Generated comprehensive Hebrew statistics")
        return statistics
        
    except Exception as e:
        logger.error(f"Error generating statistics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating Hebrew statistics")

@router.post("/search-verses", summary="Search verses by text content")
async def search_verses(
    query: str = Query(..., min_length=2, description="Search query"),
    search_hebrew: bool = Query(default=True, description="Search in Hebrew text"),
    search_english: bool = Query(default=True, description="Search in English text"),
    search_transliteration: bool = Query(default=False, description="Search in transliteration"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum results to return"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Search Psalm 119 verses by text content in Hebrew, English, or transliteration.
    """
    try:
        # Build search conditions
        conditions = []
        
        if search_hebrew:
            conditions.append(Psalm119Verse.hebrew_text.ilike(f'%{query}%'))
            conditions.append(Psalm119Verse.hebrew_text_no_vowels.ilike(f'%{query}%'))
        
        if search_english:
            conditions.append(Psalm119Verse.english_text.ilike(f'%{query}%'))
        
        if search_transliteration:
            conditions.append(Psalm119Verse.transliteration.ilike(f'%{query}%'))
        
        if not conditions:
            raise HTTPException(status_code=400, detail="At least one search option must be enabled")
        
        # Execute search query
        search_query = (
            select(Psalm119Verse)
            .where(func.or_(*conditions))
            .order_by(Psalm119Verse.verse_number)
            .limit(limit)
        )
        
        result = await db.execute(search_query)
        verses = result.scalars().all()
        
        # Format results
        search_results = []
        for verse in verses:
            verse_dict = verse.to_dict(include_letter=True, language_preference="hebrew")
            
            # Add search relevance info
            relevance_info = []
            if search_hebrew and (query.lower() in verse.hebrew_text.lower() or 
                                (verse.hebrew_text_no_vowels and query.lower() in verse.hebrew_text_no_vowels.lower())):
                relevance_info.append("עברית")
            if search_english and query.lower() in verse.english_text.lower():
                relevance_info.append("אנגלית")
            if search_transliteration and query.lower() in verse.transliteration.lower():
                relevance_info.append("תעתיק")
            
            verse_dict['search_relevance'] = relevance_info
            search_results.append(verse_dict)
        
        response = {
            "query": query,
            "total_results": len(search_results),
            "search_options": {
                "hebrew": search_hebrew,
                "english": search_english,
                "transliteration": search_transliteration
            },
            "results": search_results
        }
        
        logger.info(f"Search for '{query}' returned {len(search_results)} results")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching verses: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error searching verses")

# Background tasks for analytics
@router.post("/track-usage", summary="Track Hebrew name usage")
async def track_hebrew_name_usage(
    background_tasks: BackgroundTasks,
    name: str,
    action: str = Query(..., regex="^(search|memorial_create|view)$", description="Action type"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Track usage of Hebrew names for analytics (background task).
    """
    async def update_usage_stats():
        try:
            hebrew_service = get_hebrew_name_service()
            
            # Normalize name and get letter positions
            normalized_name = hebrew_service.normalize_hebrew_name(name)
            letter_positions = hebrew_service.get_letter_positions(normalized_name)
            
            # Update letter usage counts
            for position in set(letter_positions):  # Unique positions only
                letter_query = select(Psalm119Letter).where(Psalm119Letter.position == position)
                letter_result = await db.execute(letter_query)
                letter = letter_result.scalar_one_or_none()
                
                if letter:
                    letter.usage_count += 1
            
            await db.commit()
            logger.info(f"Updated usage statistics for name: {name}, action: {action}")
            
        except Exception as e:
            logger.error(f"Error updating usage statistics: {str(e)}", exc_info=True)
    
    background_tasks.add_task(update_usage_stats)
    
    return {"status": "success", "message": "Usage tracking queued"}

# Health check endpoint

@router.get("/health", summary="Hebrew API health check")
async def hebrew_api_health(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Check the health of Hebrew-specific API components.
    """
    try:
        # Test database connectivity
        test_query = select(func.count(Psalm119Letter.id))
        result = await db.execute(test_query)
        letter_count = result.scalar()
        
        # Test Hebrew name service
        hebrew_service = get_hebrew_name_service()
        test_validation = hebrew_service.validate_hebrew_name("דוד")
        
        # Test Hebrew calendar service
        hebrew_calendar_service = get_hebrew_calendar_service()
        test_date = hebrew_calendar_service.gregorian_to_hebrew(2024, 1, 1)
        
        health_status = {
            "status": "healthy",
            "database": "connected",
            "hebrew_letters_count": letter_count,
            "hebrew_name_service": "functional" if test_validation[0] else "error",
            "hebrew_calendar_service": "functional" if test_date else "error",
            "timestamp": func.now()
        }
        
        logger.info("Hebrew API health check completed successfully")
        return health_status
        
    except Exception as e:
        logger.error(f"Hebrew API health check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Hebrew API health check failed: {str(e)}")