-- Brands table
CREATE TABLE IF NOT EXISTS brands (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    logo_url TEXT,
    trustpilot_business_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
    trustpilot_review_id VARCHAR(255) UNIQUE NOT NULL,
    rating INTEGER NOT NULL,
    title TEXT,
    text TEXT,
    language VARCHAR(10),
    location VARCHAR(255),
    published_date TIMESTAMP NOT NULL,
    updated_date TIMESTAMP,
    experience_date DATE,
    verification_source VARCHAR(50),
    has_reply BOOLEAN DEFAULT FALSE,
    reply_text TEXT,
    reply_date TIMESTAMP,
    is_flagged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weekly snapshots table
CREATE TABLE IF NOT EXISTS weekly_snapshots (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    iso_week VARCHAR(8) NOT NULL,  -- Format: YYYY-W## (e.g., 2024-W42)
    
    -- Review Volume
    total_reviews_to_date INTEGER,        -- Total reviews up to this week
    new_reviews_this_week INTEGER,        -- New reviews added this week
    prev_week_review_count INTEGER,       -- For WoW comparison
    
    -- Rating Performance
    avg_rating DECIMAL(3,2),
    prev_week_avg_rating DECIMAL(3,2),
    
    -- Sentiment Breakdown
    positive_count INTEGER,               -- 4-5 stars
    neutral_count INTEGER,                -- 3 stars
    negative_count INTEGER,               -- 1-2 stars
    
    -- Brand Response Performance
    response_rate DECIMAL(5,2),
    avg_response_time_days DECIMAL(5,2),
    
    -- Review Content Analysis (stored as JSONB)
    language_distribution JSONB,          -- {"en": 45, "da": 23, ...}
    source_distribution JSONB,            -- {"organic": 120, "invitation": 45, ...}
    top_mentions JSONB,                   -- Array of trending topics
    positive_themes JSONB,                -- Top positive themes (from reviews 4-5)
    negative_themes JSONB,                -- Top negative themes (from reviews 1-2)
    
    -- AI Summary
    ai_summary TEXT,
    
    -- Additional metadata
    sentiment_breakdown JSONB,            -- Detailed: {1: x, 2: y, 3: z, 4: a, 5: b}
    weekly_review_ids JSONB,              -- Array of review IDs from this week
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(brand_id, week_start_date),
    UNIQUE(brand_id, iso_week)
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_reviews_brand_id ON reviews(brand_id);
CREATE INDEX IF NOT EXISTS idx_reviews_published_date ON reviews(published_date);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);
CREATE INDEX IF NOT EXISTS idx_snapshots_brand_date ON weekly_snapshots(brand_id, snapshot_date);