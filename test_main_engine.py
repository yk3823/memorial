#!/usr/bin/env python3
"""
Test script for the MAIN ENGINE - Memorial Verse Engine
Tests the core functionality that provides all verses for Hebrew names.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import create_database_engine, create_session_factory
from app.core.config import settings
from app.services.memorial_verse_engine import MemorialVerseEngine


async def test_main_engine():
    """Test the main memorial verse engine."""
    print("🎯 Testing MAIN ENGINE - Memorial Verse Engine")
    print("=" * 60)
    
    # Create database connection
    engine = create_database_engine(str(settings.SQLALCHEMY_DATABASE_URI), echo=False)
    session_factory = create_session_factory(engine)
    
    async with session_factory() as session:
        engine_instance = MemorialVerseEngine(session)
        
        # Test with "יוסף"
        test_name = "יוסף"
        print(f"\n🕯️ Testing memorial verses for '{test_name}'")
        print("-" * 50)
        
        try:
            result = await engine_instance.generate_memorial_verses(test_name)
            
            print(f"✅ Successfully generated verses for '{result.hebrew_name}'")
            print(f"📊 Statistics:")
            print(f"   - Total verses: {result.total_verses}")
            print(f"   - Name verses: {result.name_verses_count}")
            print(f"   - נשמה verses: {result.neshama_verses_count}")
            print(f"   - Name letters: {result.name_letters}")
            print(f"   - Unique letters: {result.unique_letters}")
            
            print(f"\n📜 Sections:")
            
            # Display name sections
            print(f"\n🔤 Name sections ({len(result.name_sections)}):")
            for i, section in enumerate(result.name_sections):
                print(f"   {i+1}. {section.section_title}")
                print(f"      Letter: {section.letter.hebrew_letter} ({section.letter.hebrew_name})")
                print(f"      Verses: {len(section.verses)}")
                if section.verses:
                    print(f"      First verse: {section.verses[0].verse_number} - {section.verses[0].hebrew_text[:50]}...")
                    print(f"      Last verse: {section.verses[-1].verse_number} - {section.verses[-1].hebrew_text[:50]}...")
            
            # Display נשמה sections  
            print(f"\n✨ נשמה sections ({len(result.neshama_sections)}):")
            for i, section in enumerate(result.neshama_sections):
                print(f"   {i+1}. {section.section_title}")
                print(f"      Letter: {section.letter.hebrew_letter} ({section.letter.hebrew_name})")
                print(f"      Verses: {len(section.verses)}")
                if section.verses:
                    print(f"      First verse: {section.verses[0].verse_number} - {section.verses[0].hebrew_text[:50]}...")
            
            # Test API summary format
            print(f"\n📋 Testing API summary format:")
            summary = await engine_instance.get_verse_summary_for_name(test_name)
            print(f"   API Response keys: {list(summary.keys())}")
            print(f"   Sections count: {len(summary['sections'])}")
            print(f"   Total verses: {summary['total_verses']}")
            
        except Exception as e:
            print(f"❌ Error testing '{test_name}': {e}")
            import traceback
            traceback.print_exc()
    
    await engine.dispose()
    print(f"\n🎉 Main engine test completed!")


async def test_multiple_names():
    """Test multiple Hebrew names with the main engine."""
    print(f"\n🌟 Testing Multiple Names")
    print("=" * 40)
    
    engine = create_database_engine(str(settings.SQLALCHEMY_DATABASE_URI), echo=False)
    session_factory = create_session_factory(engine)
    
    test_names = ["יוסף", "מרים", "אברהם", "שרה", "דוד"]
    
    async with session_factory() as session:
        engine_instance = MemorialVerseEngine(session)
        
        for name in test_names:
            try:
                result = await engine_instance.generate_memorial_verses(name)
                print(f"✅ {name}: {result.total_verses} verses "
                      f"({result.name_verses_count} name + {result.neshama_verses_count} נשמה)")
                
                # Show letter breakdown
                letters_info = []
                for section in result.name_sections:
                    letters_info.append(f"{section.letter.hebrew_letter}({len(section.verses)})")
                
                print(f"    Letters: {' + '.join(letters_info)} + נשמה({result.neshama_verses_count})")
                
            except Exception as e:
                print(f"❌ {name}: Error - {e}")
    
    await engine.dispose()


if __name__ == "__main__":
    print("🚀 Starting Main Engine Tests")
    print("📖 Testing Memorial Verse Engine with Psalm 119 database")
    
    try:
        # Run main engine test
        asyncio.run(test_main_engine())
        
        # Run multiple names test
        asyncio.run(test_multiple_names())
        
        print("\n🎊 All main engine tests completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⛔ Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()