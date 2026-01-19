import requests
import json
import time
from datetime import datetime, timedelta
from parsel import Selector

# =============================================================================
# CONFIGURATION
# =============================================================================

# ===== EASY CONFIGURATION =====
# Change the brand here - just the domain name (no need to modify anything else!)
BRAND_DOMAIN = "ketogo.app"  # Examples: "best.me", "ketogo.app", "certifiedfasting.com", etc. happymammoth.com

# Query parameters for filtering reviews (modify if needed)
QUERY_PARAMS = "date=last30days&languages=all"

# URLs (automatically constructed - no changes needed)
BASE_URL_CLEAN = f"https://www.trustpilot.com/review/{BRAND_DOMAIN}"  # For AI summary
BASE_URL = f"{BASE_URL_CLEAN}?{QUERY_PARAMS}"  # For reviews with filters

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Top Mentions Mapping - Full dictionary from from Trustpilot
ALL_TOPICS = json.loads('{"accountant":"Accountants","acne":"Acne","actor":"Actors","advice":"Advice","affiliate":"Affiliate","aftercare":"Aftercare","age":"Age","airline":"Airlines","airport":"Airports","airport_transfer":"Airport transfers","alarm_system":"Alarm systems","album":"Albums","alloy":"Alloys","alternatives":"Alternatives","amenities":"Amenities","ancestry":"Ancestry","animation":"Animation","app":"Application","appraisal":"Appraisal","artificial_intelligence":"Artificial intelligence","artwork":"Artwork","assignment":"Assignment","auction":"Auctions","audiologist":"Audiologists","author":"Authors","auto_insurance":"Auto insurance","back_pain":"Back pain","backpack":"Backpacks","bait":"Bait","balloon":"Balloons","bar_stool":"Bar stools","barbell":"Barbells","bass":"Bass","bath_bomb":"Bath bombs","bathroom":"Bathrooms","battery":"Batteries","beard":"Beards","bed":"Beds","bed_frame":"Bed frames","beer":"Beer","bets":"Bets","bicycle":"Bicycles","billing":"Billing","bitcoin":"Bitcoin","black_friday":"Black Friday","blinds":"Blinds","blocked_drain":"Blocked drain","boat":"Boats","boiler":"Boilers","boiler_service":"Boiler service","book":"Books","book_flight":"Booking flights","booking_process":"Booking process","bookkeeping":"Bookkeeping ","booster":"Boosters","boots":"Boots","botox":"Botox","bouquet":"Bouquets","boycott":"Boycott","bracelet":"Bracelets","breakdown_cover":"Breakdown cover","broadband":"Broadband","broker":"Brokers","brownie":"Brownies","brunch":"Brunch","bulb":"Bulbs","burger":"Burgers","buses":"Buses","business_card":"Business cards","business_environment":"Physical environment","buying_car":"Car sales","cabinet":"Cabinets","cake":"Cakes","campaign":"Campaigns","camping":"Camping","cancellation":"Cancellation","cancelled_flight":"Cancelled flights","candidate":"Candidates","candle":"Candles","canvas":"Canvases ","car":"Cars","car_insurance":"Car insurance","car_leasing":"Car leasing","car_mat":"Car mats","car_rental":"Car rentals","car_service":"Car service","caravan":"Caravans","carbon_footprint":"Carbon footprint","card_machine":"Card machines","carer":"Carers","carpet":"Carpets","carpet_cleaning":"Carpet cleaning","cash":"Cash","casino_game":"Casino games","cat":"Cats","cat_food":"Cat food","cbd_product":"CBD products","central_heating":"Central heating","chair":"Chairs","change_flight":"Flight changes","charity":"Charities ","check-in":"Check-in","checkout":"Checkout","chess":"Chess","christmas":"Christmas","cigar":"Cigars","claim":"Claim","claims":"Claims","cleaning_service":"Cleaning services","climate_change":"Climate change","clinic":"Clinics","closing":"Closing","clothing":"Clothing","coach":"Coaches","coaching":"Coaching","cocktail":"Cocktails","coffee_bean":"Coffee beans","coffee_table":"Cofee tables","collar":"Collars","color":"Colors","comic":"Comics","commission":"Commission","compensation":"Compensation","competition":"Competition","complaint":"Complaint","compliance":"Compliance","concert":"Concerts","conservatory":"Conservatory","contact":"Customer communications","contact_lenses":"Contact lenses","cooker":"Cookers","corner_sofa":"Corner sofas ","costume":"Costumes","cottage":"Cottages","course_content":"Course content","cover_letter":"Cover letters","coverage":"Coverage","covid":"Covid","credibility":"Trust","credit_score":"Credit score","creditor":"Creditors ","cremation":"Cremation","crowdfunding":"Crowdfunding","cruise":"Cruises","crypto":"Crypto currency ","crystal":"Crystal","curls":"Curls","currency":"Currency","curtains":"Curtains","cushion":"Cushions","customer_service":"Customer service","darts":"Darts","data_recovery":"Data recovery","data_science":"Data science","dating":"Dating","dealership":"Dealerships","debt":"Debt","deductible":"Deductible","delivery":"Delivery","delivery_service":"Delivery service","delivery_staff":"Delivery staff","diamond":"Diamonds","diesel":"Diesal","diet":"Diet","difficulty":"Difficulty","diffuser":"Diffusers","digital_marketing":"Digital marketing","dining_set":"Dining set","dining_table":"Dining tables","diploma":"Diploma","disability":"Disability","discount":"Discount","dog":"Dogs","dog_food":"Dog food","doll":"Dolls","domain":"Domain","door_lock":"Locks","dress":"Dresses","driver":"Drivers","driving_instructor":"Driving instructors","driving_test":"Driving test","dropshipping":"Dropshipping","dry_food":"Dry food","dumbbell":"Dumbbells","dumpster":"Dumpsters","duvet":"Duvets","duvet_cover":"Duvet covers","e-commerce":"Ecommerce","earrings":"Earrings","easter":"Easter","ebike":"E-bikes","educational_sites":"Educational sites","electric_bike":"Electric bikes","electric_scooter":"Electric scooters","electrician":"Electricians","electricity":"Electricity","email":"Email","employee":"Employee","energy_supplier":"Energy supplier","engagement_ring":"Engagement rings","engineer":"Engineers","environment":"Business environment","essential_oil":"Essential oils","estate":"Estate","estate_agent":"Estate agents","ethics":"Ethics","ev_charger":"EV chargers","exam":"Exams","exchange_rate":"Exchange rate","experience":"Experience","eye_test":"Eye test","eyewear":"Eyewear","fabric":"Fabric","facilities":"Facilities","fast_delivery":"Fast delivery","ferry":"Ferries","fertility":"Fertility","fireplace":"Fireplaces","firework":"Fireworks","first_aid":"First aid","fishing":"Fishing","fitness":"Fitness","flavor":"Flavors","flea_treatment":"Flea treatment","flight":"Flights","flooring":"Flooring","flour":"Flour","flower":"Flowers","football":"Football","forex":"Forex","fragrance":"Fragrances","fraud":"Fraud","free_delivery":"Free delivery","freezer":"Freezers","fridge":"Refrigerators","fruit":"Fruit","funding":"Funding","funeral":"Funeral","furniture":"Furniture","gallery":"Galleries","game":"Games","gaming":"Gaming","garage":"Garages","garage_door":"Garage doors","garden_centre":"Garden centers","garden_furniture":"Garden furniture","gearbox":"Gearbox","gender_inequality":"Gender inequality","gender_scan":"Pregnancy scan","germination":"Germination","gift":"Gifts","gift_box":"Gift boxes","gift_card":"Gift cards","gin":"Gin","glasses":"Glasses","glazing":"Glazing","golf":"Golf","google_ads":"Google Ads","graphic_design":"Graphic design","graphics_card":"Graphics","green_energy":"Green energy","greenhouse":"Greenhousees","groceries":"Groceries","guarantee":"Warranty","guitar":"Guitars","gutter":"Gutters","gym":"Gyms","gym_equipment":"Gym equipment","gym_wear":"Workout clothing","hair_extension":"Hair extensions","hair_loss":"Hair loss","hair_product":"Hair products","hair_removal":"Hair removal","hair_transplant":"Hair transplant","haircut":"Haircut","hamper":"Hampers","handover":"Handover","hard_drive":"Hard drives","headboard":"Headboards","headphones":"Headphones","health":"Health","health_insurance":"Health insurance","hearing_aid":"Hearing aids","hearing_test":"Hearing test","heating_system":"Heating system","helmet":"Helmets","holidays":"Holidays","home_gym":"Home gyms","home_insurance":"Home insurance","honeymoon":"Honeymoon","hoodie":"Hoodies","horse":"Horses","hosting":"Hosting","hot_tub":"Hot tubs","hot_water":"Hot water","hotel":"Hotels","housing_association":"Housing associations","hybrid":"Hybrid","immigration":"Immigration","implant":"Implants","income":"Income","information_services":"Information services","ingredient":"Ingredients","ink_cartridge":"Ink cartridges","installation_setup":"Installation setup","instructions":"Instructions","instructor":"Instructors","insulation":"Insulation","insurance":"Insurance","insurance_company":"Insurance companies","insurance_policy":"Insurance policies","insurer":"Insurers","interest_rate":"Interest rates","interior_design":"Interior design","interview":"Interviews","inventory":"Inventory","investment":"Investment","invitation":"Invitation","ipad":"iPad","iphone":"iPhone","iron":"Ironing","itinerary":"Itinerary","jacket":"Jackets","jeans":"Jeans","jewellery":"Jewelry","job_search":"Job search","job_title":"Job title","juice":"Juice","key":"Key","keyboard":"Keyboards","keyword":"Keywords","kitchen":"Kitchens","kitchen_design":"Kitchen design","knitting":"Knitting","label":"Labels","lamp":"Lamps","landlord":"Landlords","language":"Language","laptop":"Laptops","laser":"Lasers","lashes":"Lashes","laundry":"Laundry","law_firm":"Law firms","lawn":"Lawn","lawyer":"Lawyer","leasing":"Leasing","leather":"Leather","legal_service":"Legal services","leggings":"Leggings","lego":"Lego","lender":"Lenders","life_insurance":"Life insurance","loan":"Loans","location":"Location","locksmith":"Locksmiths","logo":"Logos","logo_design":"Logo design","low_carb":"Low carb","loyalty":"Loyalty","loyalty_program":"Loyalty","macbook":"MacBooks","magazine":"Magazines","makeup":"Makeup","marketing":"Marketing","mask":"Masks","massage":"Massages","math":"Math","mattress":"Mattresses","meal":"Meals","meat":"Meat","mechanic":"Mechanics","medal":"Medals","media_marketing":"Media marketing","medicine":"Medicine","meditation":"Meditation","metaverse":"Metaverse","meter_readings":"Meter readings","minecraft":"Minecraft","minibus":"Minibuses","mining":"Mining","mistake":"Mistake","mobility_scooter":"Mobility scooters","money_transfer":"Money transfer","mortgage":"Mortgages","mortgage_advisor":"Mortgage advisors","mortgage_application":"Mortgage applications","motherboard":"Motherboards","mothers_day":"Mother\'s Day","motorcycle":"Motorcycles","mover":"Movers","movie":"Movies","moving_day":"Moving day","mower":"Mowers","musician":"Musicians","nanny":"Nanny","necklace":"Necklaces","negotiations_and_settlements":"Negotiations & settlements","news":"News","notary":"Notaries","not-covered":"Not covered","nutrition":"Nutrition","office_chair":"Office chairs","office_furniture":"Office furniture","olive_oil":"Olive oil","online_pharmacy":"Online pharmacies","online_shop":"Ecommerce","opinion":"Opinion","optician":"Opticians","order":"Order","oven":"Oven","paddle_board":"Paddleboards","paint":"Paint","parcel":"Parcels","parking":"Parking","parking_facilities":"Facilities","password":"Passwords","pasta":"Pasta","paw":"Paws","payment":"Payment","payroll":"Payroll","pcr_test":"PCR test","peanut_butter":"Peanut butter","pedal":"Pedals","pension":"Pension","perfume":"Perfumes","personalised_gift":"Personalized gifts","pest_control":"Pest control","pet":"Pets","pet_insurance":"Pet insurance","petrol":"Fuel","pharmacy":"Pharmacies","phone_case":"Phone cases","photographer":"Photographers","piano":"Pianos ","piercing":"Piercings","pilates":"Pilates","pill":"Pills","pizza":"Pizza","plant":"Plants","platform":"Platform","playlist":"Playlists","plugin":"Plugins","plumber":"Plumbers","pokemon":"PokÃ©mon","portion_size":"Portion size","portrait":"Portraits","poverty":"Poverty","pregnancy":"Pregnancy","prejudice":"Prejudice","premium":"Premium","prescription":"Prescriptions","price":"Price","print":"Prints","printer":"Printers","privacy":"Privacy","prize":"Prizes","process":"Process","product":"Product","product_key":"Product keys","product_or_service":"Product","profit":"Profit","projector":"Projectors","property":"Property","protein_bar":"Protein bars","protein_powder":"Protein powder","publication":"Publication","publisher":"Publishers","puppy":"Puppies","puzzle":"Puzzles","quality":"Quality","question":"Question","quote":"Quotes","racism":"Racism","racket":"Rackets","radiator":"Radiators","rating":"Rating","reading_glasses":"Reading glasses","real_estate":"Real estate","recipe":"Recipes","recommendation":"Recommendation","recruiter":"Recruiters","recruitment":"Recruitment","refinance":"Refinancing","refund":"Refund","remote_control":"Remote controls","removal":"Removal","removal_company":"Removal companies","renewal":"Renewal","rental":"Rentals","rental_company":"Rental companies","report":"Report","response_time":"Response time","retail":"Retail","return_policy":"Return policy","road_bike":"Road bikes","rose":"Roses","rug":"Rugs","running_shoe":"Running shoes","safari":"Safari","sauce":"Sauces","sauna":"Saunas","scan":"Scans","scarf":"Scarves","scooter":"Scooters","screen_protector":"Screen protectors","scrum":"Scrum","seat":"Seats","security_system":"Security systems","seed":"Seeds","seller":"Seller","serum":"Serums","server":"Servers","server_hosting":"Server hosting","service":"Service","sewing":"Sewing","sewing_machine":"Sewing machines","shampoo":"Shampoo","shirt":"Shirts","shoes":"Shoes","shower":"Shower","shower_door":"Shower doors","shower_head":"Showerheads","shutters":"Shutters","shuttle":"Shuttles","sideboard":"Sideboards","sim_card":"Sim cards","sitter":"Sitter","sizing":"Sizing","skate":"Skating","skateboard":"Skateboards","ski":"Skiing ","skin":"Skin","skincare":"Skincare","smart-meters":"Smart meters","smell":"Smells","social_media":"Social media","socks":"Socks","sofa":"Sofas","softener":"Softeners","software":"Software","solar_panel":"Solar panels","solicitor":"Solicitors","solution":"Solution","song":"Songs","sonographer":"Sonographers","spam":"Spam","spice":"Spice","spotify":"Spotify","staff":"Staff","stairlift":"Stairlifts","stool":"Stools","storage":"Storage","storage_facility":"Storage facilities","streaming_service":"Streaming services","subscription":"Subscription","suggestion":"Suggestion","sunglasses":"Sunglasses","supplement":"Supplements","surgery":"Surgery","survey":"Surveys","sustainability":"Sustainability","sweets":"Sweets","switchover":"Switchover","t-shirt":"T-shirts","tattoo":"Tattoos","tax_preparation":"Tax preparation","tax_return":"Tax return","taxi":"Taxis","tea":"Tea","teacher":"Teachers","technology":"Technology","teeth_whitening":"Teeth whitening","tenant":"Tenants","tent":"Tents","terminal":"Terminals","test_drive":"Test driving","test_kit":"Test kits","test_result":"Test results","test_strip":"Test strips","therapist":"Therapists","ticket":"Tickets","tiles":"Tiles","timber":"Timber","time_slot":"Time slots","toilet_seat":"Toilet seats","tour_guide":"Tour guides","toy":"Toys","trademark":"Trademarking","trading_platform":"Trading platforms","trampoline":"Trampolines","transaction":"Transaction","translation":"Translation","travel_agency":"Travel agencies","travel_insurance":"Travel insurance","treadmill":"Treadmills","treatment":"Treatments","trip":"Trip","trophy":"Trophies","trousers":"Trousers","trust_and_transparency":"Trust","trustpilot":"Trustpilot","tumble_dryer":"Tumble dryers","tyre":"Tires","underwriting":"Underwriting","upgrade":"Upgrade","usefulness":"Usefulness","user_experience":"User experience","vacuum_cleaner":"Vacuum cleaners","valeting_and_preparation":"Valeting & preparation","value_for_money":"Value for money","vegan_protein":"Vegan protein","vegetable":"Vegetables","veggie":"Veggie","vehicle":"Vehicle","vet":"Veterinarians ","villa":"Villas","visa":"Visa","vitamin":"Vitamins","voucher":"Voucher","wall_art":"Wall art","wallpaper":"Wallpaper","wardrobe":"Wardrobes","warning":"Warning","warranty":"Warranty","washing_machine":"Washing machines","wasp":"Wasps","watches":"Watches","wax_melt":"Wax melts","web_design":"Web design","web_development":"Web development","web_hosting":"Web hosting","website":"Website","website_builder":"Website builders","wedding":"Weddings","wedding_day":"Wedding day","wedding_dress":"Wedding dresses","wedding_ring":"Wedding rings","weight_loss":"Weight loss","well-being":"Well-being","wetsuit":"Wetsuits","whisky":"Whisky","whitening":"Whitening","wholesale":"Wholesale","wig":"Wigs","windows_os":"Windows OS","wine":"Wine","wine_club":"Wine clubs","wine_selection":"Wine selection","wine_tasting":"Wine tastings","winning":"Winning","withdrawal":"Withdrawal","wool":"Wool","wordpress":"WordPress","work_experience":"Work experience","workout":"Workout","workwear":"Workwear","wrong_item":"Wrong item","yoga":"Yoga"}')


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
        
        # Debug: Show what we got from API
        print(f"  [DEBUG] API returned topics: {response_data.get('topics', [])[:5]}...")
        
        options = response_data['topics']
        
        # Translate technical topic names to readable names
        # Keep both key and translated value for debugging
        translated_topics = []
        for topic in options:
            readable_name = ALL_TOPICS.get(topic, topic.replace('_', ' ').title())
            translated_topics.append(readable_name)
            print(f"  [DEBUG] Mapped '{topic}' -> '{readable_name}'")
        
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


