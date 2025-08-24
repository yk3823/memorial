#!/usr/bin/env python3
import asyncio
import asyncpg

async def check_db_structure():
    """Check database structure and tables."""
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='memorial123',
            database='memorial_website_db'
        )
        
        print("📊 Database Connection Successful!")
        print("=" * 50)
        
        # Check tables
        tables = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        )
        
        print(f"📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"   ✅ {table['tablename']}")
        
        print("\n" + "=" * 50)
        
        # Check if specific tables exist
        required_tables = [
            'users', 'memorials', 'photos', 'payments', 'coupons', 
            'qr_memorials', 'qr_manufacturing_partners', 'qr_orders'
        ]
        
        existing_table_names = [t['tablename'] for t in tables]
        
        print("🔍 Checking required tables:")
        for table_name in required_tables:
            if table_name in existing_table_names:
                print(f"   ✅ {table_name} - EXISTS")
            else:
                print(f"   ❌ {table_name} - MISSING")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(check_db_structure())