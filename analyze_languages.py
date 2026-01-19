#!/usr/bin/env python3
"""
Analyze language distribution across all reviews to determine which NLP models to include
"""

from database import get_db_connection
from psycopg2.extras import RealDictCursor
from collections import Counter


def analyze_languages(brand_id=None):
    """Analyze language distribution for all reviews or specific brand"""
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if brand_id:
                # Specific brand
                cur.execute("""
                    SELECT language, COUNT(*) as count
                    FROM reviews
                    WHERE brand_id = %s AND is_flagged = FALSE
                    GROUP BY language
                    ORDER BY count DESC
                """, (brand_id,))
                
                cur.execute("""
                    SELECT name, domain FROM brands WHERE id = %s
                """, (brand_id,))
                brand = cur.fetchone()
                brand_name = f"{brand['name']} ({brand['domain']})" if brand else f"Brand ID {brand_id}"
            else:
                # All brands
                cur.execute("""
                    SELECT language, COUNT(*) as count
                    FROM reviews
                    WHERE is_flagged = FALSE
                    GROUP BY language
                    ORDER BY count DESC
                """)
                brand_name = "All Brands"
            
            languages = cur.fetchall()
            
            if not languages:
                print(f"\n[!] No reviews found")
                return
            
            # Calculate totals
            total_reviews = sum(lang['count'] for lang in languages)
            
            print(f"\n{'='*80}")
            print(f"LANGUAGE DISTRIBUTION - {brand_name}")
            print(f"{'='*80}\n")
            print(f"Total Reviews: {total_reviews:,}\n")
            
            # Print detailed breakdown
            print(f"{'Language':<15} {'Count':<12} {'Percentage':<12} {'Bar'}")
            print(f"{'-'*80}")
            
            for lang in languages:
                language = lang['language'] or 'unknown'
                count = lang['count']
                percentage = (count / total_reviews * 100)
                bar_length = int(percentage / 2)  # Scale to 50 chars max
                bar = '█' * bar_length
                
                print(f"{language:<15} {count:<12,} {percentage:>6.2f}%     {bar}")
            
            print(f"\n{'-'*80}\n")
            
            # Recommendations
            print("📦 RECOMMENDED NLP MODELS:")
            print(f"{'-'*80}")
            
            # Languages with >5% coverage
            significant_langs = [l for l in languages if (l['count'] / total_reviews * 100) >= 5]
            
            # Map language codes to spaCy model names
            spacy_models = {
                'en': 'en_core_web_sm',
                'de': 'de_core_news_sm',
                'fr': 'fr_core_news_sm',
                'es': 'es_core_news_sm',
                'it': 'it_core_news_sm',
                'pt': 'pt_core_news_sm',
                'nl': 'nl_core_news_sm',
                'da': 'da_core_news_sm',
                'sv': 'sv_core_news_sm',
                'no': 'nb_core_news_sm',
                'fi': 'fi_core_news_sm',
                'pl': 'pl_core_news_sm',
                'ro': 'ro_core_news_sm',
                'el': 'el_core_news_sm',
                'ja': 'ja_core_news_sm',
                'zh': 'zh_core_web_sm',
                'ko': 'ko_core_news_sm',
                'ru': 'ru_core_news_sm',
                'uk': 'uk_core_news_sm',
                'ca': 'ca_core_news_sm',
                'hr': 'hr_core_news_sm',
                'lt': 'lt_core_news_sm',
                'mk': 'mk_core_news_sm',
                'sl': 'sl_core_news_sm',
            }
            
            if significant_langs:
                print("\nLanguages with >5% coverage (recommended):")
                install_commands = []
                
                for lang in significant_langs:
                    language = lang['language'] or 'unknown'
                    percentage = (lang['count'] / total_reviews * 100)
                    model = spacy_models.get(language, '❌ Not available')
                    
                    if model != '❌ Not available':
                        print(f"  ✓ {language:<10} ({percentage:>5.1f}%) → {model}")
                        install_commands.append(f"python -m spacy download {model}")
                    else:
                        print(f"  ✗ {language:<10} ({percentage:>5.1f}%) → No spaCy model available")
                
                if install_commands:
                    print(f"\n📥 Installation commands:")
                    print(f"{'-'*80}")
                    for cmd in install_commands:
                        print(f"  {cmd}")
                
                # Calculate coverage
                covered_count = sum(l['count'] for l in significant_langs if spacy_models.get(l['language']))
                coverage_pct = (covered_count / total_reviews * 100)
                print(f"\n📊 Coverage with these models: {coverage_pct:.1f}% of all reviews")
            
            else:
                print("No languages found with >5% coverage")
            
            # Show languages with 1-5% coverage
            minor_langs = [l for l in languages if 1 <= (l['count'] / total_reviews * 100) < 5]
            if minor_langs:
                print(f"\n\nLanguages with 1-5% coverage (optional):")
                for lang in minor_langs:
                    language = lang['language'] or 'unknown'
                    percentage = (lang['count'] / total_reviews * 100)
                    model = spacy_models.get(language, '❌ Not available')
                    print(f"  • {language:<10} ({percentage:>5.1f}%) → {model}")
            
            print(f"\n{'='*80}\n")


def compare_brands():
    """Compare language distribution across all brands"""
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get all brands
            cur.execute("""
                SELECT id, name, domain FROM brands ORDER BY id
            """)
            brands = cur.fetchall()
            
            if not brands:
                print("\n[!] No brands found")
                return
            
            print(f"\n{'='*100}")
            print(f"LANGUAGE COMPARISON ACROSS BRANDS")
            print(f"{'='*100}\n")
            
            for brand in brands:
                cur.execute("""
                    SELECT language, COUNT(*) as count
                    FROM reviews
                    WHERE brand_id = %s AND is_flagged = FALSE
                    GROUP BY language
                    ORDER BY count DESC
                    LIMIT 5
                """, (brand['id'],))
                
                langs = cur.fetchall()
                total = sum(l['count'] for l in langs)
                
                print(f"{brand['name']} ({brand['domain']}):")
                print(f"  Total reviews: {total:,}")
                print(f"  Top languages:")
                for lang in langs:
                    pct = (lang['count'] / total * 100) if total > 0 else 0
                    print(f"    - {lang['language']}: {lang['count']:,} ({pct:.1f}%)")
                print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python analyze_languages.py all                    # Analyze all brands combined")
        print("  python analyze_languages.py compare                # Compare across brands")
        print("  python analyze_languages.py <brand_id|domain>      # Analyze specific brand")
        print("\nExamples:")
        print("  python analyze_languages.py all")
        print("  python analyze_languages.py 1")
        print("  python analyze_languages.py ketogo.app")
        sys.exit(1)
    
    if sys.argv[1] == 'all':
        analyze_languages()
    elif sys.argv[1] == 'compare':
        compare_brands()
    else:
        # Try to get brand ID
        try:
            brand_id = int(sys.argv[1])
        except ValueError:
            # Must be domain name
            from database import get_db_connection
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM brands WHERE domain = %s", (sys.argv[1],))
                    result = cur.fetchone()
                    if result:
                        brand_id = result[0]
                    else:
                        print(f"\n[!] Brand not found: {sys.argv[1]}")
                        sys.exit(1)
        
        analyze_languages(brand_id)