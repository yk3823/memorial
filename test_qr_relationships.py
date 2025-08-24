#!/usr/bin/env python3
"""
Comprehensive test to verify QR memorial relationships work correctly.
This will import the models and try to trigger the relationship mappings.
"""

import sys
import os
import asyncio
import logging

# Add project root to path
sys.path.insert(0, '/Users/josephkeinan/memorial')

async def test_qr_relationships():
    """Test QR memorial relationships comprehensively."""
    print("=" * 80)
    print("COMPREHENSIVE QR MEMORIAL RELATIONSHIP TEST")
    print("=" * 80)
    
    try:
        # Test 1: Import all models
        print("\n1. Testing model imports...")
        from app.models import Memorial, QRMemorialCode, QRScanEvent, ManufacturingPartner
        from app.models.memorial import Memorial as Memorial2
        from app.models.qr_memorial import QRMemorialCode as QRCode2
        print("   ✓ All models imported successfully")
        
        # Test 2: Check table names
        print("\n2. Testing table names...")
        print(f"   Memorial table: {Memorial.__tablename__}")
        print(f"   QR Code table: {QRMemorialCode.__tablename__}")
        print(f"   QR Scan Event table: {QRScanEvent.__tablename__}")
        print(f"   Manufacturing Partner table: {ManufacturingPartner.__tablename__}")
        print("   ✓ All table names accessible")
        
        # Test 3: Check relationship attributes exist
        print("\n3. Testing relationship attributes...")
        
        # Memorial -> QR relationship
        memorial_qr_rel = getattr(Memorial, 'qr_code', None)
        print(f"   Memorial.qr_code: {memorial_qr_rel}")
        
        # QR -> Memorial relationship
        qr_memorial_rel = getattr(QRMemorialCode, 'memorial', None)
        print(f"   QRMemorialCode.memorial: {qr_memorial_rel}")
        
        # QR -> Scan Events relationship
        qr_scans_rel = getattr(QRMemorialCode, 'scan_events', None)
        print(f"   QRMemorialCode.scan_events: {qr_scans_rel}")
        
        # Partner -> QR Orders relationship
        partner_orders_rel = getattr(ManufacturingPartner, 'qr_orders', None)
        print(f"   ManufacturingPartner.qr_orders: {partner_orders_rel}")
        
        if all([memorial_qr_rel, qr_memorial_rel, qr_scans_rel, partner_orders_rel]):
            print("   ✓ All relationships defined")
        else:
            print("   ✗ Some relationships missing")
            return False
        
        # Test 4: Test model instantiation
        print("\n4. Testing model instantiation...")
        
        # Create sample instances (without saving to DB)
        import uuid
        from datetime import datetime, date
        
        sample_user_id = uuid.uuid4()
        sample_memorial_id = uuid.uuid4()
        
        # Create Memorial instance
        memorial = Memorial(
            id=sample_memorial_id,
            owner_id=sample_user_id,
            deceased_name_hebrew="יוחנן כהן",
            deceased_name_english="John Cohen",
            parent_name_hebrew="אברהם",
            death_date_gregorian=date(2023, 1, 15),
            is_public=True
        )
        print("   ✓ Memorial instance created")
        
        # Create QR Code instance
        qr_code = QRMemorialCode(
            memorial_id=sample_memorial_id,
            qr_code_data="https://memorial.com/memorial/john-cohen?source=qr",
            qr_code_url="https://memorial.com/memorial/john-cohen?source=qr&code=12345",
            design_template="standard",
            is_active=True,
            subscription_tier="basic",
            annual_fee_cents=1800
        )
        print("   ✓ QRMemorialCode instance created")
        
        # Create Scan Event instance
        scan_event = QRScanEvent(
            qr_code_id=qr_code.id,
            scanned_at=datetime.utcnow(),
            visitor_country="Israel",
            device_type="mobile",
            browser_name="Chrome",
            scan_source="gravesite"
        )
        print("   ✓ QRScanEvent instance created")
        
        # Test 5: Test relationship property access (without DB)
        print("\n5. Testing relationship property definitions...")
        
        # Test if relationship properties are defined correctly
        try:
            # This should not fail even without database connection
            memorial_rel_property = Memorial.qr_code.property
            qr_rel_property = QRMemorialCode.memorial.property
            print(f"   Memorial.qr_code relationship type: {type(memorial_rel_property)}")
            print(f"   QRMemorialCode.memorial relationship type: {type(qr_rel_property)}")
            print("   ✓ Relationship properties accessible")
        except Exception as e:
            print(f"   ✗ Relationship property error: {e}")
            return False
        
        # Test 6: Check foreign key definitions
        print("\n6. Testing foreign key definitions...")
        
        qr_table = QRMemorialCode.__table__
        memorial_fk = None
        partner_fk = None
        
        for column in qr_table.columns:
            if hasattr(column, 'foreign_keys') and column.foreign_keys:
                for fk in column.foreign_keys:
                    if 'memorials.id' in str(fk.column):
                        memorial_fk = fk
                    elif 'manufacturing_partners.id' in str(fk.column):
                        partner_fk = fk
        
        if memorial_fk:
            print(f"   ✓ Memorial foreign key found: {memorial_fk}")
        else:
            print("   ✗ Memorial foreign key not found")
            return False
            
        if partner_fk:
            print(f"   ✓ Manufacturing partner foreign key found: {partner_fk}")
        else:
            print("   ✓ Manufacturing partner foreign key optional (NULL allowed)")
        
        # Test 7: Test back_populates configuration
        print("\n7. Testing back_populates configuration...")
        
        memorial_qr_back_populates = getattr(Memorial.qr_code.property, 'back_populates', None)
        qr_memorial_back_populates = getattr(QRMemorialCode.memorial.property, 'back_populates', None)
        
        print(f"   Memorial.qr_code back_populates: {memorial_qr_back_populates}")
        print(f"   QRMemorialCode.memorial back_populates: {qr_memorial_back_populates}")
        
        if memorial_qr_back_populates == "memorial" and qr_memorial_back_populates == "qr_code":
            print("   ✓ back_populates configured correctly")
        else:
            print("   ✗ back_populates configuration issue")
            return False
        
        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED - QR MEMORIAL RELATIONSHIPS WORKING CORRECTLY")
        print("=" * 80)
        return True
        
    except ImportError as e:
        print(f"\n✗ IMPORT ERROR: {e}")
        return False
    except AttributeError as e:
        print(f"\n✗ ATTRIBUTE ERROR: {e}")
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_qr_relationships())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test execution failed: {e}")
        sys.exit(1)