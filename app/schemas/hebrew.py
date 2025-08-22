"""
Pydantic schemas for Hebrew-specific API endpoints.
Handles Hebrew names, Psalm 119 verses, and RTL functionality.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator


class HebrewLetterInfo(BaseModel):
    """Basic Hebrew letter information."""
    hebrew_letter: str = Field(..., description="Hebrew letter character")
    hebrew_name: str = Field(..., description="Hebrew letter name in Hebrew")
    english_name: str = Field(..., description="Hebrew letter name in English")
    position: int = Field(..., ge=1, le=22, description="Position in alphabet (1-22)")
    numeric_value: int = Field(..., description="Gematria numeric value")
    

class VerseInfo(BaseModel):
    """Psalm 119 verse information."""
    id: int = Field(..., description="Verse database ID")
    verse_number: int = Field(..., ge=1, le=176, description="Verse number in Psalm 119")
    verse_in_section: int = Field(..., ge=1, le=8, description="Position within letter section")
    hebrew_text: str = Field(..., description="Hebrew text with vowels (nikud)")
    english_text: str = Field(..., description="English translation")
    transliteration: Optional[str] = Field(None, description="Hebrew transliteration")
    verse_reference: str = Field(..., description="Hebrew verse reference")
    usage_count: int = Field(default=0, description="Times used in memorials")


class HebrewLetterResponse(BaseModel):
    """Complete Hebrew letter response with optional verses."""
    id: int = Field(..., description="Letter database ID")
    hebrew_letter: str = Field(..., description="Hebrew letter character")
    hebrew_name: str = Field(..., description="Hebrew letter name in Hebrew") 
    english_name: str = Field(..., description="Hebrew letter name in English")
    transliteration: str = Field(..., description="Transliteration")
    numeric_value: int = Field(..., description="Gematria numeric value")
    position: int = Field(..., ge=1, le=22, description="Position in alphabet")
    usage_count: int = Field(default=0, description="Usage statistics")
    verses: List[Dict[str, Any]] = Field(default_factory=list, description="Sample verses")


class AlphabetResponse(BaseModel):
    """Complete Hebrew alphabet response."""
    letters: List[HebrewLetterResponse] = Field(..., description="All Hebrew letters")
    total_letters: int = Field(..., description="Total number of letters")
    description: str = Field(..., description="Description in Hebrew")


class HebrewNameAnalysisResponse(BaseModel):
    """Analysis of a Hebrew name."""
    name: str = Field(..., description="Original Hebrew name")
    letters: List[Dict[str, Any]] = Field(..., description="Letters in the name")
    total_letters: int = Field(..., description="Total letters in name")
    unique_letters: int = Field(..., description="Unique letters count")
    total_gematria_value: int = Field(..., description="Sum of all letter values")
    available_verses: int = Field(..., description="Total available verses")
    analysis_notes: str = Field(..., description="Analysis summary in Hebrew")


class VerseWithLetter(BaseModel):
    """Verse with its associated Hebrew letter."""
    id: int = Field(..., description="Verse database ID")
    verse_number: int = Field(..., ge=1, le=176, description="Verse number")
    verse_in_section: int = Field(..., ge=1, le=8, description="Position in section")
    hebrew_text: str = Field(..., description="Hebrew text with vowels")
    english_text: str = Field(..., description="English translation")
    transliteration: str = Field(..., description="Hebrew transliteration")
    verse_reference: str = Field(..., description="Hebrew verse reference")
    verse_reference_english: str = Field(..., description="English verse reference")
    letter: Dict[str, Any] = Field(..., description="Associated Hebrew letter info")
    themes: Optional[str] = Field(None, description="Verse themes")
    keywords: Optional[str] = Field(None, description="Search keywords")
    is_neshama_verse: bool = Field(default=False, description="Is this a soul verse")


class NameVersesResponse(BaseModel):
    """Response with verses selected for a Hebrew name."""
    name: str = Field(..., description="Hebrew name")
    verses: List[VerseWithLetter] = Field(..., description="Selected verses")
    name_analysis: Dict[str, Any] = Field(..., description="Name analysis")
    selection_method: str = Field(..., description="Verse selection method used")
    verses_per_letter: int = Field(..., description="Verses selected per letter")
    includes_neshama: bool = Field(..., description="Includes נשמה verses")
    total_verses: int = Field(..., description="Total verses returned")
    name_verses_count: int = Field(..., description="Name-based verses count")
    neshama_verses_count: int = Field(..., description="נשמה verses count")


class VerseSelectionRequest(BaseModel):
    """Request for selecting specific verses."""
    hebrew_name: str = Field(..., description="Hebrew name")
    verses_per_letter: int = Field(1, ge=1, le=8, description="Verses per letter")
    include_neshama: bool = Field(True, description="Include נשמה verses")
    selection_method: str = Field("balanced", description="Selection method")
    custom_letters: Optional[List[str]] = Field(None, description="Custom letter selection")
    
    @validator('hebrew_name')
    def validate_hebrew_name(cls, v):
        """Validate that name contains Hebrew characters."""
        import re
        hebrew_regex = re.compile(r'^[\u0590-\u05FF\s]*$')
        if not v or not v.strip():
            raise ValueError('השם העברי לא יכול להיות רק')
        if not hebrew_regex.match(v.strip()):
            raise ValueError('יש להזין רק אותיות עבריות')
        return v.strip()
    
    @validator('selection_method')
    def validate_selection_method(cls, v):
        """Validate selection method."""
        allowed_methods = ['balanced', 'sequential', 'random', 'custom']
        if v not in allowed_methods:
            raise ValueError(f'שיטת בחירה חייבת להיות אחת מ: {", ".join(allowed_methods)}')
        return v


class HebrewSearchRequest(BaseModel):
    """Hebrew content search request."""
    query: str = Field(..., description="Search query")
    search_type: str = Field("all", description="Search type")
    limit: int = Field(20, ge=1, le=100, description="Results limit")
    include_transliteration: bool = Field(True, description="Include transliterations")
    
    @validator('query')
    def validate_query(cls, v):
        """Validate search query."""
        if not v or not v.strip():
            raise ValueError('יש להזין שאילתת חיפוש')
        return v.strip()
    
    @validator('search_type') 
    def validate_search_type(cls, v):
        """Validate search type."""
        allowed_types = ['all', 'memorials', 'verses', 'letters']
        if v not in allowed_types:
            raise ValueError(f'סוג חיפוש חייב להיות אחד מ: {", ".join(allowed_types)}')
        return v


class MemorialSearchResult(BaseModel):
    """Memorial search result."""
    id: str = Field(..., description="Memorial ID")
    deceased_name_hebrew: str = Field(..., description="Hebrew name")
    deceased_name_english: Optional[str] = Field(None, description="English name")
    death_date_hebrew: Optional[str] = Field(None, description="Hebrew death date")
    death_date_gregorian: Optional[str] = Field(None, description="Gregorian death date")
    biography_excerpt: Optional[str] = Field(None, description="Biography excerpt")
    public_url: Optional[str] = Field(None, description="Public URL")
    page_views: int = Field(default=0, description="Page views count")


class VerseSearchResult(BaseModel):
    """Verse search result."""
    id: int = Field(..., description="Verse ID")
    verse_number: int = Field(..., description="Verse number")
    verse_in_section: int = Field(..., description="Position in section") 
    hebrew_text: str = Field(..., description="Hebrew text")
    english_text: str = Field(..., description="English text")
    transliteration: Optional[str] = Field(None, description="Transliteration")
    verse_reference: str = Field(..., description="Verse reference")
    letter: Dict[str, Any] = Field(..., description="Associated letter")
    themes: Optional[str] = Field(None, description="Themes")
    keywords: Optional[str] = Field(None, description="Keywords")
    usage_count: int = Field(default=0, description="Usage count")


class LetterSearchResult(BaseModel):
    """Hebrew letter search result."""
    id: int = Field(..., description="Letter ID")
    hebrew_letter: str = Field(..., description="Hebrew letter")
    hebrew_name: str = Field(..., description="Hebrew name")
    english_name: str = Field(..., description="English name")
    transliteration: str = Field(..., description="Transliteration")
    numeric_value: int = Field(..., description="Numeric value")
    position: int = Field(..., description="Alphabet position")
    usage_count: int = Field(default=0, description="Usage count")
    verse_count: int = Field(default=8, description="Number of verses")


class HebrewSearchResponse(BaseModel):
    """Hebrew search response."""
    query: str = Field(..., description="Original search query")
    search_type: str = Field(..., description="Search type used")
    results: Dict[str, List[Any]] = Field(..., description="Search results by type")
    total_results: int = Field(..., description="Total results count")
    has_results: bool = Field(..., description="Whether results were found")
    search_suggestions: List[str] = Field(default_factory=list, description="Search suggestions")


class HebrewValidationResponse(BaseModel):
    """Hebrew text validation response."""
    text: str = Field(..., description="Original text")
    is_valid: bool = Field(..., description="Is valid Hebrew")
    extracted_letters: List[str] = Field(..., description="Extracted Hebrew letters")
    normalized_letters: List[str] = Field(..., description="Normalized letters (sofit->regular)")
    letter_count: int = Field(..., description="Number of letters")
    unique_letters: List[str] = Field(..., description="Unique letters")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")


class GematriaCalculation(BaseModel):
    """Gematria calculation result."""
    text: str = Field(..., description="Original Hebrew text")
    letters: List[Dict[str, Any]] = Field(..., description="Letters with values")
    total_value: int = Field(..., description="Total gematria value")
    calculation_method: str = Field(default="standard", description="Calculation method")
    breakdown: Dict[str, int] = Field(..., description="Value breakdown by letter")


class HebrewStatistics(BaseModel):
    """Hebrew content statistics."""
    total_letters: int = Field(..., description="Total Hebrew letters")
    total_verses: int = Field(..., description="Total verses")
    public_memorials: int = Field(..., description="Public memorials count")
    popular_letters: List[Dict[str, Any]] = Field(..., description="Most used letters")
    popular_verses: List[Dict[str, Any]] = Field(..., description="Most used verses")
    system_info: Dict[str, Any] = Field(..., description="System information")


class YahrzeitCalculation(BaseModel):
    """Yahrzeit calculation for Hebrew dates."""
    death_date_hebrew: str = Field(..., description="Hebrew death date")
    death_date_gregorian: Optional[str] = Field(None, description="Gregorian death date")
    yahrzeit_date_hebrew: str = Field(..., description="Hebrew yahrzeit date")
    next_yahrzeit_gregorian: str = Field(..., description="Next Gregorian yahrzeit")
    years_since_death: Optional[int] = Field(None, description="Years since death")
    calculation_notes: str = Field(..., description="Calculation notes in Hebrew")


class PsalmVerseAnalysis(BaseModel):
    """Analysis of Psalm 119 verse."""
    verse_id: int = Field(..., description="Verse ID")
    verse_number: int = Field(..., description="Verse number")
    hebrew_text: str = Field(..., description="Hebrew text")
    word_analysis: List[Dict[str, Any]] = Field(..., description="Hebrew word analysis")
    themes: List[str] = Field(..., description="Verse themes")
    literary_devices: List[str] = Field(..., description="Literary devices used")
    spiritual_significance: str = Field(..., description="Spiritual significance")
    connection_to_letter: Dict[str, Any] = Field(..., description="Connection to Hebrew letter")


class HebrewMemorialSuggestions(BaseModel):
    """Suggestions for Hebrew memorial content."""
    name: str = Field(..., description="Hebrew name")
    suggested_verses: List[VerseWithLetter] = Field(..., description="Suggested verses")
    alternative_verses: List[VerseWithLetter] = Field(..., description="Alternative verses")
    name_meaning: Optional[str] = Field(None, description="Name meaning if available")
    cultural_context: Optional[str] = Field(None, description="Cultural context")
    memorial_suggestions: List[str] = Field(..., description="Memorial content suggestions")


# Error models for Hebrew-specific errors
class HebrewValidationError(BaseModel):
    """Hebrew validation error details."""
    field: str = Field(..., description="Field with error")
    value: str = Field(..., description="Invalid value")
    error_type: str = Field(..., description="Type of error")
    message_hebrew: str = Field(..., description="Error message in Hebrew")
    message_english: str = Field(..., description="Error message in English")
    suggestions: List[str] = Field(default_factory=list, description="Correction suggestions")


class HebrewAPIError(BaseModel):
    """Hebrew API error response."""
    error: str = Field(..., description="Error code")
    message_hebrew: str = Field(..., description="Error message in Hebrew")
    message_english: str = Field(..., description="Error message in English")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")