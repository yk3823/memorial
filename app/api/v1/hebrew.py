"""
Hebrew-specific API endpoints for Memorial Website.
Handles Hebrew names, Psalm 119 verses, and RTL functionality.
"""

import re
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.core.database import get_database
from app.models.psalm_119 import Psalm119Letter, Psalm119Verse
from app.models.memorial import Memorial
from app.schemas.hebrew import (
    HebrewNameAnalysisResponse,
    NameVersesResponse,
    HebrewLetterResponse,
    AlphabetResponse,
    VerseSelectionRequest,
    HebrewSearchRequest,
    HebrewSearchResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hebrew", tags=["Hebrew"])

# Hebrew letter mapping for final forms (sofit letters)
SOFIT_MAPPING = {
    'ץ': 'צ',  # Tzade sofit -> Tzade
    'ך': 'כ',  # Kaf sofit -> Kaf  
    'ן': 'נ',  # Nun sofit -> Nun
    'ם': 'מ',  # Mem sofit -> Mem
    'ף': 'פ'   # Pe sofit -> Pe
}

# Hebrew letter validation regex
HEBREW_REGEX = re.compile(r'^[\u0590-\u05FF\s]*$')
HEBREW_LETTERS_REGEX = re.compile(r'[\u05D0-\u05EA]')

# Common Hebrew words for "soul" (neshama)
NESHAMA_LETTERS = ['נ', 'ש', 'מ', 'ה']


def extract_hebrew_letters(text: str) -> List[str]:
    """Extract Hebrew letters from text, handling sofit forms."""
    if not text or not HEBREW_REGEX.match(text.strip()):
        return []
    
    letters = HEBREW_LETTERS_REGEX.findall(text)
    # Convert sofit letters to their regular forms
    normalized_letters = [SOFIT_MAPPING.get(letter, letter) for letter in letters]
    return normalized_letters


def is_valid_hebrew_text(text: str) -> bool:
    """Check if text contains only Hebrew characters and whitespace."""
    if not text or not text.strip():
        return False
    return HEBREW_REGEX.match(text.strip()) is not None


@router.get("/alphabet", response_model=AlphabetResponse)
async def get_hebrew_alphabet(
    include_verses: bool = Query(False, description="Include sample verses for each letter"),
    verses_per_letter: int = Query(1, description="Number of sample verses per letter"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get the complete Hebrew alphabet with Psalm 119 information.
    
    Returns all 22 Hebrew letters with their names, numeric values,
    and optionally sample verses from each letter's section.
    """
    try:
        # Get all Hebrew letters ordered by position
        query = select(Psalm119Letter).order_by(Psalm119Letter.position)
        result = await db.execute(query)
        letters = result.scalars().all()
        
        if not letters:
            raise HTTPException(status_code=404, detail="Hebrew alphabet not found in database")
        
        letters_data = []
        for letter in letters:
            letter_data = HebrewLetterResponse(
                id=letter.id,
                hebrew_letter=letter.hebrew_letter,
                hebrew_name=letter.hebrew_name,
                english_name=letter.english_name,
                transliteration=letter.transliteration,
                numeric_value=letter.numeric_value,
                position=letter.position,
                usage_count=letter.usage_count,
                verses=[]
            )
            
            if include_verses:
                # Get sample verses for this letter
                verses_query = (
                    select(Psalm119Verse)
                    .where(Psalm119Verse.letter_id == letter.id)
                    .order_by(Psalm119Verse.verse_in_section)
                    .limit(verses_per_letter)
                )
                verses_result = await db.execute(verses_query)
                verses = verses_result.scalars().all()
                
                letter_data.verses = [
                    {
                        "id": verse.id,
                        "verse_number": verse.verse_number,
                        "verse_in_section": verse.verse_in_section,
                        "hebrew_text": verse.hebrew_text,
                        "english_text": verse.english_text,
                        "transliteration": verse.transliteration,
                        "verse_reference": f"תהילים קיט:{verse.verse_number}",
                        "usage_count": verse.usage_count
                    }
                    for verse in verses
                ]
            
            letters_data.append(letter_data)
        
        return AlphabetResponse(
            letters=letters_data,
            total_letters=len(letters_data),
            description="האלפבית העברי עם 22 אותיות לפי תהילים קיט"
        )
        
    except Exception as e:
        logger.error(f"Error getting Hebrew alphabet: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving Hebrew alphabet")


@router.post("/analyze-name", response_model=HebrewNameAnalysisResponse)
async def analyze_hebrew_name(
    hebrew_name: str = Query(..., description="Hebrew name to analyze"),
    db: AsyncSession = Depends(get_database)
):
    """
    Analyze a Hebrew name and return the constituent letters with their information.
    
    Takes a Hebrew name and breaks it down into its letters, providing
    information about each letter including its position in the alphabet,
    numeric value, and association with Psalm 119 sections.
    """
    if not is_valid_hebrew_text(hebrew_name):
        raise HTTPException(
            status_code=422, 
            detail="שם לא תקין - יש להזין רק אותיות עבריות"
        )
    
    try:
        letters = extract_hebrew_letters(hebrew_name)
        if not letters:
            raise HTTPException(
                status_code=422,
                detail="לא נמצאו אותיות עבריות בשם"
            )
        
        # Get unique letters to avoid duplicates
        unique_letters = list(dict.fromkeys(letters))  # Preserves order
        
        # Get letter information from database
        letters_query = select(Psalm119Letter).where(
            Psalm119Letter.hebrew_letter.in_(unique_letters)
        )
        result = await db.execute(letters_query)
        found_letters = {letter.hebrew_letter: letter for letter in result.scalars().all()}
        
        # Build response with letter details
        letter_details = []
        for letter_char in unique_letters:
            if letter_char in found_letters:
                letter = found_letters[letter_char]
                letter_details.append({
                    "hebrew_letter": letter.hebrew_letter,
                    "hebrew_name": letter.hebrew_name,
                    "english_name": letter.english_name,
                    "position": letter.position,
                    "numeric_value": letter.numeric_value,
                    "verse_count": 8,  # Each letter has 8 verses
                    "gematria_value": letter.numeric_value
                })
        
        # Calculate name statistics
        total_gematria = sum(found_letters[letter].numeric_value 
                           for letter in unique_letters 
                           if letter in found_letters)
        
        return HebrewNameAnalysisResponse(
            name=hebrew_name,
            letters=letter_details,
            total_letters=len(unique_letters),
            unique_letters=len(unique_letters),
            total_gematria_value=total_gematria,
            available_verses=len(letter_details) * 8,
            analysis_notes=f"השם '{hebrew_name}' מכיל {len(unique_letters)} אותיות ייחודיות עם ערך גימטריה כולל של {total_gematria}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing Hebrew name '{hebrew_name}': {e}")
        raise HTTPException(status_code=500, detail="שגיאה בניתוח השם העברי")


@router.get("/name-verses", response_model=NameVersesResponse)
async def get_verses_for_hebrew_name(
    name: str = Query(..., description="Hebrew name"),
    verses_per_letter: int = Query(1, ge=1, le=8, description="Number of verses per letter (1-8)"),
    include_neshama: bool = Query(True, description="Include נשמה (soul) verses"),
    selection_method: str = Query("balanced", description="Verse selection method: balanced, sequential, random"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get Psalm 119 verses specifically chosen for a Hebrew name.
    
    This endpoint implements the core algorithm:
    1. Analyze the Hebrew name to extract letters
    2. For each letter, select verses from the corresponding Psalm 119 section
    3. Optionally add נשמה (soul) verses from נ,ש,מ,ה letters
    4. Return verses with proper Hebrew, transliteration, and English
    """
    if not is_valid_hebrew_text(name):
        raise HTTPException(
            status_code=422,
            detail="שם לא תקין - יש להזין רק אותיות עבריות"
        )
    
    try:
        letters = extract_hebrew_letters(name)
        if not letters:
            raise HTTPException(
                status_code=422,
                detail="לא נמצאו אותיות עבריות בשם"
            )
        
        # Get unique letters preserving order
        unique_letters = list(dict.fromkeys(letters))
        
        # Get all verses for the name letters
        name_verses = []
        letter_info = {}
        
        for letter_char in unique_letters:
            # Get letter info
            letter_query = select(Psalm119Letter).where(
                Psalm119Letter.hebrew_letter == letter_char
            )
            letter_result = await db.execute(letter_query)
            letter = letter_result.scalar_one_or_none()
            
            if not letter:
                logger.warning(f"Letter '{letter_char}' not found in database")
                continue
                
            letter_info[letter_char] = letter
            
            # Get verses for this letter based on selection method
            if selection_method == "sequential":
                verses_query = (
                    select(Psalm119Verse)
                    .where(Psalm119Verse.letter_id == letter.id)
                    .order_by(Psalm119Verse.verse_in_section)
                    .limit(verses_per_letter)
                )
            elif selection_method == "random":
                verses_query = (
                    select(Psalm119Verse)
                    .where(Psalm119Verse.letter_id == letter.id)
                    .order_by(func.random())
                    .limit(verses_per_letter)
                )
            else:  # balanced - mix of first and random
                if verses_per_letter == 1:
                    verses_query = (
                        select(Psalm119Verse)
                        .where(Psalm119Verse.letter_id == letter.id)
                        .order_by(Psalm119Verse.verse_in_section)
                        .limit(1)
                    )
                else:
                    # Take first verse and then random ones
                    first_verse_query = (
                        select(Psalm119Verse)
                        .where(Psalm119Verse.letter_id == letter.id)
                        .order_by(Psalm119Verse.verse_in_section)
                        .limit(1)
                    )
                    remaining_verses_query = (
                        select(Psalm119Verse)
                        .where(
                            Psalm119Verse.letter_id == letter.id,
                            Psalm119Verse.verse_in_section > 1
                        )
                        .order_by(func.random())
                        .limit(verses_per_letter - 1)
                    )
                    
                    first_result = await db.execute(first_verse_query)
                    first_verses = first_result.scalars().all()
                    
                    remaining_result = await db.execute(remaining_verses_query)
                    remaining_verses = remaining_result.scalars().all()
                    
                    verses = first_verses + remaining_verses
                    for verse in verses:
                        name_verses.append({
                            "id": verse.id,
                            "verse_number": verse.verse_number,
                            "verse_in_section": verse.verse_in_section,
                            "hebrew_text": verse.hebrew_text,
                            "english_text": verse.english_text,
                            "transliteration": verse.transliteration,
                            "verse_reference": f"תהילים קיט:{verse.verse_number}",
                            "verse_reference_english": f"Psalm 119:{verse.verse_number}",
                            "letter": {
                                "hebrew_letter": letter.hebrew_letter,
                                "hebrew_name": letter.hebrew_name,
                                "english_name": letter.english_name,
                                "position": letter.position
                            },
                            "themes": verse.themes,
                            "keywords": verse.keywords,
                            "is_neshama_verse": False
                        })
                    continue
            
            # For non-balanced methods, execute the query
            verses_result = await db.execute(verses_query)
            verses = verses_result.scalars().all()
            
            for verse in verses:
                name_verses.append({
                    "id": verse.id,
                    "verse_number": verse.verse_number,
                    "verse_in_section": verse.verse_in_section,
                    "hebrew_text": verse.hebrew_text,
                    "english_text": verse.english_text,
                    "transliteration": verse.transliteration,
                    "verse_reference": f"תהילים קיט:{verse.verse_number}",
                    "verse_reference_english": f"Psalm 119:{verse.verse_number}",
                    "letter": {
                        "hebrew_letter": letter.hebrew_letter,
                        "hebrew_name": letter.hebrew_name,
                        "english_name": letter.english_name,
                        "position": letter.position
                    },
                    "themes": verse.themes,
                    "keywords": verse.keywords,
                    "is_neshama_verse": False
                })
        
        # Add נשמה (soul) verses if requested
        neshama_verses = []
        if include_neshama:
            for neshama_letter in NESHAMA_LETTERS:
                letter_query = select(Psalm119Letter).where(
                    Psalm119Letter.hebrew_letter == neshama_letter
                )
                letter_result = await db.execute(letter_query)
                letter = letter_result.scalar_one_or_none()
                
                if letter:
                    # Get one verse from each נשמה letter
                    verse_query = (
                        select(Psalm119Verse)
                        .where(Psalm119Verse.letter_id == letter.id)
                        .order_by(Psalm119Verse.verse_in_section)
                        .limit(1)
                    )
                    verse_result = await db.execute(verse_query)
                    verse = verse_result.scalar_one_or_none()
                    
                    if verse:
                        neshama_verses.append({
                            "id": verse.id,
                            "verse_number": verse.verse_number,
                            "verse_in_section": verse.verse_in_section,
                            "hebrew_text": verse.hebrew_text,
                            "english_text": verse.english_text,
                            "transliteration": verse.transliteration,
                            "verse_reference": f"תהילים קיט:{verse.verse_number}",
                            "verse_reference_english": f"Psalm 119:{verse.verse_number}",
                            "letter": {
                                "hebrew_letter": letter.hebrew_letter,
                                "hebrew_name": letter.hebrew_name,
                                "english_name": letter.english_name,
                                "position": letter.position
                            },
                            "themes": verse.themes,
                            "keywords": verse.keywords,
                            "is_neshama_verse": True
                        })
        
        # Combine all verses
        all_verses = name_verses + neshama_verses
        
        # Build name analysis
        name_analysis = {
            "name": name,
            "letters": [
                {
                    "hebrew_letter": letter_info[letter_char].hebrew_letter,
                    "hebrew_name": letter_info[letter_char].hebrew_name,
                    "english_name": letter_info[letter_char].english_name,
                    "position": letter_info[letter_char].position,
                    "numeric_value": letter_info[letter_char].numeric_value
                }
                for letter_char in unique_letters
                if letter_char in letter_info
            ],
            "total_gematria": sum(
                letter_info[letter_char].numeric_value
                for letter_char in unique_letters
                if letter_char in letter_info
            )
        }
        
        return NameVersesResponse(
            name=name,
            verses=all_verses,
            name_analysis=name_analysis,
            selection_method=selection_method,
            verses_per_letter=verses_per_letter,
            includes_neshama=include_neshama,
            total_verses=len(all_verses),
            name_verses_count=len(name_verses),
            neshama_verses_count=len(neshama_verses)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting verses for name '{name}': {e}")
        raise HTTPException(status_code=500, detail="שגיאה בטעינת פסוקים לשם")


@router.get("/search", response_model=HebrewSearchResponse)
async def search_hebrew_content(
    query: str = Query(..., description="Hebrew search query"),
    search_type: str = Query("all", description="Search type: all, memorials, verses, letters"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    include_transliteration: bool = Query(True, description="Include transliteration in verse results"),
    db: AsyncSession = Depends(get_database)
):
    """
    Search Hebrew content across memorials, verses, and letters.
    
    Supports searching in Hebrew text with proper RTL handling.
    Can search across different content types or focus on specific areas.
    """
    if not query.strip():
        raise HTTPException(status_code=422, detail="יש להזין שאילתת חיפוש")
    
    try:
        results = {
            "memorials": [],
            "verses": [],
            "letters": []
        }
        
        query_lower = query.lower().strip()
        
        # Search memorials if requested
        if search_type in ["all", "memorials"]:
            memorials_query = (
                select(Memorial)
                .where(
                    or_(
                        func.lower(Memorial.deceased_name_hebrew).like(f"%{query_lower}%"),
                        func.lower(Memorial.deceased_name_english).like(f"%{query_lower}%") if Memorial.deceased_name_english else False,
                        func.lower(Memorial.biography).like(f"%{query_lower}%") if Memorial.biography else False
                    ),
                    Memorial.is_public == True  # Only public memorials in search
                )
                .limit(limit if search_type == "memorials" else limit // 2)
            )
            
            memorials_result = await db.execute(memorials_query)
            memorials = memorials_result.scalars().all()
            
            results["memorials"] = [
                {
                    "id": memorial.id,
                    "deceased_name_hebrew": memorial.deceased_name_hebrew,
                    "deceased_name_english": memorial.deceased_name_english,
                    "death_date_hebrew": memorial.death_date_hebrew,
                    "death_date_gregorian": memorial.death_date_gregorian.isoformat() if memorial.death_date_gregorian else None,
                    "biography_excerpt": memorial.biography[:150] + "..." if memorial.biography and len(memorial.biography) > 150 else memorial.biography,
                    "public_url": memorial.public_url,
                    "page_views": memorial.page_views
                }
                for memorial in memorials
            ]
        
        # Search verses if requested
        if search_type in ["all", "verses"]:
            verses_query = (
                select(Psalm119Verse, Psalm119Letter)
                .join(Psalm119Letter, Psalm119Verse.letter_id == Psalm119Letter.id)
                .where(
                    or_(
                        func.lower(Psalm119Verse.hebrew_text).like(f"%{query_lower}%"),
                        func.lower(Psalm119Verse.english_text).like(f"%{query_lower}%"),
                        func.lower(Psalm119Verse.transliteration).like(f"%{query_lower}%"),
                        func.lower(Psalm119Verse.themes).like(f"%{query_lower}%"),
                        func.lower(Psalm119Verse.keywords).like(f"%{query_lower}%")
                    )
                )
                .limit(limit if search_type == "verses" else limit // 2)
            )
            
            verses_result = await db.execute(verses_query)
            verse_pairs = verses_result.all()
            
            results["verses"] = [
                {
                    "id": verse.id,
                    "verse_number": verse.verse_number,
                    "verse_in_section": verse.verse_in_section,
                    "hebrew_text": verse.hebrew_text,
                    "english_text": verse.english_text,
                    "transliteration": verse.transliteration if include_transliteration else None,
                    "verse_reference": f"תהילים קיט:{verse.verse_number}",
                    "letter": {
                        "hebrew_letter": letter.hebrew_letter,
                        "hebrew_name": letter.hebrew_name,
                        "english_name": letter.english_name
                    },
                    "themes": verse.themes,
                    "keywords": verse.keywords,
                    "usage_count": verse.usage_count
                }
                for verse, letter in verse_pairs
            ]
        
        # Search letters if requested
        if search_type in ["all", "letters"]:
            letters_query = (
                select(Psalm119Letter)
                .where(
                    or_(
                        func.lower(Psalm119Letter.hebrew_letter).like(f"%{query_lower}%"),
                        func.lower(Psalm119Letter.hebrew_name).like(f"%{query_lower}%"),
                        func.lower(Psalm119Letter.english_name).like(f"%{query_lower}%"),
                        func.lower(Psalm119Letter.transliteration).like(f"%{query_lower}%")
                    )
                )
                .limit(limit if search_type == "letters" else 10)
            )
            
            letters_result = await db.execute(letters_query)
            letters = letters_result.scalars().all()
            
            results["letters"] = [
                {
                    "id": letter.id,
                    "hebrew_letter": letter.hebrew_letter,
                    "hebrew_name": letter.hebrew_name,
                    "english_name": letter.english_name,
                    "transliteration": letter.transliteration,
                    "numeric_value": letter.numeric_value,
                    "position": letter.position,
                    "usage_count": letter.usage_count,
                    "verse_count": 8
                }
                for letter in letters
            ]
        
        # Calculate totals
        total_results = sum(len(results[key]) for key in results)
        
        return HebrewSearchResponse(
            query=query,
            search_type=search_type,
            results=results,
            total_results=total_results,
            has_results=total_results > 0,
            search_suggestions=generate_search_suggestions(query, total_results) if total_results == 0 else []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching Hebrew content for query '{query}': {e}")
        raise HTTPException(status_code=500, detail="שגיאה בחיפוש תוכן עברי")


def generate_search_suggestions(query: str, current_results: int) -> List[str]:
    """Generate search suggestions when no results are found."""
    suggestions = []
    
    # Basic suggestions for Hebrew searches
    if is_valid_hebrew_text(query):
        suggestions.extend([
            "נסה לחפש בפחות מילים",
            "בדוק את הכתיב העברי",
            "חפש לפי אות בודדת מהשם",
            "נסה לחפש במילים נרדפות"
        ])
    else:
        suggestions.extend([
            "נסה לחפש בעברית",
            "השתמש באותיות עבריות בלבד",
            "חפש לפי שמות עבריים",
            "נסה לחפש פסוקים מתהילים קיט"
        ])
    
    return suggestions[:3]  # Return top 3 suggestions


@router.get("/memorial-verses", response_model=Dict[str, Any])
async def get_memorial_verses_for_name(
    name: str = Query(..., description="Hebrew name for memorial"),
    db: AsyncSession = Depends(get_database)
):
    """
    MAIN ENGINE ENDPOINT - Get complete memorial verses for a Hebrew name.
    
    This is the CORE FUNCTIONALITY that provides:
    1. ALL verses for each letter in the name in Psalm 119 order
    2. ALL נשמה verses (נ,ש,מ,ה) in order
    3. Proper Hebrew ordering and structure
    
    Example: For "יוסף" returns:
    - י: All 8 verses from Yod section (73-80)
    - ו: All 8 verses from Vav section (41-48) 
    - ס: All 8 verses from Samekh section (113-120)
    - ף/פ: All 8 verses from Pe section (129-136)
    - Plus נשמה verses: נ(105-112), ש(161-168), מ(97-104), ה(33-40)
    """
    if not is_valid_hebrew_text(name):
        raise HTTPException(
            status_code=422,
            detail="שם לא תקין - יש להזין רק אותיות עבריות"
        )
    
    try:
        # Import the main engine
        from app.services.memorial_verse_engine import MemorialVerseEngine
        
        # Create engine instance
        engine = MemorialVerseEngine(db)
        
        # Generate complete memorial verses
        result = await engine.get_verse_summary_for_name(name)
        
        logger.info(f"Generated memorial verses for '{name}': {result['total_verses']} total verses")
        
        return {
            "success": True,
            "hebrew_name": result["hebrew_name"],
            "summary": {
                "total_verses": result["total_verses"],
                "name_verses_count": result["name_verses_count"], 
                "neshama_verses_count": result["neshama_verses_count"],
                "name_letters": result["name_letters"],
                "unique_letters": result["unique_letters"]
            },
            "sections": result["sections"],
            "engine": "MemorialVerseEngine",
            "description": f"פסוקים מלאים לזיכרון '{name}' מתהילים קיט"
        }
        
    except ValueError as e:
        logger.error(f"Invalid input for memorial verses: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating memorial verses for '{name}': {e}")
        raise HTTPException(status_code=500, detail="שגיאה ביצירת פסוקי זיכרון")


@router.get("/stats")
async def get_hebrew_stats(db: AsyncSession = Depends(get_database)):
    """
    Get Hebrew content statistics.
    
    Returns statistics about Hebrew letters usage, popular verses,
    and overall Hebrew content metrics.
    """
    try:
        # Get total counts
        letters_count_result = await db.execute(select(func.count(Psalm119Letter.id)))
        total_letters = letters_count_result.scalar()
        
        verses_count_result = await db.execute(select(func.count(Psalm119Verse.id)))
        total_verses = verses_count_result.scalar()
        
        memorials_count_result = await db.execute(
            select(func.count(Memorial.id)).where(Memorial.is_public == True)
        )
        public_memorials = memorials_count_result.scalar()
        
        # Get most used letters
        popular_letters_query = (
            select(Psalm119Letter)
            .order_by(Psalm119Letter.usage_count.desc())
            .limit(5)
        )
        popular_letters_result = await db.execute(popular_letters_query)
        popular_letters = popular_letters_result.scalars().all()
        
        # Get most used verses
        popular_verses_query = (
            select(Psalm119Verse, Psalm119Letter)
            .join(Psalm119Letter, Psalm119Verse.letter_id == Psalm119Letter.id)
            .order_by(Psalm119Verse.usage_count.desc())
            .limit(5)
        )
        popular_verses_result = await db.execute(popular_verses_query)
        popular_verse_pairs = popular_verses_result.all()
        
        return {
            "total_letters": total_letters,
            "total_verses": total_verses,
            "public_memorials": public_memorials,
            "popular_letters": [
                {
                    "hebrew_letter": letter.hebrew_letter,
                    "hebrew_name": letter.hebrew_name,
                    "usage_count": letter.usage_count
                }
                for letter in popular_letters
            ],
            "popular_verses": [
                {
                    "verse_number": verse.verse_number,
                    "hebrew_text": verse.hebrew_text[:50] + "..." if len(verse.hebrew_text) > 50 else verse.hebrew_text,
                    "letter": letter.hebrew_letter,
                    "usage_count": verse.usage_count
                }
                for verse, letter in popular_verse_pairs
            ],
            "system_info": {
                "supports_rtl": True,
                "hebrew_fonts_loaded": True,
                "psalm_119_complete": total_verses == 176,
                "alphabet_complete": total_letters == 22
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting Hebrew stats: {e}")
        raise HTTPException(status_code=500, detail="שגיאה בטעינת סטטיסטיקות עבריות")