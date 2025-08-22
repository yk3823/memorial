"""
Hebrew Name to Psalm 119 Verse Selection Algorithm.

This service implements the core algorithm for selecting appropriate verses
from Psalm 119 based on Hebrew names, including the נשמה (soul) verses.
"""

import logging
import random
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

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

# Letters for נשמה (soul) verses
NESHAMA_LETTERS = ['נ', 'ש', 'מ', 'ה']

# Hebrew vowel characters (nikud) for text processing
HEBREW_VOWELS = '\u05B0-\u05BC\u05C1-\u05C2\u05C4-\u05C5\u05C7'


class SelectionMethod(Enum):
    """Verse selection methods."""
    SEQUENTIAL = "sequential"      # Select verses in order (1, 2, 3, ...)
    BALANCED = "balanced"         # Mix of first verse + random others
    RANDOM = "random"            # Pure random selection
    WEIGHTED = "weighted"        # Weighted by usage/popularity
    SPIRITUAL = "spiritual"      # Based on spiritual significance


class VerseQuality(Enum):
    """Verse quality/importance levels."""
    HIGH = "high"       # Key verses with strong spiritual meaning
    MEDIUM = "medium"   # Standard meaningful verses  
    LOW = "low"         # Less frequently used verses


@dataclass
class LetterAnalysis:
    """Analysis of a Hebrew letter in a name."""
    letter: str
    normalized_letter: str  # Sofit form normalized
    position_in_name: int
    frequency_in_name: int
    psalm_letter_info: Optional[Psalm119Letter] = None
    available_verses: List[Psalm119Verse] = None


@dataclass
class NameAnalysis:
    """Complete analysis of a Hebrew name."""
    original_name: str
    cleaned_name: str  # Name without vowels/punctuation
    letters: List[LetterAnalysis]
    unique_letters: List[str]
    total_gematria: int
    name_length: int
    complexity_score: float  # Based on letter variety and length


@dataclass
class VerseSelection:
    """A selected verse with metadata."""
    verse: Psalm119Verse
    letter: Psalm119Letter
    selection_reason: str
    quality_score: float
    is_neshama_verse: bool = False
    position_in_selection: int = 0


