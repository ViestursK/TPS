#!/usr/bin/env python3
"""
Trustpilot Scraper with Database Integration
Two modes: onboarding (full scrape) and update (last 30 days)
"""

import requests
from parsel import Selector
import json
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv
from database import get_or_create_brand, bulk_upsert_reviews, save_weekly_snapshot

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

BRAND_DOMAIN = os.getenv('BRANDS', 'ketogo.app').split(',')[0].strip()
MODE = os.getenv('MODE', 'update').lower()  # 'onboarding' or 'update'

# Scraper behavior settings
REQUEST_DELAY = float(os.getenv('SCRAPER_REQUEST_DELAY', '0.5'))
LANGUAGES = os.getenv('SCRAPER_LANGUAGES', 'all')
DATE_FILTER = os.getenv('SCRAPER_DATE_FILTER', 'last30days')

# Query params based on mode
if MODE == 'onboarding':
    QUERY_PARAMS = f"languages={LANGUAGES}"
    print(f"\n[MODE] ONBOARDING - Full historical scrape")
else:
    QUERY_PARAMS = f"date={DATE_FILTER}&languages={LANGUAGES}"
    print(f"\n[MODE] UPDATE - {DATE_FILTER}")

BASE_URL_CLEAN = f"https://www.trustpilot.com/review/{BRAND_DOMAIN}"
BASE_URL = f"{BASE_URL_CLEAN}?{QUERY_PARAMS}"

# JWT for unlimited pagination
JWT_TOKEN = os.getenv('JWT_ACCESS_TOKEN', '').strip()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
if JWT_TOKEN:
    HEADERS["Cookie"] = f"jwt={JWT_TOKEN}"
    print("[AUTH] JWT enabled - unlimited pagination")

# Load topics mapping
with open("tp_topics.json", "r", encoding="utf-8") as f:
    ALL_TOPICS = json.load(f)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def extract_next_data(html):
    """Extract __NEXT_DATA__ JSON from HTML"""
    selector = Selector(text=html)
    raw_json = selector.xpath("//script[@id='__NEXT_DATA__']/text()").get()
    
    if not raw_json:
        print("  [!] __NEXT_DATA__ script not found")
        return None
    
    return json.loads(raw_json)


def get_top_mentions(business_id):
    """Fetch and translate top mentions/topics"""
    url = f'https://www.trustpilot.com/api/businessunitprofile/businessunit/{business_id}/service-reviews/topics'
    try:
        response = requests.get(url, headers=HEADERS)
        response_data = json.loads(response.text)
        
        options = response_data['topics']
        translated_topics = []
        for topic in options:
            readable_name = ALL_TOPICS.get(topic, topic.replace('_', ' ').title())
            translated_topics.append(readable_name)
        
        print(f"  [+] Found {len(translated_topics)} top mentions")
        return translated_topics
    except Exception as e:
        print(f"  [!] Failed to fetch top mentions: {e}")
        return []


def calculate_sentiment(reviews):
    """Calculate sentiment breakdown, excluding flagged reviews (rating 0)"""
    # Filter out flagged/hidden reviews (rating 0)
    valid_reviews = [r for r in reviews if r.get('rating', 0) > 0]
    
    sentiment = {'positive': 0, 'neutral': 0, 'negative': 0}
    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    # Get thresholds from env
    positive_min = int(os.getenv('POSITIVE_RATING_MIN', '4'))
    negative_max = int(os.getenv('NEGATIVE_RATING_MAX', '2'))
    neutral = int(os.getenv('NEUTRAL_RATING', '3'))
    
    for r in valid_reviews:
        rating = r.get('rating')
        
        rating_counts[rating] += 1
        
        if rating >= positive_min:
            sentiment['positive'] += 1
        elif rating == neutral:
            sentiment['neutral'] += 1
        else:
            sentiment['negative'] += 1
    
    return {
        'sentiment': sentiment,
        'rating_counts': rating_counts
    }


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
        source = r.get('verification', {}).get('source', 'unknown')
        sources[source] = sources.get(source, 0) + 1
    return sources


