"""
Hebrew Name to Psalm Verse Service for Memorial Website.
Maps Hebrew names to corresponding Psalm 119 verses based on Hebrew letter positions.
"""

import logging
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class HebrewLetterMapping(Enum):
    """
    Hebrew letter to numeric position mapping for Psalm 119.
    Each Hebrew letter corresponds to a section in Psalm 119 (1-22).
    """
    ALEPH = (1, "א", "אלף")
    BET = (2, "ב", "בית")
    GIMEL = (3, "ג", "גימל")
    DALET = (4, "ד", "דלת")
    HE = (5, "ה", "הי")
    VAV = (6, "ו", "וו")
    ZAYIN = (7, "ז", "זין")
    HET = (8, "ח", "חית")
    TET = (9, "ט", "טית")
    YOD = (10, "י", "יוד")
    KAF = (11, "כ", "כף")
    LAMED = (12, "ל", "למד")
    MEM = (13, "מ", "מם")
    NUN = (14, "נ", "נון")
    SAMECH = (15, "ס", "סמך")
    AYIN = (16, "ע", "עין")
    PE = (17, "פ", "פי")
    TZADE = (18, "צ", "צדי")
    QOF = (19, "ק", "קוף")
    RESH = (20, "ר", "ריש")
    SHIN = (21, "ש", "שין")
    TAV = (22, "ת", "תו")

    def __init__(self, position: int, letter: str, name: str):
        self.position = position
        self.letter = letter
        self.name = name

    @classmethod
    def get_by_letter(cls, hebrew_letter: str) -> Optional["HebrewLetterMapping"]:
        """Get mapping by Hebrew letter character."""
        for mapping in cls:
            if mapping.letter == hebrew_letter:
                return mapping
        return None

    @classmethod
    def get_by_position(cls, position: int) -> Optional["HebrewLetterMapping"]:
        """Get mapping by position (1-22)."""
        for mapping in cls:
            if mapping.position == position:
                return mapping
        return None


@dataclass
class NameVerseMapping:
    """
    Represents the mapping between a Hebrew name and Psalm verses.
    
    Attributes:
        original_name: The original Hebrew name
        normalized_name: Normalized version (without vowels, etc.)
        letter_positions: List of Hebrew letter positions for each character
        verse_selections: Selected verses for memorial (including נשמה verses)
        total_verses: Total number of available verses for this name
        special_verses: Special verses added (like נשמה)
    """
    original_name: str
    normalized_name: str
    letter_positions: List[int]
    verse_selections: List[Dict[str, Any]]
    total_verses: int
    special_verses: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "original_name": self.original_name,
            "normalized_name": self.normalized_name,
            "letter_positions": self.letter_positions,
            "verse_selections": self.verse_selections,
            "total_verses": self.total_verses,
            "special_verses": self.special_verses,
            "summary": {
                "name_length": len(self.normalized_name),
                "unique_letters": len(set(self.letter_positions)),
                "total_selected_verses": len(self.verse_selections) + len(self.special_verses)
            }
        }


