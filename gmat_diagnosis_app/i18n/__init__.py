"""
Internationalization (i18n) module for GMAT Diagnosis App

This module provides multilingual support for Traditional Chinese and English.
It manages language selection and translation retrieval.
"""

import os
import json
from typing import Dict, Any, Optional

class I18nManager:
    """
    Manages internationalization for the GMAT diagnosis application.
    Supports Traditional Chinese (zh-TW) and English (en).
    """
    
    def __init__(self, default_language: str = 'zh-TW'):
        """
        Initialize the i18n manager.
        
        Args:
            default_language (str): Default language code ('zh-TW' or 'en')
        """
        self.current_language = default_language
        self.supported_languages = ['zh-TW', 'en']
        self.translations = {}
        self._load_translations()
    
    def _load_translations(self):
        """Load translation files for all supported languages."""
        translation_dir = os.path.join(os.path.dirname(__file__), 'translations')
        
        for lang in self.supported_languages:
            file_path = os.path.join(translation_dir, f'{lang}.py')
            if os.path.exists(file_path):
                try:
                    # Import the translation module dynamically
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(f"translations_{lang}", file_path)
                    translation_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(translation_module)
                    
                    # Get the TRANSLATIONS dictionary from the module
                    if hasattr(translation_module, 'TRANSLATIONS'):
                        self.translations[lang] = translation_module.TRANSLATIONS
                    else:
                        print(f"Warning: No TRANSLATIONS found in {file_path}")
                        self.translations[lang] = {}
                        
                except Exception as e:
                    print(f"Error loading translations for {lang}: {e}")
                    self.translations[lang] = {}
            else:
                print(f"Translation file not found: {file_path}")
                self.translations[lang] = {}
    
    def set_language(self, language: str):
        """
        Set the current language.
        
        Args:
            language (str): Language code ('zh-TW' or 'en')
        """
        if language in self.supported_languages:
            self.current_language = language
        else:
            print(f"Warning: Unsupported language '{language}'. Using default.")
    
    def get_language(self) -> str:
        """Get the current language code."""
        return self.current_language
    
    def translate(self, key: str, language: Optional[str] = None) -> str:
        """
        Get translation for a given key.
        
        Args:
            key (str): Translation key
            language (str, optional): Language code, uses current language if None
            
        Returns:
            str: Translated text, returns key if translation not found
        """
        lang = language or self.current_language
        
        if lang not in self.translations:
            return key
            
        return self.translations[lang].get(key, key)
    
    def get_available_languages(self) -> list:
        """Get list of available language codes."""
        return self.supported_languages.copy()


# Global i18n manager instance
_i18n_manager = I18nManager()

# Convenience functions for global access
def set_language(language: str):
    """Set the global language."""
    _i18n_manager.set_language(language)

def get_language() -> str:
    """Get the current global language."""
    return _i18n_manager.get_language()

def translate(key: str, language: Optional[str] = None) -> str:
    """Get translation for a key using the global manager."""
    return _i18n_manager.translate(key, language)

def get_available_languages() -> list:
    """Get available languages from the global manager."""
    return _i18n_manager.get_available_languages()

# Alias for shorter usage
t = translate 