def get_rating_breakdown(trust_score, total_reviews):
    """Calculate approximate rating breakdown (simplified for MVP)"""
    # This is a simplified estimation - in production need to parse this from the page
    return {
        "trust_score": trust_score,
        "stars": trust_score,  # Trustpilot uses 1-5 scale
        "total_reviews": total_reviews
    }


# =============================================================================
# MAIN SCRAPER
# =============================================================================

def scrape_trustpilot(max_pages=None):
    """
    Main scraper function
    Returns: Dictionary with all extracted data
    """
    print("\n" + "="*70)
    print("TRUSTPILOT SCRAPER MVP - Starting Data Extraction")
    print("="*70 + "\n")
    
    all_reviews = []
    company_data = {}
    business_id = None
    
    # Step 1: Fetch AI Summary from clean URL (no query params)
    print(f"[1] Fetching AI summary and company info from: {BASE_URL_CLEAN}")
    response_clean = requests.get(BASE_URL_CLEAN, headers=HEADERS)
    
    if response_clean.status_code != 200:
        print(f"[!] Failed to fetch clean page: HTTP {response_clean.status_code}")
        return None
    
    data_clean = extract_next_data(response_clean.text)
    if not data_clean:
        return None
    
    # Step 2: Fetch filtered reviews from URL with query params
    print(f"[2] Fetching filtered reviews from: {BASE_URL}")
    response = requests.get(BASE_URL, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"[!] Failed to fetch filtered page: HTTP {response.status_code}")
        # Continue anyway, we have company data from clean URL
        data = data_clean
    else:
        data = extract_next_data(response.text)
        if not data:
            data = data_clean  # Fallback to clean data
    
    try:
        # Get AI summary from clean URL data
        page_props_clean = data_clean["props"]["pageProps"]
        business_unit = page_props_clean["businessUnit"]
        
        # Get reviews from filtered URL data
        page_props = data["props"]["pageProps"]
        
        # Extract company/brand information
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
        
        # Fix logo URL - add https: if it starts with //
        if company_data["logo_url"] and company_data["logo_url"].startswith("//"):
            company_data["logo_url"] = "https:" + company_data["logo_url"]
        
        business_id = company_data["business_id"]
        
        # Get AI Summary from clean URL (without query params)
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
        print(f"    Categories: {', '.join(company_data['categories'][:3])}")
        
    except KeyError as e:
        print(f"[!] Failed to extract company data: {e}")
        return None
    
    # Pagination through additional pages
    if max_pages and max_pages > 1:
        print(f"\n[3] Fetching additional pages (up to {max_pages-1} more)...")
        page = 2
        
        while page <= max_pages:
            print(f"\n  Fetching page {page}...")
            url = f"{BASE_URL}&page={page}"
            
            response = requests.get(url, headers=HEADERS)
            
            if response.status_code == 404:
                print(f"  [X] Reached end of pages")
                break
            
            data = extract_next_data(response.text)
            if not data:
                break
            
            try:
                reviews = data["props"]["pageProps"]["reviews"]
                if not reviews:
                    break
                
                all_reviews.extend(reviews)
                print(f"  [+] Extracted {len(reviews)} reviews (Total: {len(all_reviews)})")
                
            except KeyError:
                break
            
            page += 1
            time.sleep(2)  # Be polite :)
    
    # Calculate past week reviews
    past_week_count = count_past_week_reviews(all_reviews)
    company_data["past_week_reviews"] = past_week_count
    
    # Compile final result
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
    # Scrape data (adjust as needed, but public visitors can acces only first 10 pages)
    data = scrape_trustpilot(max_pages=10)
    
    if data:
        # Save raw JSON for further processing
        with open("trustpilot_raw_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Raw JSON saved to: trustpilot_raw_data.json")
    else:
        print("[!] Scraping failed - no data extracted")