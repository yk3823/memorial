"""
Enhanced Psalm 119 models for Memorial Website.
Stores the 22 Hebrew letters and 176 verses of Psalm 119 with proper RTL support.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import String, Text, Integer, ForeignKey, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from .base import BaseModel


class Psalm119Letter(BaseModel):
    """
    Hebrew letter model for Psalm 119 sections.
    
    Psalm 119 is organized into 22 sections, one for each Hebrew letter.
    Each letter section contains 8 verses.
    """
    
    __tablename__ = "psalm_119_letters"
    
    # Use integer ID for ordering (1-22)
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=False,
        comment="Hebrew letter position (1-22)"
    )
    
    # Hebrew letter character
    hebrew_letter: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        unique=True,
        index=True,
        comment="Hebrew letter character (א, ב, ג, etc.)"
    )
    
    # Hebrew letter name in Hebrew
    hebrew_name: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Hebrew letter name in Hebrew (אלף, בית, גימל, etc.)"
    )
    
    # Hebrew letter name in English
    english_name: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Hebrew letter name in English (Aleph, Bet, Gimel, etc.)"
    )
    
    # Hebrew letter name transliteration
    transliteration: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Hebrew letter name transliteration"
    )
    
    # Numeric value of Hebrew letter (Gematria)
    numeric_value: Mapped[int] = mapped_column(
        nullable=False,
        comment="Numeric value of Hebrew letter in Gematria"
    )
    
    # Position in Hebrew alphabet (1-22)
    position: Mapped[int] = mapped_column(
        nullable=False,
        unique=True,
        index=True,
        comment="Position in Hebrew alphabet (1-22)"
    )
    
    # Usage statistics
    usage_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="Number of times verses from this letter have been used"
    )
    
    # Relationships
    verses: Mapped[List["Psalm119Verse"]] = relationship(
        "Psalm119Verse",
        back_populates="letter",
        lazy="select",
        order_by="Psalm119Verse.verse_in_section"
    )
    
    # Database constraints
    __table_args__ = (
        CheckConstraint(
            "position >= 1 AND position <= 22",
            name="ck_psalm_letter_position_range"
        ),
        CheckConstraint(
            "numeric_value > 0",
            name="ck_psalm_letter_numeric_value_positive"
        ),
        CheckConstraint(
            "usage_count >= 0",
            name="ck_psalm_letter_usage_count_non_negative"
        ),
        Index("ix_psalm_letter_hebrew", "hebrew_letter"),
        Index("ix_psalm_letter_position", "position", unique=True),
        Index("ix_psalm_letter_usage", "usage_count"),
    )
    
    # Methods
    def increment_usage(self) -> None:
        """Increment usage count when verses from this letter are used."""
        self.usage_count += 1
    
    def decrement_usage(self) -> None:
        """Decrement usage count when verse usage is removed."""
        if self.usage_count > 0:
            self.usage_count -= 1
    
    def get_verses(self, limit: Optional[int] = None) -> List["Psalm119Verse"]:
        """
        Get verses for this Hebrew letter.
        
        Args:
            limit: Maximum number of verses to return
            
        Returns:
            List of verses ordered by verse_in_section
        """
        verses = sorted(self.verses, key=lambda v: v.verse_in_section)
        return verses[:limit] if limit else verses
    
    def get_random_verse(self) -> Optional["Psalm119Verse"]:
        """
        Get a random verse from this letter section.
        
        Returns:
            Random verse or None if no verses
        """
        import random
        if self.verses:
            return random.choice(self.verses)
        return None
    
    @hybrid_property
    def display_name(self) -> str:
        """Get display name combining Hebrew and English."""
        return f"{self.hebrew_letter} ({self.english_name})"
    
    @hybrid_property
    def full_hebrew_name(self) -> str:
        """Get full Hebrew name with letter."""
        return f"{self.hebrew_letter} - {self.hebrew_name}"
    
    @hybrid_property
    def is_popular(self) -> bool:
        """Check if this letter is frequently used."""
        return self.usage_count >= 5
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<Psalm119Letter(id={self.id}, letter={self.hebrew_letter}, name={self.english_name})>"
    
    def to_dict(self, include_verses: bool = False, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Args:
            include_verses: Whether to include verse data
            exclude: Fields to exclude
            
        Returns:
            Dictionary representation
        """
        # Don't exclude created_at/updated_at for these models
        data = super().to_dict(exclude=exclude)
        
        # Add computed fields
        data['display_name'] = self.display_name
        data['full_hebrew_name'] = self.full_hebrew_name
        data['is_popular'] = self.is_popular
        data['verse_count'] = len(self.verses)
        
        if include_verses:
            data['verses'] = [verse.to_dict() for verse in self.get_verses()]
        
        return data
    
    @staticmethod
    def get_letter_by_hebrew_char(hebrew_char: str) -> Optional["Psalm119Letter"]:
        """
        Get letter by Hebrew character.
        
        Args:
            hebrew_char: Hebrew character to find
            
        Returns:
            Psalm119Letter or None if not found
        """
        from sqlalchemy import select
        from app.core.database import _session_factory
        
        # This would need proper session management in production
        # For now, return None - this should be implemented in service layer
        return None