def calculate_response_metrics(reviews):
    """Calculate response rate and avg response time"""
    reviews_with_reply = [r for r in reviews if r.get('reply')]
    
    if not reviews:
        return {'response_rate': 0, 'avg_response_time_days': 0}
    
    response_rate = (len(reviews_with_reply) / len(reviews)) * 100
    
    if not reviews_with_reply:
        return {'response_rate': response_rate, 'avg_response_time_days': 0}
    
    # Calculate avg response time
    total_days = 0
    count = 0
    for r in reviews_with_reply:
        try:
            pub_date_str = r.get('dates', {}).get('publishedDate')
            reply_date_str = r.get('reply', {}).get('publishedDate')
            
            if pub_date_str and reply_date_str:
                pub_date = datetime.strptime(pub_date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                reply_date = datetime.strptime(reply_date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                diff_days = (reply_date - pub_date).days
                total_days += diff_days
                count += 1
        except:
            continue
    
    avg_response_time = total_days / count if count > 0 else 0
    
    return {
        'response_rate': round(response_rate, 2),
        'avg_response_time_days': round(avg_response_time, 2)
    }


def get_weekly_review_ids(reviews):
    """Get review IDs from past week"""
    week_ago = datetime.now() - timedelta(days=7)
    weekly_ids = []
    
    for review in reviews:
        try:
            pub_date_str = review.get('dates', {}).get('publishedDate')
            if pub_date_str:
                review_date = datetime.strptime(pub_date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                if review_date >= week_ago:
                    weekly_ids.append(review['id'])
        except:
            continue
    
    return weekly_ids


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
        # Check both old and new structure
        source = None
        if 'labels' in r and r['labels'] and 'verification' in r['labels']:
            source = r['labels']['verification'].get('verificationSource', 'unknown')
        elif 'verification' in r and r['verification']:
            source = r['verification'].get('source', 'unknown')
        else:
            source = 'unknown'
        sources[source] = sources.get(source, 0) + 1
    return sources


# =============================================================================
# MAIN SCRAPER
# =============================================================================

def scrape_trustpilot():
    """Main scraper - adapts based on MODE"""
    print("\n" + "="*70)
    print(f"TRUSTPILOT SCRAPER - {MODE.upper()} MODE")
    print("="*70)
    print(f"Brand: {BRAND_DOMAIN}")
    print("="*70 + "\n")
    
    all_reviews = []
    company_data = {}
    business_id = None
    
    # Step 1: Fetch company info
    print(f"[1] Fetching company info from: {BASE_URL_CLEAN}")
    response_clean = requests.get(BASE_URL_CLEAN, headers=HEADERS)
    
    if response_clean.status_code != 200:
        print(f"[!] Failed to fetch page: HTTP {response_clean.status_code}")
        return None
    
    data_clean = extract_next_data(response_clean.text)
    if not data_clean:
        return None
    
    try:
        props = data_clean["props"]["pageProps"]
        business_unit = props["businessUnit"]
        
        company_data = {
            "brand_name": business_unit["displayName"],
            "domain": BRAND_DOMAIN,
            "logo_url": business_unit.get("logo", {}).get("url"),
            "business_id": business_unit["id"],
            "trust_score": business_unit["trustScore"],
            "total_reviews": business_unit["numberOfReviews"],
            "ai_summary": props.get("aiSummary", {}).get("summary")
        }
        
        business_id = business_unit["id"]
        print(f"  [+] Brand: {company_data['brand_name']}")
        print(f"  [+] Total reviews on TP: {company_data['total_reviews']}")
        print(f"  [+] Business ID: {business_id}")
        
    except KeyError as e:
        print(f"  [!] Failed to extract company data: {e}")
        return None
    
    # Get or create brand in database
    print(f"\n[2] Setting up brand in database...")
    brand = get_or_create_brand(
        domain=company_data['domain'],
        name=company_data['brand_name'],
        logo_url=company_data['logo_url'],
        business_id=business_id
    )
    print(f"  [+] Brand ID: {brand['id']}")
    
    # Get top mentions
    company_data["top_mentions"] = get_top_mentions(business_id)
    
    # Step 2: Scrape reviews and save incrementally
    print(f"\n[3] Scraping reviews from: {BASE_URL}")
    page = 1
    total_scraped = 0
    
    while True:
        url = f"{BASE_URL}&page={page}"
        print(f"  [Page {page}]", end=" ")
        
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 403:
            print(f"[STOPPED] Authentication required at page {page}")
            if not JWT_TOKEN:
                print(f"  [HINT] Add JWT_ACCESS_TOKEN to .env")
            break
        elif response.status_code != 200:
            print(f"[ERROR] HTTP {response.status_code}")
            break
        
        data = extract_next_data(response.text)
        if not data:
            print(f"[STOPPED] Could not extract data")
            break
        
        try:
            reviews = data["props"]["pageProps"]["reviews"]
            if not reviews:
                print(f"[STOPPED] No more reviews")
                break
            
            # Write to DB immediately
            bulk_upsert_reviews(brand['id'], reviews)
            all_reviews.extend(reviews)  # Still keep for snapshot calculation
            total_scraped += len(reviews)
            print(f"✓ {len(reviews)} reviews saved (Total: {total_scraped})")
            
        except KeyError:
            print(f"[STOPPED] No reviews found")
            break
        
        page += 1
        time.sleep(REQUEST_DELAY)
    
    # Step 3: Generate snapshots
    print(f"\n[4] Generating weekly snapshots...")
    
    if MODE == 'onboarding':
        # Generate historical snapshots for all weeks
        print("  Creating historical weekly snapshots...")
        from generate_snapshots import generate_historical_snapshots
        generate_historical_snapshots(brand['id'])
    else:
        # Just update current week snapshot
        print("  Updating current week snapshot...")
        from generate_snapshots import generate_current_week_snapshot
        generate_current_week_snapshot(brand['id'])
    
    print("\n" + "="*70)
    print("SCRAPING COMPLETE")
    print("="*70)
    print(f"Total Reviews Scraped: {len(all_reviews)}")
    print(f"Mode: {MODE.upper()}")
    
    return {
        "brand": brand,
        "company": company_data,
        "total_reviews": len(all_reviews)
    }


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    data = scrape_trustpilot()
    
    if data:
        print("\n[SUCCESS] Data stored in database")
    else:
        print("\n[FAILED] Scraping failed")