class HebrewNameToVerseSelector:
    """
    Core service for selecting Psalm 119 verses based on Hebrew names.
    
    This implements the main algorithm:
    1. Analyze Hebrew name to extract and normalize letters
    2. For each unique letter, find corresponding Psalm 119 section
    3. Select verses using specified method and criteria
    4. Add נשמה (soul) verses if requested
    5. Return verses with full Hebrew, transliteration, and analysis
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._letter_cache: Dict[str, Psalm119Letter] = {}
        self._verse_cache: Dict[int, List[Psalm119Verse]] = {}
    
    async def analyze_hebrew_name(self, name: str) -> NameAnalysis:
        """
        Analyze a Hebrew name to understand its structure and letters.
        
        Args:
            name: Hebrew name to analyze
            
        Returns:
            NameAnalysis with complete breakdown of the name
        """
        if not name or not name.strip():
            raise ValueError("Name cannot be empty")
        
        # Clean and normalize the name
        cleaned_name = self._clean_hebrew_text(name)
        letters = self._extract_hebrew_letters(cleaned_name)
        
        if not letters:
            raise ValueError("No Hebrew letters found in name")
        
        # Analyze each letter
        letter_analyses = []
        letter_frequencies = {}
        
        # Count letter frequencies
        for letter in letters:
            normalized = self._normalize_letter(letter)
            letter_frequencies[normalized] = letter_frequencies.get(normalized, 0) + 1
        
        # Create letter analysis
        position = 0
        for letter in letters:
            normalized = self._normalize_letter(letter)
            
            analysis = LetterAnalysis(
                letter=letter,
                normalized_letter=normalized,
                position_in_name=position,
                frequency_in_name=letter_frequencies[normalized]
            )
            
            # Get Psalm letter info
            psalm_letter = await self._get_letter_info(normalized)
            if psalm_letter:
                analysis.psalm_letter_info = psalm_letter
                analysis.available_verses = await self._get_verses_for_letter(psalm_letter.id)
            
            letter_analyses.append(analysis)
            position += 1
        
        # Calculate metrics
        unique_letters = list(dict.fromkeys([self._normalize_letter(l) for l in letters]))
        total_gematria = sum(
            analysis.psalm_letter_info.numeric_value 
            for analysis in letter_analyses 
            if analysis.psalm_letter_info
        )
        
        complexity_score = self._calculate_name_complexity(letter_analyses, unique_letters)
        
        return NameAnalysis(
            original_name=name,
            cleaned_name=cleaned_name,
            letters=letter_analyses,
            unique_letters=unique_letters,
            total_gematria=total_gematria,
            name_length=len(letters),
            complexity_score=complexity_score
        )
    
    async def select_verses_for_name(
        self,
        name: str,
        verses_per_letter: int = 1,
        selection_method: SelectionMethod = SelectionMethod.BALANCED,
        include_neshama: bool = True,
        quality_preference: VerseQuality = VerseQuality.MEDIUM
    ) -> Tuple[List[VerseSelection], NameAnalysis]:
        """
        Select Psalm 119 verses for a Hebrew name using specified criteria.
        
        Args:
            name: Hebrew name
            verses_per_letter: Number of verses to select per unique letter (1-8)
            selection_method: Method for selecting verses
            include_neshama: Whether to include נשמה verses
            quality_preference: Preferred quality level for verses
            
        Returns:
            Tuple of (selected verses, name analysis)
        """
        # First analyze the name
        name_analysis = await self.analyze_hebrew_name(name)
        
        # Select verses for each unique letter in the name
        selected_verses: List[VerseSelection] = []
        position = 0
        
        for unique_letter in name_analysis.unique_letters:
            # Find the letter analysis
            letter_analysis = next(
                (la for la in name_analysis.letters if la.normalized_letter == unique_letter),
                None
            )
            
            if not letter_analysis or not letter_analysis.psalm_letter_info:
                logger.warning(f"No Psalm letter found for '{unique_letter}'")
                continue
            
            # Select verses for this letter
            letter_verses = await self._select_verses_for_letter(
                letter_analysis,
                verses_per_letter,
                selection_method,
                quality_preference
            )
            
            # Add to selection with metadata
            for i, verse in enumerate(letter_verses):
                selection = VerseSelection(
                    verse=verse,
                    letter=letter_analysis.psalm_letter_info,
                    selection_reason=f"Letter '{unique_letter}' from name '{name}'",
                    quality_score=self._calculate_verse_quality_score(verse),
                    is_neshama_verse=False,
                    position_in_selection=position
                )
                selected_verses.append(selection)
                position += 1
        
        # Add נשמה (soul) verses if requested
        if include_neshama:
            neshama_verses = await self._select_neshama_verses(selection_method)
            selected_verses.extend(neshama_verses)
        
        logger.info(f"Selected {len(selected_verses)} verses for name '{name}'")
        return selected_verses, name_analysis
    
    async def _select_verses_for_letter(
        self,
        letter_analysis: LetterAnalysis,
        count: int,
        method: SelectionMethod,
        quality: VerseQuality
    ) -> List[Psalm119Verse]:
        """Select verses for a specific Hebrew letter."""
        if not letter_analysis.available_verses:
            return []
        
        verses = letter_analysis.available_verses
        
        if method == SelectionMethod.SEQUENTIAL:
            return verses[:count]
        
        elif method == SelectionMethod.RANDOM:
            return random.sample(verses, min(count, len(verses)))
        
        elif method == SelectionMethod.BALANCED:
            if count == 1:
                # Return first verse for balanced single selection
                return verses[:1]
            else:
                # Mix of first verse plus random others
                selected = [verses[0]]  # Always include first verse
                remaining = verses[1:]
                if remaining and count > 1:
                    additional = random.sample(remaining, min(count - 1, len(remaining)))
                    selected.extend(additional)
                return selected
        
        elif method == SelectionMethod.WEIGHTED:
            # Weight by inverse usage (prefer less used verses) and verse position
            weights = []
            for verse in verses:
                # Lower usage = higher weight, earlier position = higher weight
                usage_weight = 1.0 / max(verse.usage_count + 1, 1)
                position_weight = (9 - verse.verse_in_section) / 8.0  # 1.0 to 0.125
                total_weight = usage_weight * 0.7 + position_weight * 0.3
                weights.append(total_weight)
            
            selected_verses = []
            available_indices = list(range(len(verses)))
            
            for _ in range(min(count, len(verses))):
                # Weighted random selection
                total_weight = sum(weights[i] for i in available_indices)
                if total_weight == 0:
                    break
                
                rand_val = random.random() * total_weight
                cumsum = 0
                
                for i in available_indices:
                    cumsum += weights[i]
                    if rand_val <= cumsum:
                        selected_verses.append(verses[i])
                        available_indices.remove(i)
                        break
            
            return selected_verses
        
        elif method == SelectionMethod.SPIRITUAL:
            # Select based on spiritual significance (themes, word count, etc.)
            scored_verses = []
            for verse in verses:
                score = self._calculate_spiritual_significance_score(verse)
                scored_verses.append((verse, score))
            
            # Sort by spiritual score (descending) and take top verses
            scored_verses.sort(key=lambda x: x[1], reverse=True)
            return [verse for verse, _ in scored_verses[:count]]
        
        else:
            # Default to sequential
            return verses[:count]
    
    async def _select_neshama_verses(self, method: SelectionMethod) -> List[VerseSelection]:
        """Select נשמה (soul) verses from נ,ש,מ,ה letters."""
        neshama_selections = []
        position = 1000  # High position to put נשמה verses after name verses
        
        for neshama_letter in NESHAMA_LETTERS:
            letter_info = await self._get_letter_info(neshama_letter)
            if not letter_info:
                continue
            
            verses = await self._get_verses_for_letter(letter_info.id)
            if not verses:
                continue
            
            # Select one verse from each נשמה letter
            if method == SelectionMethod.RANDOM:
                verse = random.choice(verses)
            else:
                # Default to first verse for consistency
                verse = verses[0]
            
            selection = VerseSelection(
                verse=verse,
                letter=letter_info,
                selection_reason=f"נשמה verse from letter '{neshama_letter}'",
                quality_score=self._calculate_verse_quality_score(verse),
                is_neshama_verse=True,
                position_in_selection=position
            )
            
            neshama_selections.append(selection)
            position += 1
        
        return neshama_selections
    
    async def _get_letter_info(self, hebrew_letter: str) -> Optional[Psalm119Letter]:
        """Get Hebrew letter info with caching."""
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
    
    async def _get_verses_for_letter(self, letter_id: int) -> List[Psalm119Verse]:
        """Get all verses for a letter with caching."""
        if letter_id in self._verse_cache:
            return self._verse_cache[letter_id]
        
        query = (
            select(Psalm119Verse)
            .where(Psalm119Verse.letter_id == letter_id)
            .order_by(Psalm119Verse.verse_in_section)
        )
        result = await self.db.execute(query)
        verses = result.scalars().all()
        
        self._verse_cache[letter_id] = verses
        return verses
    
    def _clean_hebrew_text(self, text: str) -> str:
        """Clean Hebrew text by removing vowels and extra whitespace."""
        import re
        # Remove Hebrew vowel marks (nikud)
        text = re.sub(f'[{HEBREW_VOWELS}]', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text.strip()
    
    def _extract_hebrew_letters(self, text: str) -> List[str]:
        """Extract Hebrew letters from text."""
        import re
        hebrew_letters_regex = re.compile(r'[\u05D0-\u05EA]')
        return hebrew_letters_regex.findall(text)
    
    def _normalize_letter(self, letter: str) -> str:
        """Convert sofit (final) letters to regular forms."""
        return SOFIT_MAPPING.get(letter, letter)
    
    def _calculate_name_complexity(self, letters: List[LetterAnalysis], unique_letters: List[str]) -> float:
        """Calculate complexity score for a name (0.0 to 1.0)."""
        if not letters:
            return 0.0
        
        # Factors: length, unique letter ratio, gematria variance
        length_score = min(len(letters) / 10.0, 1.0)  # Normalize to 10 letters
        uniqueness_score = len(unique_letters) / len(letters)
        
        # Gematria variance (higher variance = more complex)
        gematria_values = [
            la.psalm_letter_info.numeric_value 
            for la in letters 
            if la.psalm_letter_info
        ]
        
        if gematria_values:
            mean_gematria = sum(gematria_values) / len(gematria_values)
            variance = sum((x - mean_gematria) ** 2 for x in gematria_values) / len(gematria_values)
            variance_score = min(variance / 10000.0, 1.0)  # Normalize variance
        else:
            variance_score = 0.0
        
        # Weighted combination
        complexity = (length_score * 0.4 + uniqueness_score * 0.4 + variance_score * 0.2)
        return min(complexity, 1.0)
    
    def _calculate_verse_quality_score(self, verse: Psalm119Verse) -> float:
        """Calculate quality score for a verse (0.0 to 1.0)."""
        # Factors: word count, themes, keywords, usage frequency
        word_count_score = min(verse.word_count_hebrew / 15.0, 1.0)  # Normalize to 15 words
        
        theme_score = 0.5
        if verse.themes:
            theme_count = len(verse.themes.split(','))
            theme_score = min(theme_count / 5.0, 1.0)  # Normalize to 5 themes
        
        keyword_score = 0.5
        if verse.keywords:
            keyword_count = len(verse.keywords.split(','))
            keyword_score = min(keyword_count / 5.0, 1.0)  # Normalize to 5 keywords
        
        # Lower usage can indicate higher quality/uniqueness
        usage_score = 1.0 - min(verse.usage_count / 100.0, 0.8)  # Cap at 0.2 minimum
        
        # Position in section (earlier verses often more significant)
        position_score = (9 - verse.verse_in_section) / 8.0
        
        # Weighted combination
        quality = (
            word_count_score * 0.2 +
            theme_score * 0.2 +
            keyword_score * 0.2 +
            usage_score * 0.2 +
            position_score * 0.2
        )
        
        return min(quality, 1.0)
    
    def _calculate_spiritual_significance_score(self, verse: Psalm119Verse) -> float:
        """Calculate spiritual significance score for verse selection."""
        score = 0.0
        
        # Check for spiritual keywords in Hebrew text
        spiritual_keywords = ['תורה', 'מצוה', 'נשמה', 'לב', 'אמת', 'צדק']
        for keyword in spiritual_keywords:
            if keyword in verse.hebrew_text:
                score += 0.1
        
        # Position bonus (first verses often more foundational)
        if verse.verse_in_section <= 2:
            score += 0.2
        
        # Word count bonus (substantive verses)
        if 8 <= verse.word_count_hebrew <= 12:
            score += 0.1
        
        # Theme bonus
        if verse.themes and any(theme in ['תורה', 'ברכה', 'אמת', 'צדק'] 
                               for theme in verse.themes.split(',')):
            score += 0.1
        
        return min(score, 1.0)