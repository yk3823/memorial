#!/usr/bin/env python3
"""
Manually create missing database tables for testing.
This script creates the payments and coupons tables that are needed for the new features.
"""

import asyncio
import asyncpg

async def create_missing_tables():
    """Create missing database tables manually."""
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
        
        # Create payments table
        print("🔧 Creating payments table...")
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                payment_id VARCHAR(100),
                order_id VARCHAR(100),
                amount NUMERIC(10, 2) NOT NULL,
                currency VARCHAR(3) NOT NULL DEFAULT 'ILS',
                description VARCHAR(500) NOT NULL DEFAULT 'Memorial Website Subscription',
                payment_method VARCHAR(20) NOT NULL DEFAULT 'paypal',
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                paypal_payer_id VARCHAR(100),
                paypal_payer_email VARCHAR(255),
                paypal_transaction_id VARCHAR(100),
                coupon_code VARCHAR(50),
                processed_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                expires_at TIMESTAMP WITH TIME ZONE,
                error_code VARCHAR(50),
                error_message TEXT,
                client_ip VARCHAR(45),
                user_agent TEXT,
                webhook_data TEXT,
                subscription_months INTEGER NOT NULL DEFAULT 1,
                max_memorials_granted INTEGER NOT NULL DEFAULT 1
            )
        """)
        
        # Create indexes for payments table
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_payment_user_status ON payments (user_id, status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_payment_method_status ON payments (payment_method, status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_payment_created_status ON payments (created_at, status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_payment_paypal_ids ON payments (payment_id, order_id, paypal_transaction_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_payment_currency_amount ON payments (currency, amount)")
        await conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_payment_payment_id_unique ON payments (payment_id) WHERE payment_id IS NOT NULL")
        await conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_payment_order_id_unique ON payments (order_id) WHERE order_id IS NOT NULL")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_payment_paypal_transaction_id ON payments (paypal_transaction_id)")
        
        print("✅ Payments table created successfully!")
        
        # Create coupons table
        print("🔧 Creating coupons table...")
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS coupons (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                code VARCHAR(100) NOT NULL UNIQUE,
                customer_name VARCHAR(255) NOT NULL,
                customer_email VARCHAR(255),
                payment_amount NUMERIC(10, 2) NOT NULL CHECK (payment_amount > 0),
                currency VARCHAR(3) NOT NULL DEFAULT 'ILS',
                is_used BOOLEAN NOT NULL DEFAULT false,
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_by_admin_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
                used_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                used_at TIMESTAMP WITH TIME ZONE,
                expires_at TIMESTAMP WITH TIME ZONE,
                office_payment_reference VARCHAR(100),
                notes TEXT,
                subscription_months INTEGER NOT NULL DEFAULT 1 CHECK (subscription_months > 0),
                max_memorials_granted INTEGER NOT NULL DEFAULT 1 CHECK (max_memorials_granted > 0),
                validation_ip VARCHAR(45),
                validation_user_agent TEXT,
                is_deleted BOOLEAN NOT NULL DEFAULT false
            )
        """)
        
        # Create indexes for coupons table
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_coupon_code ON coupons (code)")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_coupon_status_created ON coupons (status, created_at)")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_coupon_customer_name ON coupons (customer_name)")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_coupon_used_status ON coupons (is_used, status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_coupon_expires_status ON coupons (expires_at, status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_coupon_created_by_admin_id ON coupons (created_by_admin_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_coupon_used_by_user_id ON coupons (used_by_user_id)")
        
        print("✅ Coupons table created successfully!")
        
        # Create QR memorial related tables
        print("🔧 Creating QR memorial tables...")
        
        # qr_memorials table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS qr_memorials (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                code VARCHAR(50) NOT NULL UNIQUE,
                memorial_id UUID REFERENCES memorials(id) ON DELETE SET NULL,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                is_printed BOOLEAN NOT NULL DEFAULT false,
                printed_at TIMESTAMP WITH TIME ZONE,
                material VARCHAR(50) DEFAULT 'plastic',
                size VARCHAR(20) DEFAULT 'standard',
                color VARCHAR(30) DEFAULT 'black',
                custom_message TEXT,
                status VARCHAR(20) NOT NULL DEFAULT 'pending'
            )
        """)
        
        # qr_manufacturing_partners table  
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS qr_manufacturing_partners (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                name VARCHAR(255) NOT NULL,
                contact_email VARCHAR(255),
                contact_phone VARCHAR(50),
                address TEXT,
                capabilities TEXT,
                is_active BOOLEAN NOT NULL DEFAULT true
            )
        """)
        
        # qr_orders table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS qr_orders (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                partner_id UUID REFERENCES qr_manufacturing_partners(id) ON DELETE SET NULL,
                qr_memorial_id UUID NOT NULL REFERENCES qr_memorials(id) ON DELETE CASCADE,
                quantity INTEGER NOT NULL DEFAULT 1,
                total_cost NUMERIC(10, 2),
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                order_notes TEXT,
                shipped_at TIMESTAMP WITH TIME ZONE,
                delivered_at TIMESTAMP WITH TIME ZONE,
                tracking_number VARCHAR(100)
            )
        """)
        
        print("✅ QR memorial tables created successfully!")
        
        # Verify tables were created
        tables = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('payments', 'coupons', 'qr_memorials', 'qr_manufacturing_partners', 'qr_orders') ORDER BY tablename"
        )
        
        print("\n🔍 Verification - New tables created:")
        for table in tables:
            print(f"   ✅ {table['tablename']}")
        
        # Update alembic version to reflect current state
        await conn.execute("UPDATE alembic_version SET version_num = 'add_coupon_system_for_manual_payments'")
        print("✅ Updated migration version")
        
        await conn.close()
        print("\n🎉 All missing tables created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(create_missing_tables())
    if success:
        print("\n✅ Database is now ready for testing!")
    else:
        print("\n❌ Database setup failed!")