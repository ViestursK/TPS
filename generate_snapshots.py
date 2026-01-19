#!/usr/bin/env python3
"""
Generate weekly snapshots from review data
Can create historical snapshots or just current week
Uses NLP for intelligent theme extraction
"""

from datetime import datetime, timedelta
from database import get_db_connection, safe_get
from psycopg2.extras import RealDictCursor
import json

# Import NLP manager for theme extraction
try:
    from nlp_manager import nlp_manager
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False
    print("[WARNING] NLP manager not available - using basic theme extraction")


def get_week_boundaries(date):
    """Get Monday (start) and Sunday (end) for the week containing date"""
    # Ensure we have a date object
    if isinstance(date, datetime):
        date = date.date()
    
    # Find Monday of the week
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


def get_reviews_up_to_date(brand_id, end_date):
    """Get all reviews up to and including end_date"""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM reviews
                WHERE brand_id = %s
                AND published_date <= %s + INTERVAL '1 day'
                AND is_flagged = FALSE
                ORDER BY published_date
            """, (brand_id, end_date))
            return [dict(row) for row in cur.fetchall()]


def calculate_sentiment(reviews):
    """Calculate sentiment breakdown"""
    sentiment = {'positive': 0, 'neutral': 0, 'negative': 0}
    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    for r in reviews:
        rating = r.get('rating')
        if rating and 1 <= rating <= 5:
            rating_counts[rating] += 1
            
            if rating >= 4:
                sentiment['positive'] += 1
            elif rating == 3:
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


def calculate_response_metrics(reviews):
    """Calculate response rate and avg response time"""
    reviews_with_reply = [r for r in reviews if r.get('has_reply')]
    
    if not reviews:
        return {'response_rate': 0, 'avg_response_time_days': 0}
    
    response_rate = (len(reviews_with_reply) / len(reviews)) * 100
    
    if not reviews_with_reply:
        return {'response_rate': response_rate, 'avg_response_time_days': 0}
    
    # Calculate avg response time
    total_days = 0
    count = 0
    for r in reviews_with_reply:
        if r.get('published_date') and r.get('reply_date'):
            diff_days = (r['reply_date'] - r['published_date']).days
            if diff_days >= 0:  # Ensure reply is after review
                total_days += diff_days
                count += 1
    
    avg_response_time = total_days / count if count > 0 else 0
    
    return {
        'response_rate': round(response_rate, 2),
        'avg_response_time_days': round(avg_response_time, 2)
    }


def extract_themes_from_reviews(reviews, rating_filter):
    """
    Extract common themes from reviews based on rating
    Uses NLP if available, falls back to basic word frequency
    """
    
    if NLP_AVAILABLE:
        # Use NLP for intelligent theme extraction
        try:
            return nlp_manager.extract_themes(reviews, rating_filter, max_themes=10)
        except Exception as e:
            print(f"  [WARNING] NLP extraction failed: {e}, falling back to basic")
    
    # Fallback: Basic word frequency (original method)
    from collections import Counter
    import re
    
    filtered_reviews = [r for r in reviews if r.get('rating') in rating_filter]
    
    # Combine all text
    all_text = ' '.join([
        (r.get('title', '') + ' ' + r.get('text', ''))
        for r in filtered_reviews
        if r.get('title') or r.get('text')
    ]).lower()
    
    # Simple word extraction
    words = re.findall(r'\b[a-z]{4,}\b', all_text)
    
    # Common stop words to ignore (English only in fallback)
    stop_words = {
        'that', 'this', 'with', 'have', 'from', 'they', 'been', 'were',
        'their', 'what', 'about', 'which', 'when', 'there', 'would',
        'could', 'should', 'also', 'very', 'much', 'more', 'some', 'into'
    }
    
    words = [w for w in words if w not in stop_words]
    
    # Get top 10 most common
    word_freq = Counter(words)
    return [word for word, count in word_freq.most_common(10)]


def get_top_mentions(brand_id):
    """Get top mentions from brand metadata"""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT trustpilot_business_id FROM brands WHERE id = %s
            """, (brand_id,))
            result = cur.fetchone()
            
            if not result:
                return []
            
            # In a real implementation, you'd fetch this from Trustpilot API
            # For now, return empty - this would be populated during scraping
            return []


