#!/usr/bin/env python3
"""
View weekly snapshots with ISO week numbers (YYYY-W##)
"""

from database import get_db_connection
from psycopg2.extras import RealDictCursor
import json


def view_snapshots(brand_id, limit=None):
    """View snapshots for a brand with ISO week format"""
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT 
                    id,
                    brand_id,
                    week_start_date,
                    week_end_date,
                    EXTRACT(ISOYEAR FROM week_start_date)::text || '-W' || 
                        LPAD(EXTRACT(WEEK FROM week_start_date)::text, 2, '0') as iso_week,
                    total_reviews_to_date,
                    new_reviews_this_week,
                    prev_week_review_count,
                    avg_rating,
                    prev_week_avg_rating,
                    positive_count,
                    neutral_count,
                    negative_count,
                    response_rate,
                    avg_response_time_days,
                    language_distribution,
                    source_distribution,
                    positive_themes,
                    negative_themes
                FROM weekly_snapshots
                WHERE brand_id = %s
                ORDER BY week_start_date DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cur.execute(query, (brand_id,))
            snapshots = cur.fetchall()
            
            if not snapshots:
                print(f"\n[!] No snapshots found for brand_id={brand_id}")
                return
            
            print(f"\n{'='*100}")
            print(f"WEEKLY SNAPSHOTS FOR BRAND ID: {brand_id}")
            print(f"{'='*100}\n")
            
            for snap in snapshots:
                # Calculate WoW changes
                review_change = snap['new_reviews_this_week'] - snap['prev_week_review_count']
                review_change_pct = (review_change / snap['prev_week_review_count'] * 100) if snap['prev_week_review_count'] > 0 else 0
                
                rating_change = snap['avg_rating'] - snap['prev_week_avg_rating']
                
                print(f"📅 {snap['iso_week']} ({snap['week_start_date']} to {snap['week_end_date']})")
                print(f"{'─'*100}")
                
                # Review Volume
                print(f"\n📊 REVIEW VOLUME:")
                print(f"   Total reviews to date: {snap['total_reviews_to_date']:,}")
                print(f"   New this week: {snap['new_reviews_this_week']}")
                print(f"   Previous week: {snap['prev_week_review_count']}")
                print(f"   WoW Change: {review_change:+d} ({review_change_pct:+.1f}%)")
                
                # Rating Performance
                print(f"\n⭐ RATING PERFORMANCE:")
                print(f"   Average rating: {snap['avg_rating']:.2f}/5")
                print(f"   Previous week: {snap['prev_week_avg_rating']:.2f}/5")
                print(f"   WoW Change: {rating_change:+.2f}")
                
                # Sentiment
                total_sentiment = snap['positive_count'] + snap['neutral_count'] + snap['negative_count']
                pos_pct = (snap['positive_count'] / total_sentiment * 100) if total_sentiment > 0 else 0
                neu_pct = (snap['neutral_count'] / total_sentiment * 100) if total_sentiment > 0 else 0
                neg_pct = (snap['negative_count'] / total_sentiment * 100) if total_sentiment > 0 else 0
                
                print(f"\n😊 SENTIMENT BREAKDOWN:")
                print(f"   Positive (4-5★): {snap['positive_count']:,} ({pos_pct:.1f}%)")
                print(f"   Neutral (3★): {snap['neutral_count']:,} ({neu_pct:.1f}%)")
                print(f"   Negative (1-2★): {snap['negative_count']:,} ({neg_pct:.1f}%)")
                
                # Response Performance
                print(f"\n💬 RESPONSE PERFORMANCE:")
                print(f"   Response rate: {snap['response_rate']:.1f}%")
                print(f"   Avg response time: {snap['avg_response_time_days']:.1f} days")
                
                # Languages
                if snap['language_distribution']:
                    langs = snap['language_distribution']  # Already a dict
                    top_langs = sorted(langs.items(), key=lambda x: x[1], reverse=True)[:3]
                    print(f"\n🌍 TOP LANGUAGES THIS WEEK:")
                    for lang, count in top_langs:
                        print(f"   {lang}: {count}")
                
                # Sources
                if snap['source_distribution']:
                    sources = snap['source_distribution']  # Already a dict
                    print(f"\n📍 REVIEW SOURCES THIS WEEK:")
                    for source, count in sources.items():
                        print(f"   {source}: {count}")
                
                # Themes
                if snap['positive_themes']:
                    pos_themes = snap['positive_themes']  # Already a list
                    if pos_themes:
                        print(f"\n✅ TOP POSITIVE THEMES:")
                        print(f"   {', '.join(pos_themes[:5])}")
                
                if snap['negative_themes']:
                    neg_themes = snap['negative_themes']  # Already a list
                    if neg_themes:
                        print(f"\n❌ TOP NEGATIVE THEMES:")
                        print(f"   {', '.join(neg_themes[:5])}")
                
                print(f"\n{'='*100}\n")


def list_brands():
    """List all brands with snapshot counts"""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    b.id,
                    b.name,
                    b.domain,
                    COUNT(ws.id) as snapshot_count,
                    MIN(ws.week_start_date) as first_snapshot,
                    MAX(ws.week_start_date) as last_snapshot
                FROM brands b
                LEFT JOIN weekly_snapshots ws ON b.id = ws.brand_id
                GROUP BY b.id, b.name, b.domain
                ORDER BY b.id
            """)
            
            brands = cur.fetchall()
            
            print(f"\n{'='*80}")
            print("BRANDS WITH SNAPSHOTS")
            print(f"{'='*80}\n")
            
            for brand in brands:
                print(f"ID: {brand['id']} | {brand['name']} ({brand['domain']})")
                print(f"   Snapshots: {brand['snapshot_count']}")
                if brand['first_snapshot']:
                    print(f"   Range: {brand['first_snapshot']} to {brand['last_snapshot']}")
                print()


def get_brand_id(identifier):
    """Get brand ID from either ID number or domain name"""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Try as integer ID first
            try:
                brand_id = int(identifier)
                cur.execute("SELECT id FROM brands WHERE id = %s", (brand_id,))
                result = cur.fetchone()
                if result:
                    return brand_id
            except ValueError:
                pass
            
            # Try as domain name
            cur.execute("SELECT id FROM brands WHERE domain = %s", (identifier,))
            result = cur.fetchone()
            if result:
                return result['id']
            
            print(f"\n[!] Brand not found: {identifier}")
            print("    Use 'python view_snapshots.py list' to see available brands")
            return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python view_snapshots.py list                           # List all brands")
        print("  python view_snapshots.py <brand_id|domain>              # View all snapshots")
        print("  python view_snapshots.py <brand_id|domain> <limit>      # View last N snapshots")
        print("\nExamples:")
        print("  python view_snapshots.py 1")
        print("  python view_snapshots.py ketogo.app")
        print("  python view_snapshots.py ketogo.app 5")
        sys.exit(1)
    
    if sys.argv[1] == 'list':
        list_brands()
    else:
        brand_id = get_brand_id(sys.argv[1])
        if brand_id:
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
            view_snapshots(brand_id, limit)