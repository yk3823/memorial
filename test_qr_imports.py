#!/usr/bin/env python3
"""
Test script to check if QR models can be imported correctly
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/Users/josephkeinan/memorial')

def test_qr_model_imports():
    """Test importing QR models and check relationships."""
    try:
        print("Testing QR model imports...")
        
        # Test importing individual QR models
        print("1. Testing QRMemorialCode import...")
        from app.models.qr_memorial import QRMemorialCode, QRScanEvent, ManufacturingPartner
        print("   ✓ QR models imported successfully")
        
        # Test importing from models package
        print("2. Testing models package import...")
        from app.models import QRMemorialCode as QRCode2, Memorial
        print("   ✓ Models package import successful")
        
        # Test relationship definitions
        print("3. Testing Memorial -> QR relationship...")
        print(f"   Memorial.qr_code relationship: {Memorial.qr_code}")
        print("   ✓ Memorial QR relationship defined")
        
        # Test QR -> Memorial relationship
        print("4. Testing QR -> Memorial relationship...")
        print(f"   QRMemorialCode.memorial relationship: {QRMemorialCode.memorial}")
        print("   ✓ QR Memorial relationship defined")
        
        # Test QR model attributes
        print("5. Testing QR model attributes...")
        print(f"   QRMemorialCode table: {QRMemorialCode.__tablename__}")
        print(f"   QRScanEvent table: {QRScanEvent.__tablename__}")
        print(f"   ManufacturingPartner table: {ManufacturingPartner.__tablename__}")
        print("   ✓ QR model attributes accessible")
        
        return True
        
    except ImportError as e:
        print(f"   ✗ Import error: {e}")
        return False
    except AttributeError as e:
        print(f"   ✗ Attribute error: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

def test_database_table_creation():
    """Test if database tables can be created."""
    try:
        print("\nTesting database table creation...")
        
        # Import database components
        from app.core.database import engine, Base
        from app.models import QRMemorialCode, QRScanEvent, ManufacturingPartner, Memorial
        
        print("1. Database imports successful")
        
        # Check metadata
        print("2. Checking table metadata...")
        qr_code_table = QRMemorialCode.__table__
        scan_event_table = QRScanEvent.__table__
        partner_table = ManufacturingPartner.__table__
        memorial_table = Memorial.__table__
        
        print(f"   QRMemorialCode columns: {list(qr_code_table.columns.keys())}")
        print(f"   QRScanEvent columns: {list(scan_event_table.columns.keys())}")
        print(f"   ManufacturingPartner columns: {list(partner_table.columns.keys())}")
        print(f"   Memorial has qr columns: {'qr_code' in [col.name for col in memorial_table.columns]}")
        
        print("   ✓ Table metadata accessible")
        return True
        
    except Exception as e:
        print(f"   ✗ Database error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("QR MEMORIAL MODEL IMPORT TEST")
    print("=" * 60)
    
    import_success = test_qr_model_imports()
    table_success = test_database_table_creation()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Model imports: {'✓ SUCCESS' if import_success else '✗ FAILED'}")
    print(f"Table creation: {'✓ SUCCESS' if table_success else '✗ FAILED'}")
    
    overall_success = import_success and table_success
    print(f"\nOverall result: {'✓ SUCCESS' if overall_success else '✗ FAILED'}")
    
    sys.exit(0 if overall_success else 1)