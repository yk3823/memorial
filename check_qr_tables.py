#!/usr/bin/env python3
"""
Quick script to check if QR memorial tables exist in PostgreSQL
"""

import psycopg2
import sys

def check_qr_tables():
    """Check if QR memorial tables exist in the database."""
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="memorial_db", 
            user="memorial_user",
            password="memorial_pass_123"
        )
        
        cur = conn.cursor()
        
        # Check for QR-related tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%qr%'
            ORDER BY table_name;
        """)
        
        qr_tables = cur.fetchall()
        
        print("QR-related tables found:")
        if qr_tables:
            for table in qr_tables:
                print(f"  - {table[0]}")
        else:
            print("  No QR-related tables found!")
        
        # Check all tables to see what exists
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        all_tables = cur.fetchall()
        
        print(f"\nAll tables in database ({len(all_tables)} total):")
        for table in all_tables:
            print(f"  - {table[0]}")
        
        # Check if memorial table has qr-related columns
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = 'memorials'
            AND column_name LIKE '%qr%'
            ORDER BY column_name;
        """)
        
        qr_columns = cur.fetchall()
        
        print(f"\nQR-related columns in memorials table:")
        if qr_columns:
            for column in qr_columns:
                print(f"  - {column[0]} ({column[1]})")
        else:
            print("  No QR-related columns found in memorials table!")
        
        cur.close()
        conn.close()
        
        return len(qr_tables) > 0
        
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return False

if __name__ == "__main__":
    success = check_qr_tables()
    sys.exit(0 if success else 1)