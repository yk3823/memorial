#!/usr/bin/env python3
"""
Test script for Hebrew name to verse selection algorithm.
Demonstrates the core functionality with real Hebrew names.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import create_database_engine, create_session_factory
from app.core.config import settings
from app.services.verse_selection import HebrewNameToVerseSelector, SelectionMethod


async def test_verse_selection():
    """Test the Hebrew name to verse selection algorithm."""
    print("🔍 Testing Hebrew Name to Verse Selection Algorithm")
    print("=" * 60)
    
    # Create database connection
    engine = create_database_engine(str(settings.SQLALCHEMY_DATABASE_URI), echo=False)
    session_factory = create_session_factory(engine)
    
    async with session_factory() as session:
        selector = HebrewNameToVerseSelector(session)
        
        # Test names
        test_names = [
            "יוסף",      # Joseph - common Hebrew name
            "מרים",      # Miriam - female name
            "אברהם",     # Abraham - patriarchal name
            "שרה",       # Sarah - simple name
            "יהודה",     # Judah - longer name
            "רחל"        # Rachel - another female name
        ]
        
        for name in test_names:
            print(f"\n🌟 Testing name: {name}")
            print("-" * 40)
            
            try:
                # Analyze the name
                name_analysis = await selector.analyze_hebrew_name(name)
                
                print(f"📊 Name Analysis:")
                print(f"   Original: {name_analysis.original_name}")
                print(f"   Cleaned: {name_analysis.cleaned_name}")
                print(f"   Letters: {name_analysis.unique_letters}")
                print(f"   Length: {name_analysis.name_length}")
                print(f"   Gematria: {name_analysis.total_gematria}")
                print(f"   Complexity: {name_analysis.complexity_score:.2f}")
                
                # Select verses using balanced method
                verses, analysis = await selector.select_verses_for_name(
                    name=name,
                    verses_per_letter=1,
                    selection_method=SelectionMethod.BALANCED,
                    include_neshama=True
                )
                
                print(f"\n📜 Selected Verses ({len(verses)} total):")
                
                # Show name-based verses
                name_verses = [v for v in verses if not v.is_neshama_verse]
                print(f"\n   Name verses ({len(name_verses)}):")
                for i, selection in enumerate(name_verses):
                    verse = selection.verse
                    letter = selection.letter
                    print(f"   {i+1}. [{letter.hebrew_letter}] תהילים קיט:{verse.verse_number}")
                    print(f"      {verse.hebrew_text}")
                    print(f"      {verse.english_text}")
                    print(f"      Quality: {selection.quality_score:.2f}")
                
                # Show נשמה verses
                neshama_verses = [v for v in verses if v.is_neshama_verse]
                if neshama_verses:
                    print(f"\n   נשמה verses ({len(neshama_verses)}):")
                    for i, selection in enumerate(neshama_verses):
                        verse = selection.verse
                        letter = selection.letter
                        print(f"   {i+1}. [{letter.hebrew_letter}] תהילים קיט:{verse.verse_number}")
                        print(f"      {verse.hebrew_text}")
                        print(f"      Quality: {selection.quality_score:.2f}")
                
                print(f"\n   Total verses for {name}: {len(verses)}")
                
            except Exception as e:
                print(f"❌ Error testing name '{name}': {e}")
                continue
    
    await engine.dispose()
    print(f"\n✅ Verse selection algorithm testing completed!")


async def test_different_methods():
    """Test different verse selection methods."""
    print(f"\n🔬 Testing Different Selection Methods")
    print("=" * 50)
    
    engine = create_database_engine(str(settings.SQLALCHEMY_DATABASE_URI), echo=False)
    session_factory = create_session_factory(engine)
    
    test_name = "דוד"  # David - a name with repeated letter
    methods = [
        SelectionMethod.SEQUENTIAL,
        SelectionMethod.BALANCED,
        SelectionMethod.RANDOM,
        SelectionMethod.WEIGHTED
    ]
    
    async with session_factory() as session:
        selector = HebrewNameToVerseSelector(session)
        
        for method in methods:
            print(f"\n📋 Method: {method.value}")
            print("-" * 30)
            
            try:
                verses, analysis = await selector.select_verses_for_name(
                    name=test_name,
                    verses_per_letter=2,  # More verses to see difference
                    selection_method=method,
                    include_neshama=False  # Focus on name verses
                )
                
                name_verses = [v for v in verses if not v.is_neshama_verse]
                print(f"   Selected {len(name_verses)} verses:")
                for selection in name_verses:
                    verse = selection.verse
                    letter = selection.letter
                    print(f"   [{letter.hebrew_letter}] Verse {verse.verse_number} (section {verse.verse_in_section})")
                
            except Exception as e:
                print(f"   ❌ Error with method {method.value}: {e}")
    
    await engine.dispose()


if __name__ == "__main__":
    print("🚀 Starting Hebrew Name to Verse Selection Tests")
    print("📖 Testing with Psalm 119 database")
    
    try:
        # Run basic tests
        asyncio.run(test_verse_selection())
        
        # Run method comparison tests
        asyncio.run(test_different_methods())
        
        print("\n🎉 All tests completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⛔ Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()