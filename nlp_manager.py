#!/usr/bin/env python3
"""
NLP Manager - IMPROVED THEME EXTRACTION
- Better filtering of generic/useless phrases
- Shows positive themes even from 1 review
- Smarter translation handling
"""

import subprocess
import sys
import os
from pathlib import Path
import json
from dotenv import load_dotenv

load_dotenv()

# Load NLP configuration from environment
NLP_MIN_COVERAGE_PCT = float(os.getenv('NLP_MIN_COVERAGE_PCT', '2.0'))
NLP_MAX_THEMES = int(os.getenv('NLP_MAX_THEMES', '10'))
NLP_TEXT_LIMIT = int(os.getenv('NLP_TEXT_LIMIT', '1000'))
NLP_MIN_PHRASE_FREQ = int(os.getenv('NLP_MIN_PHRASE_FREQ', '2'))
NLP_MIN_PHRASE_WORDS = int(os.getenv('NLP_MIN_PHRASE_WORDS', '2'))
NLP_MAX_PHRASE_WORDS = int(os.getenv('NLP_MAX_PHRASE_WORDS', '5'))
ENABLE_TRANSLATION = os.getenv('ENABLE_TRANSLATION', 'true').lower() == 'true'

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

# Check if translator is available
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    if ENABLE_TRANSLATION:
        print("[INFO] Translation enabled but deep-translator not installed")
        print("      Run: pip install deep-translator")


