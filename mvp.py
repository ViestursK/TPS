#!/usr/bin/env python3
"""
Trustpilot Scraper MVP - Enhanced with JWT Authentication
Extracts company data and reviews from Trustpilot with optional JWT for unlimited pagination
"""

import requests
from parsel import Selector
import json
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# CONFIGURATION FROM .ENV
# =============================================================================

BRAND_DOMAIN = os.getenv('BRANDS', 'ketogo.app').split(',')[0].strip()
MAX_PAGES_STR = os.getenv('MAX_PAGES', 'all').strip().lower()

# Parse MAX_PAGES - support 'all' or numeric value
if MAX_PAGES_STR == 'all':
    MAX_PAGES = None  # None means unlimited
    UNLIMITED_MODE = True
else:
    MAX_PAGES = int(MAX_PAGES_STR)
    UNLIMITED_MODE = False

QUERY_PARAMS = "languages=all"

# URLs
BASE_URL_CLEAN = f"https://www.trustpilot.com/review/{BRAND_DOMAIN}"
BASE_URL = f"{BASE_URL_CLEAN}?{QUERY_PARAMS}"

# =============================================================================
# HEADERS WITH JWT SUPPORT
# =============================================================================

def get_headers(use_jwt=False):
    """Get headers with optional JWT authentication"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    if use_jwt:
        jwt_token = os.getenv('JWT_ACCESS_TOKEN', '').strip()
        if jwt_token:
            headers["Cookie"] = f"jwt={jwt_token}"
            print("[SUCCESS] Using JWT authentication (unlimited scraping enabled)")
            return headers, True
        else:
            print("[WARNING] JWT not found - scraping limited to 10 pages")
            return headers, False
    
    return headers, False

# Determine if we should use JWT
# Use JWT if: unlimited mode OR max_pages > 10
NEEDS_JWT = UNLIMITED_MODE or (MAX_PAGES and MAX_PAGES > 10)
HEADERS, HAS_JWT = get_headers(use_jwt=NEEDS_JWT)

# Top Mentions Mapping
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
    """Fetch and translate top mentions/topics for the business"""
    url = f'https://www.trustpilot.com/api/businessunitprofile/businessunit/{business_id}/service-reviews/topics'
    try:
        print("  [*] Fetching top mentions...")
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


def count_past_week_reviews(reviews):
    """Count reviews from the past 7 days"""
    week_ago = datetime.now() - timedelta(days=7)
    count = 0
    
    for review in reviews:
        try:
            pub_date = review['dates']['publishedDate']
            review_date = datetime.strptime(pub_date, "%Y-%m-%dT%H:%M:%S.%fZ")
            if review_date >= week_ago:
                count += 1
        except:
            continue
    
    return count


# =============================================================================
# MAIN SCRAPER
# =============================================================================

def scrape_trustpilot(max_pages=None):
    """
    Main scraper function with JWT support
    max_pages=None means scrape ALL pages until no more reviews (requires JWT for >10 pages)
    max_pages=N means stop at page N
    """
    print("\n" + "="*70)
    print("TRUSTPILOT SCRAPER - JWT-Enhanced Version")
    print("="*70)
    print(f"Brand: {BRAND_DOMAIN}")
    print(f"Mode: {'UNLIMITED (all pages)' if max_pages is None else f'LIMITED ({max_pages} pages)'}")
    print(f"JWT Auth: {'ENABLED' if HAS_JWT else 'DISABLED (10 page limit)'}")
    print("="*70 + "\n")
    
    all_reviews = []
    company_data = {}
    business_id = None
    
    # Step 1: Fetch AI Summary
    print(f"[1] Fetching AI summary and company info from: {BASE_URL_CLEAN}")
    response_clean = requests.get(BASE_URL_CLEAN, headers=HEADERS)
    
    if response_clean.status_code != 200:
        print(f"[!] Failed to fetch clean page: HTTP {response_clean.status_code}")
        return None
    
    data_clean = extract_next_data(response_clean.text)
    if not data_clean:
        return None
    
    # Step 2: Fetch filtered reviews
    print(f"[2] Fetching filtered reviews from: {BASE_URL}")
    response = requests.get(BASE_URL, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"[!] Failed to fetch filtered page: HTTP {response.status_code}")
        data = data_clean
    else:
        data = extract_next_data(response.text)
        if not data:
            data = data_clean
    
    try:
        page_props_clean = data_clean["props"]["pageProps"]
        business_unit = page_props_clean["businessUnit"]
        page_props = data["props"]["pageProps"]
        
        # Extract company data
        company_data = {
            "brand_name": business_unit["displayName"],
            "business_id": business_unit["id"],
            "website": business_unit.get("websiteUrl", "N/A"),
            "logo_url": business_unit.get("profileImageUrl", ""),
            "total_reviews": business_unit["numberOfReviews"],
            "trust_score": business_unit["trustScore"],
            "stars": business_unit.get("stars", business_unit["trustScore"]),
            "is_claimed": business_unit.get("isClaimed", False),
            "categories": [cat["name"] for cat in business_unit.get("categories", [])],
        }
        
        if company_data["logo_url"] and company_data["logo_url"].startswith("//"):
            company_data["logo_url"] = "https:" + company_data["logo_url"]
        
        business_id = company_data["business_id"]
        
        # Get AI Summary
        ai_summary_data = page_props_clean.get("aiSummary")
        if ai_summary_data:
            company_data["ai_summary"] = {
                "summary": ai_summary_data.get("summary", "N/A"),
                "updated_at": ai_summary_data.get("updatedAt", "N/A"),
                "language": ai_summary_data.get("lang", "en"),
                "model_version": ai_summary_data.get("modelVersion", "N/A")
            }
            print("  [+] AI Summary extracted")
        else:
            company_data["ai_summary"] = None
            print("  [!] No AI Summary available")
        
        # Get initial reviews
        initial_reviews = page_props.get("reviews", [])
        all_reviews.extend(initial_reviews)
        print(f"  [+] Extracted {len(initial_reviews)} reviews from page 1")
        
        # Get Top Mentions
        if business_id:
            company_data["top_mentions"] = get_top_mentions(business_id)
        
        print(f"\n[+] Company Data Extracted:")
        print(f"    Brand: {company_data['brand_name']}")
        print(f"    Total Reviews: {company_data['total_reviews']}")
        print(f"    Trust Score: {company_data['trust_score']}/5")
        
    except KeyError as e:
        print(f"[!] Failed to extract company data: {e}")
        return None
    
    # Pagination - continue until no more reviews OR we hit max_pages
    if max_pages is None or max_pages > 1:
        if max_pages is None:
            print(f"\n[3] Fetching additional pages (unlimited - will scrape until no more reviews)...")
        else:
            print(f"\n[3] Fetching additional pages (up to {max_pages-1} more)...")
        
        page = 2
        
        while True:
            # Check if we've hit the page limit
            if max_pages is not None and page > max_pages:
                print(f"\n  [STOPPED] Reached page limit ({max_pages})")
                break
            
            print(f"\n  Fetching page {page}...")
            url = f"{BASE_URL}&page={page}"
            
            response = requests.get(url, headers=HEADERS)
            
            if response.status_code == 404:
                print(f"  [STOPPED] Reached end of pages (404)")
                break
            elif response.status_code == 403:
                print(f"  [STOPPED] Access denied (403) - JWT required for page {page}")
                if not HAS_JWT:
                    print(f"  [HINT] Add JWT_ACCESS_TOKEN to .env to scrape beyond 10 pages")
                break
            elif response.status_code != 200:
                print(f"  [ERROR] HTTP {response.status_code} at page {page} - stopping")
                break
            
            data = extract_next_data(response.text)
            if not data:
                print(f"  [STOPPED] Could not extract data from page {page}")
                break
            
            try:
                reviews = data["props"]["pageProps"]["reviews"]
                if not reviews:
                    print(f"  [STOPPED] No more reviews found")
                    break
                
                all_reviews.extend(reviews)
                print(f"  [+] Extracted {len(reviews)} reviews (Total: {len(all_reviews)})")
                
            except KeyError:
                print(f"  [STOPPED] No reviews found on page {page}")
                break
            
            page += 1
            time.sleep(0.5)  # Be polite
    
    # Calculate stats
    past_week_count = count_past_week_reviews(all_reviews)
    company_data["past_week_reviews"] = past_week_count
    
    result = {
        "company": company_data,
        "reviews": all_reviews,
        "extraction_date": datetime.now().isoformat(),
        "total_reviews_extracted": len(all_reviews)
    }
    
    print("\n" + "="*70)
    print("EXTRACTION COMPLETE")
    print("="*70)
    print(f"Total Reviews Extracted: {len(all_reviews)}")
    print(f"Past Week Reviews: {past_week_count}")
    print(f"AI Summary: {'Available' if company_data['ai_summary'] else 'Not Available'}")
    print(f"Top Mentions: {len(company_data.get('top_mentions', []))}")
    
    return result


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    data = scrape_trustpilot(max_pages=MAX_PAGES)
    
    if data:
        output_file = "trustpilot_raw_data.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\nRaw JSON saved to: {output_file}")
    else:
        print("[!] Scraping failed - no data extracted")