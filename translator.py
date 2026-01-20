#!/usr/bin/env python3
"""
Simple translator for theme keywords using Google Translate (free)
Falls back to original text if translation fails
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Translation enabled by default, can disable via env
ENABLE_TRANSLATION = os.getenv('ENABLE_TRANSLATION', 'true').lower() == 'true'

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    print("[WARNING] deep-translator not installed. Run: pip install deep-translator")


def translate_to_english(text, source_lang='auto'):
    """
    Translate text to English
    
    Args:
        text: Text to translate
        source_lang: Source language code (default: auto-detect)
    
    Returns:
        Translated text (or original if translation fails)
    """
    if not ENABLE_TRANSLATION:
        return text
    
    if not TRANSLATOR_AVAILABLE:
        return text
    
    if not text or text.strip() == '':
        return text
    
    # Already English? Skip
    if source_lang == 'en':
        return text
    
    try:
        translator = GoogleTranslator(source=source_lang, target='en')
        translated = translator.translate(text)
        return translated if translated else text
    except Exception as e:
        # Silently fail and return original
        return text


def translate_themes_dict(themes_by_language):
    """
    Translate themes from multiple languages to English
    
    Args:
        themes_by_language: Dict like {'de': ['gute qualität', 'schnelle lieferung'], 'fr': [...]}
    
    Returns:
        List of translated English themes with language tags
    """
    if not ENABLE_TRANSLATION or not TRANSLATOR_AVAILABLE:
        # Return all themes as-is without translation
        all_themes = []
        for lang, themes in themes_by_language.items():
            all_themes.extend(themes)
        return all_themes
    
    translated_themes = []
    
    for lang, themes in themes_by_language.items():
        if lang == 'en':
            # Already English
            translated_themes.extend(themes)
        else:
            # Translate each theme
            for theme in themes:
                translated = translate_to_english(theme, source_lang=lang)
                # Add language tag if different from original
                if translated.lower() != theme.lower():
                    translated_themes.append(f"{translated} ({lang})")
                else:
                    translated_themes.append(theme)
    
    return translated_themes


def get_translator_status():
    """Get status message about translator"""
    if not ENABLE_TRANSLATION:
        return "Translation disabled (set ENABLE_TRANSLATION=true to enable)"
    
    if TRANSLATOR_AVAILABLE:
        return "Translation enabled (Google Translate)"
    else:
        return "Translation unavailable (install: pip install deep-translator)"


if __name__ == "__main__":
    # Test
    print(f"\n[Translator Status]")
    print(f"  {get_translator_status()}\n")
    
    if TRANSLATOR_AVAILABLE and ENABLE_TRANSLATION:
        # Test translations
        test_phrases = {
            'de': 'schnelle lieferung',
            'fr': 'excellent service',
            'es': 'muy buena calidad',
        }
        
        print("[Test Translations]")
        for lang, phrase in test_phrases.items():
            translated = translate_to_english(phrase, lang)
            print(f"  {lang}: '{phrase}' → '{translated}'")