"""
Psalm Verse model for Memorial Website.
Stores the 176 verses of Psalm 119 in Hebrew, English, and transliteration.
"""

from typing import Optional, List

from sqlalchemy import String, Text, Index, CheckConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from .base import BaseModel


class PsalmVerse(BaseModel):
    """
    Psalm verse model for storing verses from Psalm 119.
    
    Psalm 119 is the longest chapter in the Bible with 176 verses,
    organized into 22 sections corresponding to Hebrew letters.
    Each memorial can be associated with specific verses.
    """
    
    __tablename__ = "psalm_verses"
    
    # Override the UUID primary key to use integer for verse numbering
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=False,
        comment="Verse number (1-176)"
    )
    
    # Hebrew letter section (Aleph, Bet, Gimel, etc.)
    hebrew_letter: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="Hebrew letter for this section (א, ב, ג, etc.)"
    )
    
    hebrew_letter_name: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Name of the Hebrew letter (Aleph, Bet, Gimel, etc.)"
    )
    
    # Position within the Hebrew letter section (1-8)
    verse_in_section: Mapped[int] = mapped_column(
        nullable=False,
        comment="Position within the 8-verse Hebrew letter section"
    )
    
    # Verse number within Psalm 119 (1-176)
    verse_number: Mapped[int] = mapped_column(
        nullable=False,
        unique=True,
        index=True,
        comment="Verse number within Psalm 119 (1-176)"
    )
    
    # Verse text in different languages
    verse_text_hebrew: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Verse text in Hebrew with vowels (נקודות)"
    )
    
    verse_text_hebrew_no_vowels: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Verse text in Hebrew without vowels"
    )
    
    verse_text_english: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Verse text in English translation"
    )
    
    verse_text_transliteration: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Hebrew text transliterated to English characters"
    )
    
    # Additional translations (optional)
    verse_text_spanish: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Verse text in Spanish translation"
    )
    
    verse_text_french: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Verse text in French translation"
    )
    
    verse_text_russian: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Verse text in Russian translation"
    )
    
    # Themes and keywords for verse categorization
    themes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Comma-separated themes/topics for this verse"
    )
    
    keywords: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Comma-separated keywords for searching"
    )
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="Number of times this verse has been associated with memorials"
    )
    
    # Relationships (many-to-many with memorials through association table)
    memorials: Mapped[List["Memorial"]] = relationship(
        "Memorial",
        secondary="memorial_psalm_verses",
        back_populates="psalm_verses",
        lazy="select"
    )
    
    # Database indexes for performance
    __table_args__ = (
        # Ensure verse numbers are valid (1-176)
        CheckConstraint(
            "verse_number >= 1 AND verse_number <= 176",
            name="ck_psalm_verse_number_range"
        ),
        
        # Ensure verse in section is valid (1-8)
        CheckConstraint(
            "verse_in_section >= 1 AND verse_in_section <= 8",
            name="ck_psalm_verse_in_section_range"
        ),
        
        # Ensure non-negative usage count
        CheckConstraint(
            "usage_count >= 0",
            name="ck_psalm_usage_count_non_negative"
        ),
        
        # Performance indexes
        Index("ix_psalm_hebrew_letter", "hebrew_letter", "verse_in_section"),
        Index("ix_psalm_verse_number", "verse_number", unique=True),
        Index("ix_psalm_letter_name", "hebrew_letter_name"),
        Index("ix_psalm_usage_count", "usage_count"),
        Index("ix_psalm_themes", "themes", postgresql_using="gin", postgresql_ops={"themes": "gin_trgm_ops"}),
        Index("ix_psalm_keywords", "keywords", postgresql_using="gin", postgresql_ops={"keywords": "gin_trgm_ops"}),
        
        # Full text search indexes
        Index("ix_psalm_hebrew_text_search", "verse_text_hebrew", postgresql_using="gin", postgresql_ops={"verse_text_hebrew": "gin_trgm_ops"}),
        Index("ix_psalm_english_text_search", "verse_text_english", postgresql_using="gin", postgresql_ops={"verse_text_english": "gin_trgm_ops"}),
    )
    
    # Text search and filtering methods
    def search_text(self, query: str, language: str = "english") -> bool:
        """
        Search for text within the verse.
        
        Args:
            query: Text to search for
            language: Language to search in (hebrew, english, transliteration)
            
        Returns:
            bool: True if query found in verse text
        """
        query_lower = query.lower()
        
        if language == "hebrew":
            return query_lower in self.verse_text_hebrew.lower()
        elif language == "english":
            return query_lower in self.verse_text_english.lower()
        elif language == "transliteration":
            return query_lower in self.verse_text_transliteration.lower()
        else:
            # Search all languages
            return (
                query_lower in self.verse_text_hebrew.lower() or
                query_lower in self.verse_text_english.lower() or
                query_lower in self.verse_text_transliteration.lower()
            )
    
    def has_theme(self, theme: str) -> bool:
        """
        Check if verse contains a specific theme.
        
        Args:
            theme: Theme to search for
            
        Returns:
            bool: True if theme found
        """
        if not self.themes:
            return False
        
        themes_list = [t.strip().lower() for t in self.themes.split(",")]
        return theme.lower() in themes_list
    
    def has_keyword(self, keyword: str) -> bool:
        """
        Check if verse contains a specific keyword.
        
        Args:
            keyword: Keyword to search for
            
        Returns:
            bool: True if keyword found
        """
        if not self.keywords:
            return False
        
        keywords_list = [k.strip().lower() for k in self.keywords.split(",")]
        return keyword.lower() in keywords_list
    
    # Content management
    def add_theme(self, theme: str) -> None:
        """
        Add a theme to the verse.
        
        Args:
            theme: Theme to add
        """
        if not self.themes:
            self.themes = theme
        else:
            themes_list = [t.strip() for t in self.themes.split(",")]
            if theme not in themes_list:
                themes_list.append(theme)
                self.themes = ", ".join(themes_list)
    
    def add_keyword(self, keyword: str) -> None:
        """
        Add a keyword to the verse.
        
        Args:
            keyword: Keyword to add
        """
        if not self.keywords:
            self.keywords = keyword
        else:
            keywords_list = [k.strip() for k in self.keywords.split(",")]
            if keyword not in keywords_list:
                keywords_list.append(keyword)
                self.keywords = ", ".join(keywords_list)
    
    def get_themes_list(self) -> List[str]:
        """
        Get list of themes for this verse.
        
        Returns:
            List of theme strings
        """
        if not self.themes:
            return []
        return [t.strip() for t in self.themes.split(",")]
    
    def get_keywords_list(self) -> List[str]:
        """
        Get list of keywords for this verse.
        
        Returns:
            List of keyword strings
        """
        if not self.keywords:
            return []
        return [k.strip() for k in self.keywords.split(",")]
    
    # Usage tracking
    def increment_usage(self) -> None:
        """Increment the usage counter when verse is associated with a memorial."""
        self.usage_count += 1
    
    def decrement_usage(self) -> None:
        """Decrement the usage counter when verse association is removed."""
        if self.usage_count > 0:
            self.usage_count -= 1
    
    # Display properties
    @hybrid_property
    def section_display(self) -> str:
        """Get display string for the Hebrew letter section."""
        return f"{self.hebrew_letter} ({self.hebrew_letter_name})"
    
    @hybrid_property
    def verse_reference(self) -> str:
        """Get verse reference (e.g., 'Psalm 119:1')."""
        return f"Psalm 119:{self.verse_number}"
    
    @hybrid_property
    def full_reference(self) -> str:
        """Get full reference with Hebrew letter."""
        return f"{self.verse_reference} ({self.section_display})"
    
    @hybrid_property
    def is_popular(self) -> bool:
        """Check if this is a popular verse (high usage)."""
        return self.usage_count >= 10
    
    @hybrid_property 
    def word_count_hebrew(self) -> int:
        """Count words in Hebrew text."""
        return len(self.verse_text_hebrew.split())
    
    @hybrid_property
    def word_count_english(self) -> int:
        """Count words in English text."""
        return len(self.verse_text_english.split())
    
    def get_verse_text(self, language: str = "english") -> str:
        """
        Get verse text in specified language.
        
        Args:
            language: Language code (hebrew, english, transliteration, etc.)
            
        Returns:
            str: Verse text in requested language
        """
        language = language.lower()
        
        if language == "hebrew":
            return self.verse_text_hebrew
        elif language == "english":
            return self.verse_text_english
        elif language == "transliteration":
            return self.verse_text_transliteration
        elif language == "spanish" and self.verse_text_spanish:
            return self.verse_text_spanish
        elif language == "french" and self.verse_text_french:
            return self.verse_text_french
        elif language == "russian" and self.verse_text_russian:
            return self.verse_text_russian
        else:
            return self.verse_text_english  # Default to English
    
    def __repr__(self) -> str:
        """String representation of psalm verse."""
        return f"<PsalmVerse(id={self.id}, verse={self.verse_number}, letter={self.hebrew_letter_name})>"
    
    def to_dict(self, include_all_languages: bool = False, exclude: Optional[List[str]] = None) -> dict:
        """
        Convert psalm verse to dictionary.
        
        Args:
            include_all_languages: Whether to include all language translations
            exclude: Fields to exclude
            
        Returns:
            dict: Psalm verse data dictionary
        """
        # Don't exclude created_at/updated_at for psalm verses since they use integer IDs
        data = super().to_dict(exclude=exclude)
        
        # Add computed fields
        data['section_display'] = self.section_display
        data['verse_reference'] = self.verse_reference
        data['full_reference'] = self.full_reference
        data['is_popular'] = self.is_popular
        data['word_count_hebrew'] = self.word_count_hebrew
        data['word_count_english'] = self.word_count_english
        data['themes_list'] = self.get_themes_list()
        data['keywords_list'] = self.get_keywords_list()
        
        # Optionally exclude less common language translations
        if not include_all_languages:
            optional_languages = [
                'verse_text_spanish',
                'verse_text_french', 
                'verse_text_russian'
            ]
            for lang in optional_languages:
                if lang in data and not data[lang]:
                    del data[lang]
        
        return data
    
    @staticmethod
    def get_hebrew_letters() -> List[tuple]:
        """
        Get list of Hebrew letters with their names.
        
        Returns:
            List of (letter, name) tuples
        """
        return [
            ("א", "Aleph"), ("ב", "Bet"), ("ג", "Gimel"), ("ד", "Dalet"),
            ("ה", "He"), ("ו", "Vav"), ("ז", "Zayin"), ("ח", "Het"),
            ("ט", "Tet"), ("י", "Yod"), ("כ", "Kaf"), ("ל", "Lamed"),
            ("מ", "Mem"), ("נ", "Nun"), ("ס", "Samech"), ("ע", "Ayin"),
            ("פ", "Pe"), ("צ", "Tzade"), ("ק", "Qof"), ("ר", "Resh"),
            ("ש", "Shin"), ("ת", "Tav")
        ]
    
    @staticmethod
    def get_supported_languages() -> List[str]:
        """Get list of supported languages for verse text."""
        return ["hebrew", "english", "transliteration", "spanish", "french", "russian"]
    
    @staticmethod
    def get_total_verses() -> int:
        """Get total number of verses in Psalm 119."""
        return 176
    
    @staticmethod
    def get_verses_per_section() -> int:
        """Get number of verses per Hebrew letter section."""
        return 8


# We need to import CheckConstraint
from sqlalchemy import CheckConstraint