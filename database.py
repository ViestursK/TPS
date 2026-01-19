"""Database connection and utility functions"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')


def safe_get(obj, *keys, default=None):
    """Safely get nested dict values, returns default if any key missing or value is None"""
    for key in keys:
        if obj is None or not isinstance(obj, dict):
            return default
        obj = obj.get(key)
    return obj if obj is not None else default


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_or_create_brand(domain, name=None, logo_url=None, business_id=None):
    """Get existing brand or create new one"""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Try to get existing
            cur.execute("SELECT * FROM brands WHERE domain = %s", (domain,))
            brand = cur.fetchone()
            
            if brand:
                # Update if new info provided
                if name or logo_url or business_id:
                    cur.execute("""
                        UPDATE brands 
                        SET name = COALESCE(%s, name),
                            logo_url = COALESCE(%s, logo_url),
                            trustpilot_business_id = COALESCE(%s, trustpilot_business_id),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        RETURNING *
                    """, (name, logo_url, business_id, brand['id']))
                    brand = cur.fetchone()
                return dict(brand)
            
            # Create new
            cur.execute("""
                INSERT INTO brands (domain, name, logo_url, trustpilot_business_id)
                VALUES (%s, %s, %s, %s)
                RETURNING *
            """, (domain, name or domain, logo_url, business_id))
            
            return dict(cur.fetchone())


def upsert_review(brand_id, review_data):
    """Insert or update a review"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO reviews (
                    brand_id, trustpilot_review_id, rating, title, text,
                    language, location, published_date, updated_date,
                    experience_date, verification_source, has_reply,
                    reply_text, reply_date
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (trustpilot_review_id) 
                DO UPDATE SET
                    rating = EXCLUDED.rating,
                    title = EXCLUDED.title,
                    text = EXCLUDED.text,
                    updated_date = EXCLUDED.updated_date,
                    has_reply = EXCLUDED.has_reply,
                    reply_text = EXCLUDED.reply_text,
                    reply_date = EXCLUDED.reply_date
            """, (
                brand_id,
                review_data['id'],
                review_data['rating'],
                review_data.get('title'),
                review_data.get('text'),
                review_data.get('language'),
                safe_get(review_data, 'location', 'name'),
                safe_get(review_data, 'dates', 'publishedDate'),
                safe_get(review_data, 'dates', 'updatedDate'),
                safe_get(review_data, 'dates', 'experiencedDate'),
                safe_get(review_data, 'labels', 'verification', 'verificationSource'),
                bool(review_data.get('reply')),
                safe_get(review_data, 'reply', 'message'),
                safe_get(review_data, 'reply', 'publishedDate')
            ))


def bulk_upsert_reviews(brand_id, reviews):
    """Bulk insert/update reviews for efficiency"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            data = [
                (
                    brand_id,
                    r['id'],
                    r['rating'],
                    r.get('title'),
                    r.get('text'),
                    r.get('language'),
                    safe_get(r, 'location', 'name'),
                    safe_get(r, 'dates', 'publishedDate'),
                    safe_get(r, 'dates', 'updatedDate'),
                    safe_get(r, 'dates', 'experiencedDate'),
                    safe_get(r, 'labels', 'verification', 'verificationSource'),
                    bool(r.get('reply')),
                    safe_get(r, 'reply', 'message'),
                    safe_get(r, 'reply', 'publishedDate'),
                    r.get('rating', 0) == 0  # is_flagged if rating is 0
                )
                for r in reviews
            ]
            
            execute_values(cur, """
                INSERT INTO reviews (
                    brand_id, trustpilot_review_id, rating, title, text,
                    language, location, published_date, updated_date,
                    experience_date, verification_source, has_reply,
                    reply_text, reply_date, is_flagged
                ) VALUES %s
                ON CONFLICT (trustpilot_review_id) 
                DO UPDATE SET
                    rating = EXCLUDED.rating,
                    title = EXCLUDED.title,
                    text = EXCLUDED.text,
                    updated_date = EXCLUDED.updated_date,
                    has_reply = EXCLUDED.has_reply,
                    reply_text = EXCLUDED.reply_text,
                    reply_date = EXCLUDED.reply_date,
                    is_flagged = EXCLUDED.is_flagged
            """, data)
            
    print(f"  [+] Upserted {len(reviews)} reviews")


def save_weekly_snapshot(brand_id, snapshot_data):
    """Save weekly snapshot with all report data"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO weekly_snapshots (
                    brand_id, snapshot_date, total_reviews, avg_rating,
                    positive_count, neutral_count, negative_count,
                    reviews_past_week, response_rate, avg_response_time_days,
                    top_mentions, ai_summary, language_distribution,
                    source_distribution, weekly_reviews, sentiment_breakdown
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (brand_id, snapshot_date)
                DO UPDATE SET
                    total_reviews = EXCLUDED.total_reviews,
                    avg_rating = EXCLUDED.avg_rating,
                    positive_count = EXCLUDED.positive_count,
                    neutral_count = EXCLUDED.neutral_count,
                    negative_count = EXCLUDED.negative_count,
                    reviews_past_week = EXCLUDED.reviews_past_week,
                    response_rate = EXCLUDED.response_rate,
                    avg_response_time_days = EXCLUDED.avg_response_time_days,
                    top_mentions = EXCLUDED.top_mentions,
                    ai_summary = EXCLUDED.ai_summary,
                    language_distribution = EXCLUDED.language_distribution,
                    source_distribution = EXCLUDED.source_distribution,
                    weekly_reviews = EXCLUDED.weekly_reviews,
                    sentiment_breakdown = EXCLUDED.sentiment_breakdown
            """, (
                brand_id,
                snapshot_data['snapshot_date'],
                snapshot_data['total_reviews'],
                snapshot_data['avg_rating'],
                snapshot_data['positive_count'],
                snapshot_data['neutral_count'],
                snapshot_data['negative_count'],
                snapshot_data['reviews_past_week'],
                snapshot_data.get('response_rate'),
                snapshot_data.get('avg_response_time_days'),
                snapshot_data.get('top_mentions'),
                snapshot_data.get('ai_summary'),
                snapshot_data.get('language_distribution'),
                snapshot_data.get('source_distribution'),
                snapshot_data.get('weekly_reviews'),
                snapshot_data.get('sentiment_breakdown')
            ))