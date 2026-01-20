#!/usr/bin/env python3
"""
Generate weekly snapshots from review data - OPTIMIZED VERSION
Uses batch processing and incremental calculations to avoid memory issues
"""

import os
from datetime import datetime, timedelta
from database import get_db_connection, safe_get
from psycopg2.extras import RealDictCursor
import json
from dotenv import load_dotenv

load_dotenv()

# Load sentiment configuration from environment
POSITIVE_RATING_MIN = int(os.getenv('POSITIVE_RATING_MIN', '4'))
NEGATIVE_RATING_MAX = int(os.getenv('NEGATIVE_RATING_MAX', '2'))
NEUTRAL_RATING = int(os.getenv('NEUTRAL_RATING', '3'))
NLP_MAX_THEMES = int(os.getenv('NLP_MAX_THEMES', '10'))

# Import NLP manager for theme extraction
try:
    from nlp_manager import nlp_manager
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False
    print("[WARNING] NLP manager not available - using basic theme extraction")


def get_week_boundaries(date):
    """Get Monday (start) and Sunday (end) for the week containing date"""
    if isinstance(date, datetime):
        date = date.date()
    
    days_since_monday = date.weekday()
    week_start = date - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def get_reviews_in_date_range(brand_id, start_date, end_date):
    """Get all reviews published within date range"""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM reviews
                WHERE brand_id = %s
                AND published_date >= %s
                AND published_date < %s + INTERVAL '1 day'
                AND is_flagged = FALSE
                ORDER BY published_date
            """, (brand_id, start_date, end_date))
            return [dict(row) for row in cur.fetchall()]


def calculate_cumulative_stats(brand_id, up_to_date):
    """
    Calculate cumulative stats efficiently using SQL aggregation
    Returns: avg_rating, response_rate, avg_response_time
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get rating stats
            cur.execute("""
                SELECT 
                    AVG(rating) as avg_rating,
                    COUNT(*) as total_reviews
                FROM reviews
                WHERE brand_id = %s
                AND published_date <= %s + INTERVAL '1 day'
                AND is_flagged = FALSE
                AND rating BETWEEN 1 AND 5
            """, (brand_id, up_to_date))
            
            rating_stats = cur.fetchone()
            avg_rating = float(rating_stats['avg_rating']) if rating_stats['avg_rating'] else 0
            total_reviews = rating_stats['total_reviews']
            
            # Get response stats
            cur.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE has_reply = TRUE) as replies,
                    COUNT(*) as total,
                    AVG(
                        EXTRACT(EPOCH FROM (reply_date - published_date)) / 86400
                    ) FILTER (WHERE has_reply = TRUE AND reply_date > published_date) as avg_days
                FROM reviews
                WHERE brand_id = %s
                AND published_date <= %s + INTERVAL '1 day'
                AND is_flagged = FALSE
            """, (brand_id, up_to_date))
            
            response_stats = cur.fetchone()
            response_rate = (response_stats['replies'] / response_stats['total'] * 100) if response_stats['total'] > 0 else 0
            avg_response_time = float(response_stats['avg_days']) if response_stats['avg_days'] else 0
            
            return {
                'avg_rating': round(avg_rating, 2),
                'total_reviews': total_reviews,
                'response_rate': round(response_rate, 2),
                'avg_response_time_days': round(avg_response_time, 2)
            }


def calculate_sentiment(reviews):
    """Calculate sentiment breakdown using env-configured thresholds"""
    sentiment = {'positive': 0, 'neutral': 0, 'negative': 0}
    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    for r in reviews:
        rating = r.get('rating')
        if rating and 1 <= rating <= 5:
            rating_counts[rating] += 1
            
            if rating >= POSITIVE_RATING_MIN:
                sentiment['positive'] += 1
            elif rating == NEUTRAL_RATING:
                sentiment['neutral'] += 1
            else:
                sentiment['negative'] += 1
    
    return sentiment, rating_counts


def get_language_distribution(reviews):
    """Get language distribution"""
    langs = {}
    for r in reviews:
        lang = r.get('language', 'unknown')
        langs[lang] = langs.get(lang, 0) + 1
    return langs


def get_source_distribution(reviews):
    """Get source/verification distribution"""
    sources = {}
    for r in reviews:
        source = r.get('verification_source', 'unknown')
        sources[source] = sources.get(source, 0) + 1
    return sources


def extract_themes_from_reviews(reviews, rating_filter):
    """
    Extract common themes from reviews based on rating
    Uses NLP if available, falls back to basic word frequency
    """
    
    if NLP_AVAILABLE:
        try:
            return nlp_manager.extract_themes(reviews, rating_filter, max_themes=NLP_MAX_THEMES)
        except Exception as e:
            print(f"  [WARNING] NLP extraction failed: {e}, falling back to basic")
    
    # Fallback: Basic word frequency
    from collections import Counter
    import re
    
    filtered_reviews = [r for r in reviews if r.get('rating') in rating_filter]
    
    all_text = ' '.join([
        (r.get('title', '') + ' ' + r.get('text', ''))
        for r in filtered_reviews
        if r.get('title') or r.get('text')
    ]).lower()
    
    words = re.findall(r'\b[a-z]{4,}\b', all_text)
    
    stop_words = {
        'that', 'this', 'with', 'have', 'from', 'they', 'been', 'were',
        'their', 'what', 'about', 'which', 'when', 'there', 'would',
        'could', 'should', 'also', 'very', 'much', 'more', 'some', 'into'
    }
    
    words = [w for w in words if w not in stop_words]
    word_freq = Counter(words)
    return [word for word, count in word_freq.most_common(NLP_MAX_THEMES)]


def create_weekly_snapshot(brand_id, week_start, week_end, prev_week_snapshot=None, cumulative_stats=None):
    """Create snapshot for a specific week - OPTIMIZED"""
    
    print(f"  Creating snapshot for {week_start} to {week_end}", end=" ")
    
    # Get reviews for this week only (small query)
    weekly_reviews = get_reviews_in_date_range(brand_id, week_start, week_end)
    
    # Use pre-calculated cumulative stats if provided
    if cumulative_stats is None:
        cumulative_stats = calculate_cumulative_stats(brand_id, week_end)
    
    # Calculate sentiment for THIS WEEK only
    sentiment, rating_counts = calculate_sentiment(weekly_reviews)
    
    # Extract themes (only from this week's reviews)
    positive_themes = extract_themes_from_reviews(weekly_reviews, [POSITIVE_RATING_MIN, 5])
    negative_themes = extract_themes_from_reviews(weekly_reviews, [1, NEGATIVE_RATING_MAX])
    
    # Previous week stats for comparison
    prev_week_review_count = prev_week_snapshot['new_reviews_this_week'] if prev_week_snapshot else 0
    prev_week_avg_rating = prev_week_snapshot['avg_rating'] if prev_week_snapshot else cumulative_stats['avg_rating']
    
    # Calculate ISO week (YYYY-W##)
    iso_year, iso_week, _ = week_start.isocalendar()
    iso_week_str = f"{iso_year}-W{iso_week:02d}"
    
    # Build snapshot data
    snapshot_data = {
        'brand_id': brand_id,
        'week_start_date': week_start,
        'week_end_date': week_end,
        'iso_week': iso_week_str,
        
        # Review Volume
        'total_reviews_to_date': cumulative_stats['total_reviews'],
        'new_reviews_this_week': len(weekly_reviews),
        'prev_week_review_count': prev_week_review_count,
        
        # Rating Performance (cumulative)
        'avg_rating': cumulative_stats['avg_rating'],
        'prev_week_avg_rating': round(prev_week_avg_rating, 2),
        
        # Sentiment (this week only)
        'positive_count': sentiment['positive'],
        'neutral_count': sentiment['neutral'],
        'negative_count': sentiment['negative'],
        
        # Response Performance (cumulative)
        'response_rate': cumulative_stats['response_rate'],
        'avg_response_time_days': cumulative_stats['avg_response_time_days'],
        
        # Content Analysis (this week only)
        'language_distribution': json.dumps(get_language_distribution(weekly_reviews)),
        'source_distribution': json.dumps(get_source_distribution(weekly_reviews)),
        'top_mentions': json.dumps([]),  # Would be populated from brand data
        'positive_themes': json.dumps(positive_themes),
        'negative_themes': json.dumps(negative_themes),
        
        # Metadata
        'sentiment_breakdown': json.dumps(rating_counts),
        'weekly_review_ids': json.dumps([r['trustpilot_review_id'] for r in weekly_reviews]),
        'ai_summary': None
    }
    
    # Insert snapshot
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO weekly_snapshots (
                    brand_id, week_start_date, week_end_date, iso_week,
                    total_reviews_to_date, new_reviews_this_week, prev_week_review_count,
                    avg_rating, prev_week_avg_rating,
                    positive_count, neutral_count, negative_count,
                    response_rate, avg_response_time_days,
                    language_distribution, source_distribution, top_mentions,
                    positive_themes, negative_themes,
                    sentiment_breakdown, weekly_review_ids, ai_summary
                ) VALUES (
                    %(brand_id)s, %(week_start_date)s, %(week_end_date)s, %(iso_week)s,
                    %(total_reviews_to_date)s, %(new_reviews_this_week)s, %(prev_week_review_count)s,
                    %(avg_rating)s, %(prev_week_avg_rating)s,
                    %(positive_count)s, %(neutral_count)s, %(negative_count)s,
                    %(response_rate)s, %(avg_response_time_days)s,
                    %(language_distribution)s, %(source_distribution)s, %(top_mentions)s,
                    %(positive_themes)s, %(negative_themes)s,
                    %(sentiment_breakdown)s, %(weekly_review_ids)s, %(ai_summary)s
                )
                ON CONFLICT (brand_id, week_start_date)
                DO UPDATE SET
                    week_end_date = EXCLUDED.week_end_date,
                    iso_week = EXCLUDED.iso_week,
                    total_reviews_to_date = EXCLUDED.total_reviews_to_date,
                    new_reviews_this_week = EXCLUDED.new_reviews_this_week,
                    prev_week_review_count = EXCLUDED.prev_week_review_count,
                    avg_rating = EXCLUDED.avg_rating,
                    prev_week_avg_rating = EXCLUDED.prev_week_avg_rating,
                    positive_count = EXCLUDED.positive_count,
                    neutral_count = EXCLUDED.neutral_count,
                    negative_count = EXCLUDED.negative_count,
                    response_rate = EXCLUDED.response_rate,
                    avg_response_time_days = EXCLUDED.avg_response_time_days,
                    language_distribution = EXCLUDED.language_distribution,
                    source_distribution = EXCLUDED.source_distribution,
                    top_mentions = EXCLUDED.top_mentions,
                    positive_themes = EXCLUDED.positive_themes,
                    negative_themes = EXCLUDED.negative_themes,
                    sentiment_breakdown = EXCLUDED.sentiment_breakdown,
                    weekly_review_ids = EXCLUDED.weekly_review_ids
            """, snapshot_data)
    
    print(f"✓ ({len(weekly_reviews)} reviews)")
    return snapshot_data