class NLPManager:
    """Manages spaCy models - auto-installs on first use"""
    
    def __init__(self, min_coverage_pct=None):
        self.min_coverage_pct = min_coverage_pct if min_coverage_pct is not None else NLP_MIN_COVERAGE_PCT
        self.loaded_models = {}
        self.installed_models = self._load_cache()
    
    def _load_cache(self):
        if CACHE_FILE.exists():
            with open(CACHE_FILE, 'r') as f:
                return set(json.load(f))
        return set()
    
    def _save_cache(self):
        with open(CACHE_FILE, 'w') as f:
            json.dump(list(self.installed_models), f)
    
    def _is_model_installed(self, model_name):
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
    
    def _translate_to_english(self, text, source_lang):
        """Translate text to English using Google Translate"""
        if not ENABLE_TRANSLATION or not TRANSLATOR_AVAILABLE:
            return text
        
        if source_lang == 'en' or not text:
            return text
        
        try:
            translator = GoogleTranslator(source=source_lang, target='en')
            translated = translator.translate(text)
            return translated if translated else text
        except:
            return text
    
    def get_language_distribution(self, reviews):
        from collections import Counter
        langs = [r.get('language', 'unknown') for r in reviews if not r.get('is_flagged')]
        return Counter(langs)
    
    def ensure_models_for_reviews(self, reviews):
        if not reviews:
            return {}
        
        lang_dist = self.get_language_distribution(reviews)
        total_reviews = sum(lang_dist.values())
        
        needed_langs = {}
        for lang, count in lang_dist.items():
            percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
            
            if percentage >= self.min_coverage_pct and lang in SPACY_MODELS:
                model_name = SPACY_MODELS[lang]
                needed_langs[lang] = model_name
        
        if not needed_langs:
            print(f"  [ℹ] No languages meet {self.min_coverage_pct}% threshold for NLP processing")
            return {}
        
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
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]
        
        try:
            import spacy
            nlp = spacy.load(model_name)
            self.loaded_models[model_name] = nlp
            return nlp
        except Exception as e:
            return None
    
    def _is_generic_phrase(self, phrase, lang='en'):
        """Check if phrase is generic/useless across languages"""
        
        # Multi-language generic phrases to exclude
        generic_patterns = {
            # English
            'my account', 'my subscription', 'my money', 'my card', 'my credit card',
            'this app', 'this company', 'this service', 'this product', 'the app',
            'the company', 'the service', 'the product', 'customer service',
            'my lawyer', 'my experience', 'the time', 'the email', 'the support',
            'no answer', 'no stars', 'even a star', 'just hands',
            
            # German
            'mein konto', 'mein abonnement', 'mein geld', 'meine karte',
            'diese app', 'dieses unternehmen', 'dieser service', 'die app',
            'mein anwalt', 'keine sterne', 'kein stern', 'keine antwort',
            
            # French
            'mon compte', 'mon abonnement', 'mon argent', 'ma carte',
            'cette application', 'cette entreprise', 'ce service',
            'mon avocat', 'pas de réponse',
            
            # Spanish
            'mi cuenta', 'mi suscripción', 'mi dinero', 'mi tarjeta',
            'esta aplicación', 'esta empresa', 'este servicio',
            
            # Common across languages
            'attention', 'beware', 'twice', 'actung',
        }
        
        phrase_lower = phrase.lower().strip()
        
        # Check exact matches
        if phrase_lower in generic_patterns:
            return True
        
        # Check if contains only generic words (>50% of words are generic)
        words = phrase_lower.split()
        generic_word_count = sum(1 for word in words if word in generic_patterns)
        if len(words) > 0 and generic_word_count / len(words) > 0.5:
            return True
        
        return False
    
    def extract_themes(self, reviews, rating_filter, max_themes=None, auto_install=False):
        """
        Extract themes from reviews using NLP, auto-translated to English
        
        IMPROVED:
        - Better generic phrase filtering
        - Lower threshold for positive reviews (show even 1 review themes)
        - Cleaner language tags
        """
        if max_themes is None:
            max_themes = NLP_MAX_THEMES
        
        # Check if this is positive sentiment extraction
        is_positive = any(r >= 4 for r in rating_filter)
        
        # Group reviews by language
        reviews_by_lang = {}
        for r in reviews:
            if r.get('rating') in rating_filter:
                lang = r.get('language', 'unknown')
                if lang not in reviews_by_lang:
                    reviews_by_lang[lang] = []
                reviews_by_lang[lang].append(r)
        
        if not reviews_by_lang:
            return []
        
        # For positive reviews with very few samples, use lower frequency threshold
        total_positive_reviews = sum(len(revs) for revs in reviews_by_lang.values())
        min_freq = 1 if (is_positive and total_positive_reviews < 5) else NLP_MIN_PHRASE_FREQ
        
        # Multi-language stop words
        stop_words = {
            'this', 'that', 'they', 'them', 'their', 'these', 'those', 'what', 'which',
            'who', 'whom', 'whose', 'when', 'where', 'why', 'how', 'there', 'here',
            'your', 'yours', 'mine', 'ours', 'theirs', 'very', 'really', 'just',
            'sich', 'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einer',
            'eines', 'einem', 'einen', 'ich', 'mich', 'mir', 'du', 'dich', 'dir',
            'sie', 'ihm', 'ihn', 'wir', 'uns', 'ihr', 'euch', 'ihnen',
            'le', 'la', 'les', 'un', 'une', 'des', 'ce', 'cet', 'cette', 'ces',
            'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles',
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'este', 'esta',
            'il', 'lo', 'la', 'gli', 'le', 'uno', 'una', 'questo', 'questa',
            'de', 'het', 'een', 'dit', 'dat', 'deze', 'die', 'ik', 'jij', 'hij',
        }
        
        # Extract phrases by language
        all_phrases_with_lang = []
        
        for lang, lang_reviews in reviews_by_lang.items():
            if lang not in SPACY_MODELS:
                continue
            
            model_name = SPACY_MODELS[lang]
            
            if auto_install and not self._is_model_installed(model_name):
                self._install_model(model_name)
            
            nlp = self.load_model(model_name)
            if not nlp:
                continue
            
            # Extract phrases for this language
            phrases = []
            for review in lang_reviews:
                text = (review.get('title', '') + ' ' + review.get('text', '')).strip()
                if not text:
                    continue
                
                try:
                    doc = nlp(text[:NLP_TEXT_LIMIT])
                    
                    for chunk in doc.noun_chunks:
                        phrase = chunk.text.lower().strip()
                        word_count = len(phrase.split())
                        
                        if word_count < NLP_MIN_PHRASE_WORDS or word_count > NLP_MAX_PHRASE_WORDS:
                            continue
                        if len(phrase) < 8:
                            continue
                        if any(c.isdigit() for c in phrase):
                            continue
                        if phrase.split()[0] in stop_words:
                            continue
                        
                        # NEW: Filter generic phrases
                        if self._is_generic_phrase(phrase, lang):
                            continue
                        
                        phrases.append(phrase)
                except:
                    continue
            
            # Count frequency and filter
            from collections import Counter
            phrase_counts = Counter(phrases)
            
            # Use lower threshold for positive with few reviews
            for phrase, count in phrase_counts.items():
                if count >= min_freq:
                    all_phrases_with_lang.append((phrase, lang, count))
        
        if not all_phrases_with_lang:
            return []
        
        # Translate to English and deduplicate
        translated_phrases = {}
        
        for phrase, lang, count in all_phrases_with_lang:
            if lang == 'en':
                # English - no translation needed
                key = phrase
                display = phrase
            else:
                # Translate
                translated = self._translate_to_english(phrase, lang)
                
                # Check if translation actually changed it
                if ENABLE_TRANSLATION and TRANSLATOR_AVAILABLE and translated.lower() != phrase.lower():
                    key = translated.lower()
                    display = f"{translated} ({lang})"
                else:
                    # Translation didn't work or not enabled
                    key = phrase
                    display = f"{phrase} ({lang})"
            
            # Aggregate counts for same translated phrase
            if key not in translated_phrases:
                translated_phrases[key] = {'display': display, 'count': 0}
            translated_phrases[key]['count'] += count
        
        # Sort by frequency and return top N
        sorted_phrases = sorted(
            translated_phrases.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        return [item[1]['display'] for item in sorted_phrases[:max_themes]]


# Global instance
nlp_manager = NLPManager()


if __name__ == "__main__":
    print("\n[NLP Manager Configuration]")
    print(f"  Min coverage: {NLP_MIN_COVERAGE_PCT}%")
    print(f"  Max themes: {NLP_MAX_THEMES}")
    print(f"  Translation: {'Enabled' if ENABLE_TRANSLATION else 'Disabled'}")
    print(f"  Translator: {'Available' if TRANSLATOR_AVAILABLE else 'Not installed'}")