class HebrewNameService:
    """
    Service for mapping Hebrew names to Psalm 119 verses.
    
    This service provides the core algorithm for memorial verse selection:
    1. Maps each Hebrew letter in a name to its corresponding Psalm 119 section
    2. Selects verses from those sections
    3. Adds special נשמה (soul) verses for traditional Jewish memorial practice
    """
    
    def __init__(self):
        self.letter_mapping = {
            mapping.letter: mapping.position 
            for mapping in HebrewLetterMapping
        }
        
        # Hebrew letters that can appear at end of words (final forms)
        self.final_letters = {
            'ך': 'כ',  # Final Kaf -> Kaf
            'ם': 'מ',  # Final Mem -> Mem
            'ן': 'נ',  # Final Nun -> Nun
            'ף': 'פ',  # Final Pe -> Pe
            'ץ': 'צ',  # Final Tzade -> Tzade
        }
        
        # Special verse selections for נשמה (soul/memory)
        self.neshama_letters = ['נ', 'ש', 'מ', 'ה']  # Letters of נשמה
        
        # Hebrew vowel characters to remove during normalization
        self.hebrew_vowels = (
            '\u05B0\u05B1\u05B2\u05B3\u05B4\u05B5\u05B6\u05B7\u05B8\u05B9\u05BA\u05BB\u05BC'
            '\u05BD\u05BE\u05BF\u05C0\u05C1\u05C2\u05C3\u05C4\u05C5\u05C6\u05C7'
        )

    def normalize_hebrew_name(self, hebrew_name: str) -> str:
        """
        Normalize Hebrew name for processing.
        
        Args:
            hebrew_name: Raw Hebrew name input
            
        Returns:
            Normalized Hebrew name (no vowels, final letters converted)
        """
        if not hebrew_name:
            return ""
        
        # Remove vowels (nikud)
        normalized = "".join(char for char in hebrew_name if char not in self.hebrew_vowels)
        
        # Convert final letters to regular forms
        for final_letter, regular_letter in self.final_letters.items():
            normalized = normalized.replace(final_letter, regular_letter)
        
        # Remove non-Hebrew characters and whitespace
        hebrew_chars = ""
        for char in normalized:
            if '\u0590' <= char <= '\u05FF' and char not in [' ', '\t', '\n']:
                hebrew_chars += char
        
        return hebrew_chars

    def get_letter_positions(self, normalized_name: str) -> List[int]:
        """
        Get Hebrew letter positions for each character in the name.
        
        Args:
            normalized_name: Normalized Hebrew name
            
        Returns:
            List of positions (1-22) for each Hebrew letter
        """
        positions = []
        for char in normalized_name:
            if char in self.letter_mapping:
                positions.append(self.letter_mapping[char])
            else:
                logger.warning(f"Unknown Hebrew character in name: {char}")
        
        return positions

    def validate_hebrew_name(self, hebrew_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Hebrew name input.
        
        Args:
            hebrew_name: Hebrew name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not hebrew_name or not hebrew_name.strip():
            return False, "שם חייב להכיל אותיות עבריות"
        
        normalized = self.normalize_hebrew_name(hebrew_name)
        if not normalized:
            return False, "לא נמצאו אותיות עבריות תקינות בשם"
        
        if len(normalized) > 50:
            return False, "השם ארוך מדי (מקסימום 50 אותיות)"
        
        # Check for invalid characters
        invalid_chars = []
        for char in normalized:
            if char not in self.letter_mapping:
                invalid_chars.append(char)
        
        if invalid_chars:
            return False, f"אותיות לא תקינות בשם: {', '.join(invalid_chars)}"
        
        return True, None

    async def get_verses_for_name(
        self,
        hebrew_name: str,
        verses_per_letter: int = 1,
        include_neshama: bool = True,
        selection_method: str = "balanced"
    ) -> NameVerseMapping:
        """
        Get Psalm verses for a Hebrew name.
        
        Args:
            hebrew_name: Hebrew name
            verses_per_letter: Number of verses to select per letter
            include_neshama: Whether to include נשמה verses
            selection_method: Method for verse selection ('balanced', 'sequential', 'random')
            
        Returns:
            NameVerseMapping with selected verses
            
        Raises:
            ValueError: If name is invalid or verses cannot be retrieved
        """
        # Validate input
        is_valid, error_msg = self.validate_hebrew_name(hebrew_name)
        if not is_valid:
            raise ValueError(f"שם לא תקין: {error_msg}")
        
        # Normalize name
        normalized_name = self.normalize_hebrew_name(hebrew_name)
        letter_positions = self.get_letter_positions(normalized_name)
        
        if not letter_positions:
            raise ValueError("לא נמצאו אותיות עבריות תקינות בשם")
        
        # Get verses from database
        verse_selections = await self._select_verses_from_positions(
            letter_positions,
            verses_per_letter,
            selection_method
        )
        
        # Add נשמה verses if requested
        special_verses = []
        if include_neshama:
            special_verses = await self._get_neshama_verses()
        
        # Calculate totals
        total_verses = len(set(letter_positions)) * 8  # Each letter has 8 verses
        
        return NameVerseMapping(
            original_name=hebrew_name,
            normalized_name=normalized_name,
            letter_positions=letter_positions,
            verse_selections=verse_selections,
            total_verses=total_verses,
            special_verses=special_verses
        )

    async def _select_verses_from_positions(
        self,
        letter_positions: List[int],
        verses_per_letter: int,
        selection_method: str
    ) -> List[Dict[str, Any]]:
        """
        Select verses from Hebrew letter positions.
        
        Args:
            letter_positions: List of letter positions
            verses_per_letter: Number of verses per letter
            selection_method: Selection method
            
        Returns:
            List of selected verse data
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.core.database import get_db_session
        from app.models.psalm_119 import Psalm119Verse, Psalm119Letter
        
        selected_verses = []
        unique_positions = list(set(letter_positions))  # Remove duplicates
        
        async with get_db_session() as db:
            for position in unique_positions:
                # Get verses for this letter position
                query = (
                    select(Psalm119Verse)
                    .options(selectinload(Psalm119Verse.letter))
                    .join(Psalm119Letter)
                    .filter(Psalm119Letter.position == position)
                    .order_by(Psalm119Verse.verse_in_section)
                )
                
                result = await db.execute(query)
                verses = result.scalars().all()
                
                if not verses:
                    logger.warning(f"No verses found for letter position {position}")
                    continue
                
                # Select verses based on method
                if selection_method == "sequential":
                    selected = verses[:verses_per_letter]
                elif selection_method == "random":
                    import random
                    selected = random.sample(verses, min(verses_per_letter, len(verses)))
                else:  # balanced - prefer diverse verse positions
                    selected = self._balanced_selection(verses, verses_per_letter)
                
                # Convert to dict format
                for verse in selected:
                    verse_data = verse.to_dict(include_letter=True, language_preference="hebrew")
                    verse_data['selection_reason'] = f"נבחר עבור האות {verse.letter.hebrew_letter} בשם"
                    selected_verses.append(verse_data)
        
        return selected_verses

    def _balanced_selection(self, verses: List, count: int) -> List:
        """
        Select verses using balanced method (spread across the 8 verses).
        
        Args:
            verses: List of available verses
            count: Number of verses to select
            
        Returns:
            Selected verses
        """
        if count >= len(verses):
            return verses
        
        # Distribute selections across the 8-verse range
        step = len(verses) / count
        selected_indices = [int(i * step) for i in range(count)]
        
        return [verses[i] for i in selected_indices]

    async def _get_neshama_verses(self) -> List[Dict[str, Any]]:
        """
        Get special נשמה (soul) verses for memorial.
        
        Returns:
            List of נשמה verse data
        """
        from sqlalchemy import select, or_
        from sqlalchemy.orm import selectinload
        from app.core.database import get_db_session
        from app.models.psalm_119 import Psalm119Verse, Psalm119Letter
        
        neshama_verses = []
        
        async with get_db_session() as db:
            # Get verses for נ-ש-מ-ה letters
            neshama_positions = []
            for letter in self.neshama_letters:
                if letter in self.letter_mapping:
                    neshama_positions.append(self.letter_mapping[letter])
            
            if neshama_positions:
                query = (
                    select(Psalm119Verse)
                    .options(selectinload(Psalm119Verse.letter))
                    .join(Psalm119Letter)
                    .filter(Psalm119Letter.position.in_(neshama_positions))
                    .filter(Psalm119Verse.verse_in_section == 1)  # Take first verse from each letter
                )
                
                result = await db.execute(query)
                verses = result.scalars().all()
                
                for verse in verses:
                    verse_data = verse.to_dict(include_letter=True, language_preference="hebrew")
                    verse_data['selection_reason'] = f"נבחר עבור נשמה - אות {verse.letter.hebrew_letter}"
                    neshama_verses.append(verse_data)
        
        return neshama_verses

    async def get_popular_name_patterns(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get popular Hebrew name patterns and their verse statistics.
        
        Args:
            limit: Maximum number of patterns to return
            
        Returns:
            List of popular name patterns with statistics
        """
        # This would analyze actual usage patterns from the database
        # For now, return common Hebrew names as examples
        common_names = [
            "יוסף", "דוד", "משה", "אברהם", "יעקב", "יצחק", "שמואל", "בנימין",
            "אהרן", "שלמה", "נתן", "חיים", "אליעזר", "מרדכי", "יהושע", "גדעון",
            "שרה", "רבקה", "רחל", "לאה", "מרים", "אסתר", "רות", "חנה"
        ]
        
        patterns = []
        for name in common_names[:limit]:
            try:
                mapping = await self.get_verses_for_name(name, verses_per_letter=1)
                patterns.append({
                    "name": name,
                    "normalized": mapping.normalized_name,
                    "letter_count": len(mapping.normalized_name),
                    "unique_letters": len(set(mapping.letter_positions)),
                    "total_verses": mapping.total_verses,
                    "selected_verses": len(mapping.verse_selections),
                    "popularity_score": len(mapping.normalized_name) * len(set(mapping.letter_positions))
                })
            except Exception as e:
                logger.warning(f"Failed to process name {name}: {e}")
                continue
        
        # Sort by popularity score
        patterns.sort(key=lambda x: x["popularity_score"], reverse=True)
        
        return patterns

    def get_hebrew_alphabet_info(self) -> List[Dict[str, Any]]:
        """
        Get information about the Hebrew alphabet for UI display.
        
        Returns:
            List of Hebrew letter information
        """
        alphabet_info = []
        for mapping in HebrewLetterMapping:
            alphabet_info.append({
                "position": mapping.position,
                "letter": mapping.letter,
                "name": mapping.name,
                "english_name": mapping.name,  # Would need translation
                "psalm_section": f"{mapping.position * 8 - 7}-{mapping.position * 8}",
                "verses_range": f"פסוקים {mapping.position * 8 - 7}-{mapping.position * 8}"
            })
        
        return alphabet_info

    async def get_letter_usage_statistics(self) -> Dict[str, Any]:
        """
        Get usage statistics for Hebrew letters in memorials.
        
        Returns:
            Statistics about letter usage
        """
        from sqlalchemy import select, func
        from app.core.database import get_db_session
        from app.models.psalm_119 import Psalm119Letter, Psalm119Verse
        
        async with get_db_session() as db:
            # Get letter usage counts
            query = (
                select(
                    Psalm119Letter.hebrew_letter,
                    Psalm119Letter.hebrew_name,
                    Psalm119Letter.position,
                    Psalm119Letter.usage_count,
                    func.count(Psalm119Verse.id).label('verse_count')
                )
                .outerjoin(Psalm119Verse, Psalm119Letter.id == Psalm119Verse.letter_id)
                .group_by(
                    Psalm119Letter.id,
                    Psalm119Letter.hebrew_letter,
                    Psalm119Letter.hebrew_name,
                    Psalm119Letter.position,
                    Psalm119Letter.usage_count
                )
                .order_by(Psalm119Letter.position)
            )
            
            result = await db.execute(query)
            letter_stats = []
            
            for row in result:
                letter_stats.append({
                    "letter": row.hebrew_letter,
                    "name": row.hebrew_name,
                    "position": row.position,
                    "usage_count": row.usage_count,
                    "verse_count": row.verse_count,
                    "popularity_score": row.usage_count / max(1, row.verse_count)
                })
            
            # Calculate totals
            total_usage = sum(stat["usage_count"] for stat in letter_stats)
            total_verses = sum(stat["verse_count"] for stat in letter_stats)
            
            return {
                "letter_statistics": letter_stats,
                "summary": {
                    "total_usage": total_usage,
                    "total_verses": total_verses,
                    "most_popular_letter": max(letter_stats, key=lambda x: x["usage_count"], default={}),
                    "least_popular_letter": min(letter_stats, key=lambda x: x["usage_count"], default={}),
                    "average_usage_per_letter": total_usage / len(letter_stats) if letter_stats else 0
                }
            }


# Global service instance
_hebrew_name_service: Optional[HebrewNameService] = None


def get_hebrew_name_service() -> HebrewNameService:
    """
    Get Hebrew name service singleton.
    
    Returns:
        HebrewNameService instance
    """
    global _hebrew_name_service
    if _hebrew_name_service is None:
        _hebrew_name_service = HebrewNameService()
    return _hebrew_name_service


# Utility functions for common operations
async def get_verses_for_hebrew_name(
    hebrew_name: str,
    verses_per_letter: int = 1,
    include_neshama: bool = True
) -> Dict[str, Any]:
    """
    Quick utility to get verses for a Hebrew name.
    
    Args:
        hebrew_name: Hebrew name
        verses_per_letter: Number of verses per letter
        include_neshama: Include נשמה verses
        
    Returns:
        Verse mapping dictionary
    """
    service = get_hebrew_name_service()
    mapping = await service.get_verses_for_name(
        hebrew_name,
        verses_per_letter,
        include_neshama
    )
    return mapping.to_dict()


def validate_hebrew_name_input(hebrew_name: str) -> Tuple[bool, Optional[str]]:
    """
    Quick utility to validate Hebrew name.
    
    Args:
        hebrew_name: Hebrew name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    service = get_hebrew_name_service()
    return service.validate_hebrew_name(hebrew_name)