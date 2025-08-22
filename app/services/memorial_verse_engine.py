"""
Memorial Verse Engine - Core functionality for Jewish Memorial Website

This is the MAIN ENGINE that provides verses for Hebrew names in the correct order:
1. For each letter in the name (יוסף): י → ו → ס → ף 
2. Show ALL 8 verses for each letter in Psalm 119 order
3. Then add all verses for נשמה letters (נ, ש, מ, ה) in order

Example for "יוסף":
- Letter י: Verses 73-80 (all 8 verses of Yod section)
- Letter ו: Verses 41-48 (all 8 verses of Vav section)  
- Letter ס: Verses 113-120 (all 8 verses of Samekh section)
- Letter ף/פ: Verses 129-136 (all 8 verses of Pe section)
- נשמה: נ (105-112), ש (161-168), מ (97-104), ה (33-40)
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.psalm_119 import Psalm119Letter, Psalm119Verse

logger = logging.getLogger(__name__)

# Hebrew letter mapping for final forms (sofit letters)
SOFIT_MAPPING = {
    'ץ': 'צ',  # Tzade sofit -> Tzade
    'ך': 'כ',  # Kaf sofit -> Kaf  
    'ן': 'נ',  # Nun sofit -> Nun
    'ם': 'מ',  # Mem sofit -> Mem
    'ף': 'פ'   # Pe sofit -> Pe
}

# Letters for נשמה (soul) verses - always in this order
NESHAMA_LETTERS = ['נ', 'ש', 'מ', 'ה']


@dataclass
class MemorialVerseSection:
    """A section of verses for a specific Hebrew letter."""
    letter: Psalm119Letter
    verses: List[Psalm119Verse]
    is_neshama: bool = False
    section_title: str = ""


@dataclass
class MemorialVerseResult:
    """Complete result for a Hebrew name with all verses."""
    hebrew_name: str
    name_letters: List[str]  # Original letters from the name
    unique_letters: List[str]  # Unique letters (no duplicates)
    name_sections: List[MemorialVerseSection]  # Verses for name letters
    neshama_sections: List[MemorialVerseSection]  # נשמה verses
    total_verses: int
    name_verses_count: int
    neshama_verses_count: int


class MemorialVerseEngine:
    """
    MAIN ENGINE for generating Hebrew memorial verses.
    
    This is the core engine that provides the exact functionality needed:
    - Takes a Hebrew name like "יוסף"
    - Returns ALL verses for each letter in Psalm 119 order
    - Adds נשמה verses at the end
    - Maintains proper Hebrew ordering and structure
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._letter_cache: Dict[str, Psalm119Letter] = {}
        self._verse_cache: Dict[int, List[Psalm119Verse]] = {}
    
    async def generate_memorial_verses(self, hebrew_name: str) -> MemorialVerseResult:
        """
        MAIN ENGINE FUNCTION - Generate complete memorial verses for a Hebrew name.
        
        Args:
            hebrew_name: Hebrew name like "יוסף", "מרים", etc.
            
        Returns:
            MemorialVerseResult with all verses in correct order
        """
        if not hebrew_name or not hebrew_name.strip():
            raise ValueError("Hebrew name cannot be empty")
        
        # Step 1: Extract and normalize Hebrew letters from the name
        name_letters = self._extract_hebrew_letters(hebrew_name.strip())
        if not name_letters:
            raise ValueError("No Hebrew letters found in name")
        
        # Step 2: Get unique letters while preserving order
        unique_letters = list(dict.fromkeys(name_letters))
        normalized_letters = [self._normalize_letter(letter) for letter in unique_letters]
        
        logger.info(f"Processing name '{hebrew_name}' with letters: {unique_letters}")
        
        # Step 3: Generate verse sections for each letter in the name
        name_sections = []
        name_verses_count = 0
        
        for i, letter in enumerate(unique_letters):
            normalized = normalized_letters[i]
            section = await self._get_verse_section_for_letter(
                letter, normalized, is_neshama=False
            )
            if section:
                name_sections.append(section)
                name_verses_count += len(section.verses)
        
        # Step 4: Generate נשמה (soul) verse sections
        neshama_sections = []
        neshama_verses_count = 0
        
        for neshama_letter in NESHAMA_LETTERS:
            section = await self._get_verse_section_for_letter(
                neshama_letter, neshama_letter, is_neshama=True
            )
            if section:
                neshama_sections.append(section)
                neshama_verses_count += len(section.verses)
        
        # Step 5: Create final result
        result = MemorialVerseResult(
            hebrew_name=hebrew_name,
            name_letters=name_letters,
            unique_letters=unique_letters,
            name_sections=name_sections,
            neshama_sections=neshama_sections,
            total_verses=name_verses_count + neshama_verses_count,
            name_verses_count=name_verses_count,
            neshama_verses_count=neshama_verses_count
        )
        
        logger.info(f"Generated {result.total_verses} verses for '{hebrew_name}': "
                   f"{result.name_verses_count} name verses + {result.neshama_verses_count} נשמה verses")
        
        return result
    
    async def _get_verse_section_for_letter(
        self, 
        original_letter: str, 
        normalized_letter: str, 
        is_neshama: bool = False
    ) -> Optional[MemorialVerseSection]:
        """
        Get ALL verses for a specific Hebrew letter in Psalm 119 order.
        
        Args:
            original_letter: The original letter from the name
            normalized_letter: The normalized letter (sofit converted)
            is_neshama: Whether this is a נשמה letter
            
        Returns:
            MemorialVerseSection with all 8 verses for this letter
        """
        # Get letter information from database
        letter_info = await self._get_letter_info(normalized_letter)
        if not letter_info:
            logger.warning(f"Letter '{normalized_letter}' not found in database")
            return None
        
        # Get ALL verses for this letter in Psalm 119 order
        verses = await self._get_all_verses_for_letter(letter_info.id)
        if not verses:
            logger.warning(f"No verses found for letter '{normalized_letter}'")
            return None
        
        # Create section title
        if is_neshama:
            section_title = f"פסוקי נשמה - אות {letter_info.hebrew_letter} ({letter_info.hebrew_name})"
        else:
            section_title = f"אות {letter_info.hebrew_letter} ({letter_info.hebrew_name}) מהשם"
        
        return MemorialVerseSection(
            letter=letter_info,
            verses=verses,
            is_neshama=is_neshama,
            section_title=section_title
        )
    
    async def _get_letter_info(self, hebrew_letter: str) -> Optional[Psalm119Letter]:
        """Get Hebrew letter information with caching."""
        if hebrew_letter in self._letter_cache:
            return self._letter_cache[hebrew_letter]
        
        query = select(Psalm119Letter).where(
            Psalm119Letter.hebrew_letter == hebrew_letter
        )
        result = await self.db.execute(query)
        letter = result.scalar_one_or_none()
        
        if letter:
            self._letter_cache[hebrew_letter] = letter
        
        return letter
    
    async def _get_all_verses_for_letter(self, letter_id: int) -> List[Psalm119Verse]:
        """Get ALL verses for a letter in Psalm 119 order (all 8 verses)."""
        if letter_id in self._verse_cache:
            return self._verse_cache[letter_id]
        
        # Get all 8 verses for this letter in correct order
        query = (
            select(Psalm119Verse)
            .where(Psalm119Verse.letter_id == letter_id)
            .order_by(Psalm119Verse.verse_in_section)  # 1, 2, 3, 4, 5, 6, 7, 8
        )
        result = await self.db.execute(query)
        verses = list(result.scalars().all())
        
        # Cache the result
        self._verse_cache[letter_id] = verses
        
        logger.debug(f"Retrieved {len(verses)} verses for letter_id {letter_id}")
        return verses
    
    def _extract_hebrew_letters(self, text: str) -> List[str]:
        """Extract Hebrew letters from text, preserving order."""
        import re
        hebrew_letters_regex = re.compile(r'[\u05D0-\u05EA]')
        return hebrew_letters_regex.findall(text)
    
    def _normalize_letter(self, letter: str) -> str:
        """Convert sofit (final) letters to regular forms."""
        return SOFIT_MAPPING.get(letter, letter)
    
    async def get_verse_summary_for_name(self, hebrew_name: str) -> Dict:
        """
        Get a summary of verses for a Hebrew name (for API responses).
        
        Returns:
            Dictionary with summary information
        """
        result = await self.generate_memorial_verses(hebrew_name)
        
        # Create summary response
        summary = {
            "hebrew_name": result.hebrew_name,
            "name_letters": result.name_letters,
            "unique_letters": result.unique_letters,
            "total_verses": result.total_verses,
            "name_verses_count": result.name_verses_count,
            "neshama_verses_count": result.neshama_verses_count,
            "sections": []
        }
        
        # Add name sections
        for section in result.name_sections:
            section_data = {
                "letter": {
                    "hebrew_letter": section.letter.hebrew_letter,
                    "hebrew_name": section.letter.hebrew_name,
                    "english_name": section.letter.english_name,
                    "position": section.letter.position,
                    "numeric_value": section.letter.numeric_value
                },
                "section_title": section.section_title,
                "is_neshama": section.is_neshama,
                "verse_count": len(section.verses),
                "verses": [
                    {
                        "id": verse.id,
                        "verse_number": verse.verse_number,
                        "verse_in_section": verse.verse_in_section,
                        "hebrew_text": verse.hebrew_text,
                        "english_text": verse.english_text,
                        "transliteration": verse.transliteration,
                        "verse_reference": f"תהילים קיט:{verse.verse_number}",
                        "verse_reference_english": f"Psalm 119:{verse.verse_number}"
                    }
                    for verse in section.verses
                ]
            }
            summary["sections"].append(section_data)
        
        # Add נשמה sections
        for section in result.neshama_sections:
            section_data = {
                "letter": {
                    "hebrew_letter": section.letter.hebrew_letter,
                    "hebrew_name": section.letter.hebrew_name,
                    "english_name": section.letter.english_name,
                    "position": section.letter.position,
                    "numeric_value": section.letter.numeric_value
                },
                "section_title": section.section_title,
                "is_neshama": section.is_neshama,
                "verse_count": len(section.verses),
                "verses": [
                    {
                        "id": verse.id,
                        "verse_number": verse.verse_number,
                        "verse_in_section": verse.verse_in_section,
                        "hebrew_text": verse.hebrew_text,
                        "english_text": verse.english_text,
                        "transliteration": verse.transliteration,
                        "verse_reference": f"תהילים קיט:{verse.verse_number}",
                        "verse_reference_english": f"Psalm 119:{verse.verse_number}"
                    }
                    for verse in section.verses
                ]
            }
            summary["sections"].append(section_data)
        
        return summary