class Psalm119Verse(BaseModel):
    """
    Enhanced Psalm 119 verse model with RTL support and Hebrew letter relationship.
    
    Each verse belongs to one of the 22 Hebrew letter sections.
    Optimized for Hebrew-first, RTL memorial websites.
    """
    
    __tablename__ = "psalm_119_verses"
    
    # Use integer ID for verse numbering (1-176)
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=False,
        comment="Absolute verse number (1-176)"
    )
    
    # Relationship to Hebrew letter
    letter_id: Mapped[int] = mapped_column(
        ForeignKey("psalm_119_letters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Hebrew letter section ID"
    )
    
    # Position within the Hebrew letter section (1-8)
    verse_in_section: Mapped[int] = mapped_column(
        nullable=False,
        comment="Position within the 8-verse Hebrew letter section (1-8)"
    )
    
    # Verse number within Psalm 119 (same as id, for clarity)
    verse_number: Mapped[int] = mapped_column(
        nullable=False,
        unique=True,
        index=True,
        comment="Verse number within Psalm 119 (1-176)"
    )
    
    # Hebrew text with vowels (nikud) - PRIMARY
    hebrew_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Primary Hebrew text with vowels (nikud) for RTL display"
    )
    
    # Hebrew text without vowels for search
    hebrew_text_no_vowels: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Hebrew text without vowels for search optimization"
    )
    
    # English translation
    english_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="English translation of the verse"
    )
    
    # Hebrew transliteration
    transliteration: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Hebrew text transliterated to Latin characters"
    )
    
    # Additional metadata
    themes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Comma-separated Hebrew/English themes for this verse"
    )
    
    keywords: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Comma-separated Hebrew/English keywords for searching"
    )
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="Number of times this verse has been associated with memorials"
    )
    
    # Verse quality metrics
    word_count_hebrew: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="Number of Hebrew words in this verse"
    )
    
    word_count_english: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="Number of English words in this verse"
    )
    
    # Relationships
    letter: Mapped["Psalm119Letter"] = relationship(
        "Psalm119Letter",
        back_populates="verses",
        lazy="select"
    )
    
    # memorials: Mapped[List["Memorial"]] = relationship(
    #     "Memorial",
    #     secondary="memorial_psalm_verses",
    #     back_populates="psalm_verses",
    #     lazy="select"
    # )
    
    # Database constraints and indexes
    __table_args__ = (
        # Ensure verse numbers are valid
        CheckConstraint(
            "verse_number >= 1 AND verse_number <= 176",
            name="ck_psalm_verse_number_range"
        ),
        CheckConstraint(
            "verse_in_section >= 1 AND verse_in_section <= 8",
            name="ck_psalm_verse_in_section_range"
        ),
        CheckConstraint(
            "usage_count >= 0",
            name="ck_psalm_verse_usage_count_non_negative"
        ),
        CheckConstraint(
            "word_count_hebrew >= 0 AND word_count_english >= 0",
            name="ck_psalm_verse_word_counts_non_negative"
        ),
        
        # Unique constraint for letter + verse in section
        UniqueConstraint(
            "letter_id", "verse_in_section",
            name="uq_psalm_verse_letter_position"
        ),
        
        # Performance indexes optimized for Hebrew searches
        Index("ix_psalm_verse_letter_section", "letter_id", "verse_in_section"),
        Index("ix_psalm_verse_number", "verse_number", unique=True),
        Index("ix_psalm_verse_usage", "usage_count"),
        Index("ix_psalm_verse_word_counts", "word_count_hebrew", "word_count_english"),
        
        # Full text search indexes for Hebrew (RTL) support
        Index(
            "ix_psalm_hebrew_fulltext", 
            "hebrew_text", 
            postgresql_using="gin",
            postgresql_ops={"hebrew_text": "gin_trgm_ops"}
        ),
        Index(
            "ix_psalm_hebrew_no_vowels_fulltext", 
            "hebrew_text_no_vowels", 
            postgresql_using="gin",
            postgresql_ops={"hebrew_text_no_vowels": "gin_trgm_ops"}
        ),
        Index(
            "ix_psalm_english_fulltext", 
            "english_text", 
            postgresql_using="gin",
            postgresql_ops={"english_text": "gin_trgm_ops"}
        ),
        Index(
            "ix_psalm_themes_search", 
            "themes", 
            postgresql_using="gin",
            postgresql_ops={"themes": "gin_trgm_ops"}
        ),
        Index(
            "ix_psalm_keywords_search", 
            "keywords", 
            postgresql_using="gin",
            postgresql_ops={"keywords": "gin_trgm_ops"}
        ),
    )
    
    # Hebrew text processing methods
    def update_word_counts(self) -> None:
        """Update word counts for Hebrew and English text."""
        self.word_count_hebrew = len(self.hebrew_text.split()) if self.hebrew_text else 0
        self.word_count_english = len(self.english_text.split()) if self.english_text else 0
    
    def generate_no_vowels_text(self) -> None:
        """Generate Hebrew text without vowels for search optimization."""
        if not self.hebrew_text:
            return
        
        # Hebrew vowel characters (nikud) Unicode ranges
        vowel_chars = '\u05B0-\u05BC\u05C1-\u05C2\u05C4-\u05C5\u05C7'
        import re
        self.hebrew_text_no_vowels = re.sub(f'[{vowel_chars}]', '', self.hebrew_text)
    
    # Search methods optimized for Hebrew RTL
    def search_hebrew(self, query: str, include_no_vowels: bool = True) -> bool:
        """
        Search in Hebrew text with RTL support.
        
        Args:
            query: Hebrew text to search for
            include_no_vowels: Also search in text without vowels
            
        Returns:
            True if query found
        """
        query_lower = query.lower()
        
        # Search in main Hebrew text
        if query_lower in self.hebrew_text.lower():
            return True
        
        # Search in no-vowels text if available
        if include_no_vowels and self.hebrew_text_no_vowels:
            if query_lower in self.hebrew_text_no_vowels.lower():
                return True
        
        return False
    
    def search_all_languages(self, query: str) -> bool:
        """
        Search across all language fields.
        
        Args:
            query: Text to search for
            
        Returns:
            True if query found in any language
        """
        query_lower = query.lower()
        
        # Search Hebrew (primary)
        if self.search_hebrew(query):
            return True
        
        # Search English
        if query_lower in self.english_text.lower():
            return True
        
        # Search transliteration
        if query_lower in self.transliteration.lower():
            return True
        
        return False
    
    # Content management
    def add_theme(self, theme: str) -> None:
        """Add a theme to the verse."""
        if not self.themes:
            self.themes = theme
        else:
            themes_list = [t.strip() for t in self.themes.split(",")]
            if theme not in themes_list:
                themes_list.append(theme)
                self.themes = ", ".join(themes_list)
    
    def add_keyword(self, keyword: str) -> None:
        """Add a keyword to the verse."""
        if not self.keywords:
            self.keywords = keyword
        else:
            keywords_list = [k.strip() for k in self.keywords.split(",")]
            if keyword not in keywords_list:
                keywords_list.append(keyword)
                self.keywords = ", ".join(keywords_list)
    
    def get_themes_list(self) -> List[str]:
        """Get list of themes."""
        if not self.themes:
            return []
        return [t.strip() for t in self.themes.split(",")]
    
    def get_keywords_list(self) -> List[str]:
        """Get list of keywords."""
        if not self.keywords:
            return []
        return [k.strip() for k in self.keywords.split(",")]
    
    # Usage tracking
    def increment_usage(self) -> None:
        """Increment usage counter and letter usage."""
        self.usage_count += 1
        if self.letter:
            self.letter.increment_usage()
    
    def decrement_usage(self) -> None:
        """Decrement usage counter."""
        if self.usage_count > 0:
            self.usage_count -= 1
        if self.letter:
            self.letter.decrement_usage()
    
    # Display properties
    @hybrid_property
    def verse_reference(self) -> str:
        """Get verse reference."""
        return f"תהילים קיט:{self.verse_number}"
    
    @hybrid_property
    def verse_reference_english(self) -> str:
        """Get English verse reference."""
        return f"Psalm 119:{self.verse_number}"
    
    @hybrid_property
    def full_reference(self) -> str:
        """Get full reference with Hebrew letter."""
        if self.letter:
            return f"{self.verse_reference} ({self.letter.display_name})"
        return self.verse_reference
    
    @hybrid_property
    def section_info(self) -> str:
        """Get section information."""
        if self.letter:
            return f"{self.letter.hebrew_letter} - פסוק {self.verse_in_section}"
        return f"פסוק {self.verse_in_section}"
    
    @hybrid_property
    def is_popular(self) -> bool:
        """Check if this is a popular verse."""
        return self.usage_count >= 10
    
    @hybrid_property
    def hebrew_length_category(self) -> str:
        """Categorize verse by Hebrew text length."""
        if self.word_count_hebrew <= 5:
            return "קצר"  # Short
        elif self.word_count_hebrew <= 10:
            return "בינוני"  # Medium
        else:
            return "ארוך"  # Long
    
    def get_primary_text(self, language: str = "hebrew") -> str:
        """
        Get verse text in specified language.
        
        Args:
            language: Language preference (hebrew, english, transliteration)
            
        Returns:
            Verse text in requested language
        """
        if language == "hebrew":
            return self.hebrew_text
        elif language == "english":
            return self.english_text
        elif language == "transliteration":
            return self.transliteration
        else:
            return self.hebrew_text  # Default to Hebrew
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<Psalm119Verse(id={self.id}, verse={self.verse_number}, letter={self.letter.hebrew_letter if self.letter else 'N/A'})>"
    
    def to_dict(self, 
                include_letter: bool = True, 
                language_preference: str = "hebrew",
                exclude: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert to dictionary with Hebrew-first approach.
        
        Args:
            include_letter: Include letter information
            language_preference: Primary language for display
            exclude: Fields to exclude
            
        Returns:
            Dictionary representation optimized for RTL display
        """
        # Don't exclude created_at/updated_at for these models
        data = super().to_dict(exclude=exclude)
        
        # Add computed fields
        data['verse_reference'] = self.verse_reference
        data['verse_reference_english'] = self.verse_reference_english
        data['full_reference'] = self.full_reference
        data['section_info'] = self.section_info
        data['is_popular'] = self.is_popular
        data['hebrew_length_category'] = self.hebrew_length_category
        data['themes_list'] = self.get_themes_list()
        data['keywords_list'] = self.get_keywords_list()
        
        # Include letter information
        if include_letter and self.letter:
            data['letter'] = self.letter.to_dict(include_verses=False)
        
        # Set primary text based on language preference
        data['primary_text'] = self.get_primary_text(language_preference)
        
        return data