#!/usr/bin/env python3
"""
Seed Manufacturing Partners
Creates sample manufacturing partners for QR memorial system testing.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the parent directory to the path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.qr_memorial import ManufacturingPartner


async def seed_manufacturing_partners():
    """Create sample manufacturing partners."""
    
    settings = get_settings()
    
    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True
    )
    
    # Create session factory
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Sample manufacturing partners
    partners_data = [
        {
            "company_name": "Hebrew Memorial Arts",
            "contact_email": "orders@hebrewmemorials.com",
            "contact_phone": "+1-555-0101",
            "website_url": "https://hebrewmemorials.com",
            "specialties": ["Hebrew", "weather-resistant", "custom-designs"],
            "supported_materials": ["aluminum", "stainless-steel", "bronze"],
            "minimum_order_quantity": 1,
            "maximum_order_quantity": 50,
            "base_price_cents": 8500,  # $85.00
            "setup_fee_cents": 0,
            "rush_order_fee_cents": 2500,  # $25.00
            "turnaround_days": 7,
            "rush_turnaround_days": 3,
            "rating": 4.8,
            "total_orders": 156,
            "successful_orders": 154,
            "average_delivery_days": 6.2,
            "is_active": True,
            "is_preferred": True,
            "supports_api": True
        },
        {
            "company_name": "Premium Engravings LLC",
            "contact_email": "service@premiumengraving.com",
            "contact_phone": "+1-555-0102",
            "website_url": "https://premiumengraving.com",
            "specialties": ["high-quality", "weather-resistant", "fast-turnaround"],
            "supported_materials": ["aluminum", "stainless-steel"],
            "minimum_order_quantity": 1,
            "maximum_order_quantity": 100,
            "base_price_cents": 7500,  # $75.00
            "setup_fee_cents": 1500,   # $15.00
            "rush_order_fee_cents": 3000,  # $30.00
            "turnaround_days": 10,
            "rush_turnaround_days": 5,
            "rating": 4.5,
            "total_orders": 89,
            "successful_orders": 87,
            "average_delivery_days": 9.1,
            "is_active": True,
            "is_preferred": False,
            "supports_api": False
        },
        {
            "company_name": "Memorial Craft Solutions",
            "contact_email": "info@memorialcraft.com",
            "contact_phone": "+1-555-0103",
            "website_url": "https://memorialcraft.com",
            "specialties": ["Hebrew", "custom-designs", "bulk-orders"],
            "supported_materials": ["aluminum", "bronze", "granite"],
            "minimum_order_quantity": 5,
            "maximum_order_quantity": 200,
            "base_price_cents": 6500,  # $65.00
            "setup_fee_cents": 2500,   # $25.00
            "rush_order_fee_cents": 2000,  # $20.00
            "turnaround_days": 14,
            "rush_turnaround_days": 7,
            "rating": 4.2,
            "total_orders": 34,
            "successful_orders": 33,
            "average_delivery_days": 12.8,
            "is_active": True,
            "is_preferred": False,
            "supports_api": True
        },
        {
            "company_name": "Sacred Symbols Engraving",
            "contact_email": "orders@sacredsymbols.com",
            "contact_phone": "+1-555-0104",
            "website_url": "https://sacredsymbols.com",
            "specialties": ["Hebrew", "religious-symbols", "weather-resistant"],
            "supported_materials": ["aluminum", "stainless-steel", "brass"],
            "minimum_order_quantity": 1,
            "maximum_order_quantity": 25,
            "base_price_cents": 9500,  # $95.00
            "setup_fee_cents": 0,
            "rush_order_fee_cents": 4000,  # $40.00
            "turnaround_days": 5,
            "rush_turnaround_days": 2,
            "rating": 4.9,
            "total_orders": 78,
            "successful_orders": 78,
            "average_delivery_days": 4.8,
            "is_active": True,
            "is_preferred": True,
            "supports_api": True
        },
        {
            "company_name": "Budget Memorial Services",
            "contact_email": "contact@budgetmemorial.com",
            "contact_phone": "+1-555-0105",
            "website_url": "https://budgetmemorial.com",
            "specialties": ["affordable", "basic-designs"],
            "supported_materials": ["aluminum"],
            "minimum_order_quantity": 1,
            "maximum_order_quantity": 10,
            "base_price_cents": 4500,  # $45.00
            "setup_fee_cents": 1000,   # $10.00
            "rush_order_fee_cents": 1500,  # $15.00
            "turnaround_days": 21,
            "rush_turnaround_days": 14,
            "rating": 3.8,
            "total_orders": 23,
            "successful_orders": 21,
            "average_delivery_days": 19.5,
            "is_active": True,
            "is_preferred": False,
            "supports_api": False
        }
    ]
    
    async with async_session() as session:
        try:
            print("Creating manufacturing partners...")
            
            for partner_data in partners_data:
                # Check if partner already exists
                from sqlalchemy import select
                existing = await session.execute(
                    select(ManufacturingPartner).where(
                        ManufacturingPartner.company_name == partner_data["company_name"]
                    )
                )
                
                if existing.scalar_one_or_none():
                    print(f"Partner '{partner_data['company_name']}' already exists, skipping...")
                    continue
                
                # Create new partner
                partner = ManufacturingPartner(**partner_data)
                session.add(partner)
                print(f"Created partner: {partner_data['company_name']}")
            
            await session.commit()
            print("✅ Manufacturing partners seeded successfully!")
            
            # Display summary
            result = await session.execute(select(ManufacturingPartner))
            all_partners = result.scalars().all()
            
            print(f"\n📊 Manufacturing Partners Summary:")
            print(f"Total Partners: {len(all_partners)}")
            print(f"Active Partners: {len([p for p in all_partners if p.is_active])}")
            print(f"Preferred Partners: {len([p for p in all_partners if p.is_preferred])}")
            print(f"API-Enabled Partners: {len([p for p in all_partners if p.supports_api])}")
            
            print(f"\n💰 Pricing Range:")
            prices = [p.base_price_cents / 100 for p in all_partners]
            print(f"Min Price: ${min(prices):.2f}")
            print(f"Max Price: ${max(prices):.2f}")
            print(f"Avg Price: ${sum(prices) / len(prices):.2f}")
            
            print(f"\n⏱️ Turnaround Times:")
            turnarounds = [p.turnaround_days for p in all_partners]
            print(f"Min Days: {min(turnarounds)}")
            print(f"Max Days: {max(turnarounds)}")
            print(f"Avg Days: {sum(turnarounds) / len(turnarounds):.1f}")
            
        except Exception as e:
            print(f"❌ Error seeding manufacturing partners: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    print("🏭 Seeding Manufacturing Partners for QR Memorial System")
    print("=" * 60)
    asyncio.run(seed_manufacturing_partners())