def create_weekly_snapshot(brand_id, week_start, week_end, prev_week_snapshot=None):
    """Create snapshot for a specific week"""
    
    print(f"  Creating snapshot for {week_start} to {week_end}")
    
    # Get reviews for this week
    weekly_reviews = get_reviews_in_date_range(brand_id, week_start, week_end)
    
    # Get all reviews up to end of this week (for cumulative stats)
    all_reviews_to_date = get_reviews_up_to_date(brand_id, week_end)
    
    # Calculate metrics
    # Sentiment for THIS WEEK only
    sentiment, rating_counts = calculate_sentiment(weekly_reviews)
    
    # But avg rating and response metrics are cumulative (all reviews to date)
    all_sentiment, all_rating_counts = calculate_sentiment(all_reviews_to_date)
    avg_rating = sum(r * c for r, c in all_rating_counts.items()) / sum(all_rating_counts.values()) if sum(all_rating_counts.values()) > 0 else 0
    
    response_metrics = calculate_response_metrics(all_reviews_to_date)
    
    # Extract themes
    positive_themes = extract_themes_from_reviews(weekly_reviews, [4, 5])
    negative_themes = extract_themes_from_reviews(weekly_reviews, [1, 2])
    
    # Previous week stats for comparison
    prev_week_review_count = prev_week_snapshot['new_reviews_this_week'] if prev_week_snapshot else 0
    prev_week_avg_rating = prev_week_snapshot['avg_rating'] if prev_week_snapshot else avg_rating
    
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
        'total_reviews_to_date': len(all_reviews_to_date),
        'new_reviews_this_week': len(weekly_reviews),
        'prev_week_review_count': prev_week_review_count,
        
        # Rating Performance
        'avg_rating': round(avg_rating, 2),
        'prev_week_avg_rating': round(prev_week_avg_rating, 2),
        
        # Sentiment
        'positive_count': sentiment['positive'],
        'neutral_count': sentiment['neutral'],
        'negative_count': sentiment['negative'],
        
        # Response Performance
        'response_rate': response_metrics['response_rate'],
        'avg_response_time_days': response_metrics['avg_response_time_days'],
        
        # Content Analysis
        'language_distribution': json.dumps(get_language_distribution(weekly_reviews)),
        'source_distribution': json.dumps(get_source_distribution(weekly_reviews)),
        'top_mentions': json.dumps(get_top_mentions(brand_id)),
        'positive_themes': json.dumps(positive_themes),
        'negative_themes': json.dumps(negative_themes),
        
        # Metadata
        'sentiment_breakdown': json.dumps(rating_counts),
        'weekly_review_ids': json.dumps([r['trustpilot_review_id'] for r in weekly_reviews]),
        'ai_summary': None  # Would be populated from brand data during scraping
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
    
    return snapshot_data


def generate_historical_snapshots(brand_id):
    """Generate snapshots for all historical weeks that have reviews"""
    
    print(f"\n[Generating Historical Snapshots]")
    
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
    
    # Auto-detect and install needed NLP models
    if NLP_AVAILABLE:
        print(f"\n  [Checking NLP models...]")
        all_reviews = get_reviews_up_to_date(brand_id, last_review_date)
        nlp_manager.ensure_models_for_reviews(all_reviews)
        print()
    
    # Get week boundaries
    first_week_start, _ = get_week_boundaries(first_review_date)
    current_week_start, current_week_end = get_week_boundaries(datetime.now())
    
    # Generate snapshots week by week
    current_start = first_week_start
    prev_snapshot = None
    snapshot_count = 0
    
    while current_start <= current_week_start:
        week_start = current_start
        week_end = current_start + timedelta(days=6)
        
        snapshot = create_weekly_snapshot(brand_id, week_start, week_end, prev_snapshot)
        prev_snapshot = snapshot
        snapshot_count += 1
        
        current_start += timedelta(days=7)
    
    print(f"\n  [✓] Generated {snapshot_count} weekly snapshots")
    print(f"      From {first_week_start} to {current_week_start}")


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