#!/usr/bin/env python3
"""
Create a verified test user for comprehensive API testing.
"""
import asyncio
import asyncpg
from datetime import date
import uuid
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_verified_user():
    """Create a verified test user directly in database."""
    
    # Database connection details (should match your config)
    DATABASE_URL = "postgresql://memorial_user:memorial_pass_123@localhost:5432/memorial_db"
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("Connected to database")
        
        # User details
        email = "verified_test@example.com"
        password = "TestPassword123!"
        password_hash = pwd_context.hash(password)
        user_id = uuid.uuid4()
        
        # Delete existing user if exists
        await conn.execute("DELETE FROM users WHERE email = $1", email)
        print(f"Cleaned up existing user with email: {email}")
        
        # Insert verified user
        await conn.execute("""
            INSERT INTO users (
                id, email, password_hash, first_name, last_name, phone_number,
                is_active, is_verified, subscription_status, trial_end_date,
                role, login_count, is_deleted
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """, 
            user_id, email, password_hash, "Verified", "TestUser", "+1234567890",
            True, True, "trial", date(2025, 8, 24),
            "user", 0, False
        )
        
        print(f"Created verified user:")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print(f"  ID: {user_id}")
        print(f"  Verified: True")
        
        await conn.close()
        return email, password
        
    except Exception as e:
        print(f"Error creating verified user: {e}")
        return None, None

if __name__ == "__main__":
    asyncio.run(create_verified_user())