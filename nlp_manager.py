#!/usr/bin/env python3
"""
NLP Manager - Auto-detects languages and installs spaCy models on demand
"""

import subprocess
import sys
from pathlib import Path
import json

# Map language codes to spaCy models
SPACY_MODELS = {
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
}

# Cache file to track installed models
CACHE_FILE = Path.home() / '.trustpilot_nlp_cache.json'


class NLPManager:
    """Manages spaCy models - auto-installs on first use"""
    
    def __init__(self, min_coverage_pct=5.0):
        """
        Args:
            min_coverage_pct: Only install models for languages with >= this % of reviews
        """
        self.min_coverage_pct = min_coverage_pct
        self.loaded_models = {}
        self.installed_models = self._load_cache()
    
    def _load_cache(self):
        """Load cache of installed models"""
        if CACHE_FILE.exists():
            with open(CACHE_FILE, 'r') as f:
                return set(json.load(f))
        return set()
    
    def _save_cache(self):
        """Save cache of installed models"""
        with open(CACHE_FILE, 'w') as f:
            json.dump(list(self.installed_models), f)
    
    def _is_model_installed(self, model_name):
        """Check if spaCy model is installed"""
        if model_name in self.installed_models:
            return True
        
        try:
            import spacy
            spacy.load(model_name)
            self.installed_models.add(model_name)
            self._save_cache()
            return True
        except:
            return False
    
    def _install_model(self, model_name):
        """Install spaCy model"""
        print(f"  [📥] Installing {model_name}...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "spacy", "download", model_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.installed_models.add(model_name)
            self._save_cache()
            print(f"  [✓] {model_name} installed successfully")
            return True
        except subprocess.CalledProcessError:
            print(f"  [✗] Failed to install {model_name}")
            return False
    
    def get_language_distribution(self, reviews):
        """Get language distribution from reviews"""
        from collections import Counter
        langs = [r.get('language', 'unknown') for r in reviews if not r.get('is_flagged')]
        return Counter(langs)
    
    def ensure_models_for_reviews(self, reviews):
        """
        Analyze reviews and auto-install needed models
        Returns: dict of {lang_code: model_name} for languages meeting threshold
        """
        if not reviews:
            return {}
        
        # Get language distribution
        lang_dist = self.get_language_distribution(reviews)
        total_reviews = sum(lang_dist.values())
        
        # Find languages meeting threshold
        needed_langs = {}
        for lang, count in lang_dist.items():
            percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
            
            if percentage >= self.min_coverage_pct and lang in SPACY_MODELS:
                model_name = SPACY_MODELS[lang]
                needed_langs[lang] = model_name
        
        if not needed_langs:
            print("  [ℹ] No languages meet coverage threshold for NLP processing")
            return {}
        
        # Install missing models
        print(f"\n  [NLP] Found {len(needed_langs)} languages meeting {self.min_coverage_pct}% threshold")
        
        for lang, model_name in needed_langs.items():
            count = lang_dist[lang]
            pct = (count / total_reviews * 100)
            print(f"    • {lang}: {count} reviews ({pct:.1f}%)", end="")
            
            if not self._is_model_installed(model_name):
                print(f" - needs installation")
                self._install_model(model_name)
            else:
                print(f" - ✓ already installed")
        
        return needed_langs
    
    def load_model(self, model_name):
        """Load a spaCy model (cached)"""
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]
        
        try:
            import spacy
            nlp = spacy.load(model_name)
            self.loaded_models[model_name] = nlp
            return nlp
        except Exception as e:
            # Silently skip - model not installed/available
            return None
    
    def extract_themes(self, reviews, rating_filter, max_themes=10, auto_install=False):
        """
        Extract themes from reviews using NLP
        
        Args:
            reviews: List of review dicts
            rating_filter: List of ratings to include (e.g., [1, 2] for negative)
            max_themes: Max number of themes to return
            auto_install: If True, auto-install missing models (only use at brand level)
        
        Returns:
            List of theme strings
        """
        # Group reviews by language
        reviews_by_lang = {}
        for r in reviews:
            if r.get('rating') in rating_filter:
                lang = r.get('language', 'unknown')
                if lang not in reviews_by_lang:
                    reviews_by_lang[lang] = []
                reviews_by_lang[lang].append(r)
        
        # Multi-language stop words (pronouns, articles, common words)
        stop_words = {
            # English
            'this', 'that', 'they', 'them', 'their', 'these', 'those', 'what', 'which',
            'who', 'whom', 'whose', 'when', 'where', 'why', 'how', 'there', 'here',
            'your', 'yours', 'mine', 'ours', 'theirs',
            # German
            'sich', 'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einer',
            'eines', 'einem', 'einen', 'ich', 'mich', 'mir', 'du', 'dich', 'dir',
            'sie', 'ihm', 'ihn', 'wir', 'uns', 'ihr', 'euch', 'ihnen',
            # French
            'le', 'la', 'les', 'un', 'une', 'des', 'ce', 'cet', 'cette', 'ces',
            'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles',
            'moi', 'toi', 'lui', 'eux',
            # Spanish
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'este', 'esta',
            'estos', 'estas', 'ese', 'esa', 'esos', 'esas', 'yo', 'tu', 'él', 'ella',
            'nosotros', 'vosotros', 'ellos', 'ellas', 'mi', 'mis', 'su', 'sus',
            # Italian
            'il', 'lo', 'la', 'gli', 'le', 'uno', 'una', 'questo', 'questa',
            'questi', 'queste', 'io', 'tu', 'lui', 'lei', 'noi', 'voi', 'loro',
            # Dutch
            'de', 'het', 'een', 'dit', 'dat', 'deze', 'die', 'ik', 'jij', 'hij',
            'zij', 'wij', 'jullie', 'ze', 'mij', 'jou',
        }
        
        # Process each language
        all_phrases = []
        
        for lang, lang_reviews in reviews_by_lang.items():
            if lang not in SPACY_MODELS:
                continue
            
            model_name = SPACY_MODELS[lang]
            
            # Only auto-install if explicitly requested (at brand level)
            if auto_install and not self._is_model_installed(model_name):
                self._install_model(model_name)
            
            nlp = self.load_model(model_name)
            
            if not nlp:
                continue
            
            # Extract noun phrases from reviews
            for review in lang_reviews:
                text = (review.get('title', '') + ' ' + review.get('text', '')).strip()
                if not text:
                    continue
                
                try:
                    doc = nlp(text[:1000])  # Limit to 1000 chars for speed
                    
                    # Extract noun chunks (better than single words)
                    for chunk in doc.noun_chunks:
                        # Clean and normalize
                        phrase = chunk.text.lower().strip()
                        
                        # Filter by word count (need at least 2 words for context)
                        word_count = len(phrase.split())
                        if word_count < 2 or word_count > 5:
                            continue
                        
                        # Skip if too short overall
                        if len(phrase) < 8:
                            continue
                        
                        # Skip if contains numbers
                        if any(c.isdigit() for c in phrase):
                            continue
                        
                        # Skip if starts with stop word
                        first_word = phrase.split()[0]
                        if first_word in stop_words:
                            continue
                        
                        # Skip common generic phrases
                        generic_phrases = {
                            'the company', 'this company', 'the product', 'this product',
                            'the service', 'this service', 'the app', 'this app',
                            'my account', 'my experience', 'the time', 'this time',
                        }
                        if phrase in generic_phrases:
                            continue
                        
                        all_phrases.append(phrase)
                
                except Exception as e:
                    # Skip problematic reviews
                    continue
        
        # Count frequency
        from collections import Counter
        phrase_counts = Counter(all_phrases)
        
        # Filter low-frequency phrases (must appear at least 2 times)
        filtered_phrases = {phrase: count for phrase, count in phrase_counts.items() if count >= 2}
        
        # Return top phrases
        return [phrase for phrase, count in Counter(filtered_phrases).most_common(max_themes)]


# Global instance
nlp_manager = NLPManager(min_coverage_pct=2.0)


if __name__ == "__main__":
    # Test with database
    from database import get_db_connection
    from psycopg2.extras import RealDictCursor
    
    print("\n[Testing NLP Manager]\n")
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM reviews 
                WHERE brand_id = 1 AND is_flagged = FALSE
                LIMIT 100
            """)
            reviews = [dict(row) for row in cur.fetchall()]
    
    # Test auto-detection and installation
    needed_models = nlp_manager.ensure_models_for_reviews(reviews)
    
    print(f"\n[Models ready for use]:")
    for lang, model in needed_models.items():
        print(f"  {lang}: {model}")
    
    # Test theme extraction
    if needed_models:
        print(f"\n[Testing theme extraction on negative reviews]...")
        negative_themes = nlp_manager.extract_themes(reviews, [1, 2], max_themes=5)
        print(f"Themes found: {negative_themes}")