def generate_historical_snapshots(brand_id):
    """Generate snapshots for all historical weeks - OPTIMIZED"""
    
    print(f"\n[Generating Historical Snapshots - OPTIMIZED]")
    
    # Get date range of reviews
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    MIN(published_date) as first_review,
                    MAX(published_date) as last_review
                FROM reviews
                WHERE brand_id = %s AND is_flagged = FALSE
            """, (brand_id,))
            result = cur.fetchone()
            
            if not result[0]:
                print("  No reviews found")
                return
            
            first_review_date = result[0].date()
            last_review_date = result[1].date()
    
    print(f"  Review date range: {first_review_date} to {last_review_date}")
    
    # Auto-detect and install needed NLP models (one-time)
    if NLP_AVAILABLE:
        print(f"\n  [Checking NLP models...]")
        # Sample 1000 reviews for language detection
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM reviews 
                    WHERE brand_id = %s AND is_flagged = FALSE
                    ORDER BY RANDOM()
                    LIMIT 1000
                """, (brand_id,))
                sample_reviews = [dict(row) for row in cur.fetchall()]
        
        nlp_manager.ensure_models_for_reviews(sample_reviews)
        print()
    
    # Get week boundaries
    first_week_start, _ = get_week_boundaries(first_review_date)
    current_week_start, current_week_end = get_week_boundaries(datetime.now())
    
    # Generate snapshots week by week
    current_start = first_week_start
    prev_snapshot = None
    snapshot_count = 0
    
    import time
    start_time = time.time()
    
    while current_start <= current_week_start:
        week_start = current_start
        week_end = current_start + timedelta(days=6)
        
        # Calculate cumulative stats once per week
        cumulative_stats = calculate_cumulative_stats(brand_id, week_end)
        
        snapshot = create_weekly_snapshot(brand_id, week_start, week_end, prev_snapshot, cumulative_stats)
        prev_snapshot = snapshot
        snapshot_count += 1
        
        current_start += timedelta(days=7)
    
    elapsed = time.time() - start_time
    
    print(f"\n  [✓] Generated {snapshot_count} weekly snapshots in {elapsed:.1f}s")
    print(f"      From {first_week_start} to {current_week_start}")
    print(f"      Avg: {elapsed/snapshot_count:.2f}s per snapshot")
    print(f"\n  Configuration used:")
    print(f"      Positive: {POSITIVE_RATING_MIN}+ stars")
    print(f"      Neutral: {NEUTRAL_RATING} stars")
    print(f"      Negative: {NEGATIVE_RATING_MAX}- stars")
    print(f"      Max themes: {NLP_MAX_THEMES}")


def generate_current_week_snapshot(brand_id):
    """Generate snapshot for just the current week"""
    
    print(f"\n[Generating Current Week Snapshot]")
    
    current_week_start, current_week_end = get_week_boundaries(datetime.now())
    
    # Get previous week's snapshot
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM weekly_snapshots
                WHERE brand_id = %s
                AND week_start_date < %s
                ORDER BY week_start_date DESC
                LIMIT 1
            """, (brand_id, current_week_start))
            prev_snapshot = cur.fetchone()
            prev_snapshot = dict(prev_snapshot) if prev_snapshot else None
    
    snapshot = create_weekly_snapshot(brand_id, current_week_start, current_week_end, prev_snapshot)
    
    print(f"  [✓] Snapshot created for {current_week_start} to {current_week_end}")
    print(f"      New reviews this week: {snapshot['new_reviews_this_week']}")
    print(f"      Total reviews to date: {snapshot['total_reviews_to_date']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python generate_snapshots.py <brand_id> [--historical]")
        sys.exit(1)
    
    brand_id = int(sys.argv[1])
    historical = '--historical' in sys.argv
    
    if historical:
        generate_historical_snapshots(brand_id)
    else:
        generate_current_week_snapshot(brand_id)