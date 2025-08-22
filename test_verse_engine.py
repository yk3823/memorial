#!/usr/bin/env python3
"""
Test script to verify the MemorialVerseEngine returns ALL verses.
Run with: python test_verse_engine.py
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.services.memorial_verse_engine import MemorialVerseEngine


async def test_verse_engine():
    """Test the verse engine with a sample name."""
    async with AsyncSessionLocal() as db:
        engine = MemorialVerseEngine(db)
        
        # Test with the name "יוסף"
        test_name = "יוסף"
        print(f"\n=== Testing verse engine for name: {test_name} ===\n")
        
        result = await engine.generate_memorial_verses(test_name)
        
        print(f"Hebrew Name: {result.hebrew_name}")
        print(f"Name Letters: {result.name_letters}")
        print(f"Unique Letters: {result.unique_letters}")
        print(f"Total Verses: {result.total_verses}")
        print(f"Name Verses: {result.name_verses_count}")
        print(f"Neshama Verses: {result.neshama_verses_count}")
        print()
        
        # Show verses for each letter
        print("=== Name Letter Sections ===")
        for section in result.name_sections:
            print(f"\nLetter: {section.letter.hebrew_letter} ({section.letter.hebrew_name})")
            print(f"Section: {section.section_title}")
            print(f"Number of verses: {len(section.verses)}")
            print("Verse numbers:", [v.verse_number for v in section.verses])
            
        print("\n=== Neshama (נשמה) Sections ===")
        for section in result.neshama_sections:
            print(f"\nLetter: {section.letter.hebrew_letter} ({section.letter.hebrew_name})")
            print(f"Section: {section.section_title}")
            print(f"Number of verses: {len(section.verses)}")
            print("Verse numbers:", [v.verse_number for v in section.verses])
        
        # Verify we have 8 verses per letter
        print("\n=== Verification ===")
        all_correct = True
        for section in result.name_sections + result.neshama_sections:
            verse_count = len(section.verses)
            status = "✓" if verse_count == 8 else "✗"
            print(f"{status} Letter {section.letter.hebrew_letter}: {verse_count} verses")
            if verse_count != 8:
                all_correct = False
                
        if all_correct:
            print("\n✅ SUCCESS: All letters have exactly 8 verses!")
        else:
            print("\n❌ ERROR: Some letters don't have 8 verses!")
            
        # Test the API summary format
        print("\n=== Testing API Summary Format ===")
        summary = await engine.get_verse_summary_for_name(test_name)
        print(f"API Response has {len(summary['sections'])} sections")
        print(f"Total verses in API response: {summary['total_verses']}")


if __name__ == "__main__":
    asyncio.run(test_verse_engine())