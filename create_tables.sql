-- Simple table creation for Memorial Website
-- Skip complex features for now and just create what we need for basic functionality

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20),
    hebrew_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    verification_token VARCHAR(255),
    reset_password_token VARCHAR(255),
    reset_password_expires_at TIMESTAMP,
    subscription_status VARCHAR(20) DEFAULT 'trial' NOT NULL,
    subscription_end_date DATE,
    trial_end_date DATE,
    role VARCHAR(20) DEFAULT 'user' NOT NULL,
    last_login_at TIMESTAMP,
    login_count INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

-- Memorials table
CREATE TABLE IF NOT EXISTS memorials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id),
    deceased_name_hebrew VARCHAR(255),
    deceased_name_english VARCHAR(255),
    birth_date_gregorian DATE,
    birth_date_hebrew VARCHAR(50),
    death_date_gregorian DATE NOT NULL,
    death_date_hebrew VARCHAR(50),
    biography TEXT,
    memorial_song_url VARCHAR(500),
    yahrzeit_date_hebrew VARCHAR(50),
    next_yahrzeit_gregorian DATE,
    unique_slug VARCHAR(100) UNIQUE NOT NULL,
    page_views INTEGER DEFAULT 0 NOT NULL,
    is_public BOOLEAN DEFAULT FALSE NOT NULL,
    is_locked BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

-- Photos table
CREATE TABLE IF NOT EXISTS photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memorial_id UUID NOT NULL REFERENCES memorials(id),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    width INTEGER,
    height INTEGER,
    is_primary BOOLEAN DEFAULT FALSE NOT NULL,
    display_order INTEGER DEFAULT 0 NOT NULL,
    caption TEXT,
    alt_text VARCHAR(255),
    is_public BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

-- Contacts table
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memorial_id UUID NOT NULL REFERENCES memorials(id),
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255),
    phone_number VARCHAR(20),
    relationship VARCHAR(100),
    contact_type VARCHAR(20) DEFAULT 'email' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_memorials_owner ON memorials(owner_id);
CREATE INDEX IF NOT EXISTS idx_memorials_slug ON memorials(unique_slug);
CREATE INDEX IF NOT EXISTS idx_photos_memorial ON photos(memorial_id);
CREATE INDEX IF NOT EXISTS idx_contacts_memorial ON contacts(memorial_id);