#!/usr/bin/env python3
"""Find reviews with invalid ratings in the database"""

from database import get_db_connection
from psycopg2.extras import RealDictCursor

def find_invalid_ratings():
    """Find all reviews with ratings outside 1-5 range"""
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Find reviews with rating < 1 or > 5
            cur.execute("""
                SELECT 
                    id,
                    brand_id,
                    trustpilot_review_id,
                    rating,
                    title,
                    published_date
                FROM reviews
                WHERE rating < 1 OR rating > 5
                ORDER BY rating
            """)
            
            invalid_reviews = cur.fetchall()
            
            if invalid_reviews:
                print(f"\n[!] Found {len(invalid_reviews)} reviews with invalid ratings:\n")
                for r in invalid_reviews:
                    print(f"Rating: {r['rating']}")
                    print(f"  ID: {r['trustpilot_review_id']}")
                    print(f"  Title: {r['title']}")
                    print(f"  Date: {r['published_date']}")
                    print(f"  Link: https://www.trustpilot.com/reviews/{r['trustpilot_review_id']}")
                    print()
            else:
                print("\n[✓] All reviews have valid ratings (1-5)")
            
            # Also check for NULL ratings
            cur.execute("SELECT COUNT(*) FROM reviews WHERE rating IS NULL")
            null_count = cur.fetchone()['count']
            
            if null_count > 0:
                print(f"\n[!] Found {null_count} reviews with NULL ratings")
            
            # Show rating distribution
            cur.execute("""
                SELECT rating, COUNT(*) as count
                FROM reviews
                GROUP BY rating
                ORDER BY rating
            """)
            
            print("\n[Stats] Rating distribution:")
            for row in cur.fetchall():
                print(f"  {row['rating']} stars: {row['count']} reviews")

if __name__ == "__main__":
    find_invalid_ratings()