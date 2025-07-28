"""i18n utilities for DSPy Variables using Python's gettext module."""

import gettext
import os
from pathlib import Path
from typing import Optional

# Cache for loaded translation catalogs
_translation_cache = {}
_current_locale = None

def get_locales_dir() -> Path:
    """Get the path to the locales directory."""
    return Path(__file__).parent / "locales"

def get_translation(locale: str) -> gettext.GNUTranslations:
    """Get a translation catalog for the given locale.
    
    Args:
        locale: The locale code (e.g., "zh_CN", "es", "fr")
        
    Returns:
        A GNUTranslations object, or NullTranslations if not found
    """
    if locale in _translation_cache:
        return _translation_cache[locale]
    
    locales_dir = get_locales_dir()
    
    try:
        # Try to load the translation catalog
        translation = gettext.translation(
            'messages',  # domain
            localedir=str(locales_dir),  # Convert Path to string
            languages=[locale],
            fallback=False  # Don't fall back initially, so we can check if it worked
        )
        _translation_cache[locale] = translation
        return translation
    except Exception as e:
        # If loading fails, try with fallback
        try:
            translation = gettext.translation(
                'messages',
                localedir=str(locales_dir),
                languages=[locale], 
                fallback=True
            )
            _translation_cache[locale] = translation
            return translation
        except Exception:
            # Return null translation (no-op) if all fails
            translation = gettext.NullTranslations()
            _translation_cache[locale] = translation
            return translation

def translate(message: str, locale: Optional[str] = None) -> str:
    """Translate a message to the given locale.
    
    Args:
        message: The message to translate
        locale: The locale to translate to. If None, uses current dspy locale.
        
    Returns:
        The translated message, or the original message if translation not found
    """
    if locale is None:
        # Try to get locale from dspy settings
        try:
            from dspy.dsp.utils.settings import settings
            locale = getattr(settings, 'locale', None)
        except (ImportError, AttributeError):
            locale = None
    
    if locale is None:
        return message
    
    translation = get_translation(locale)
    return translation.gettext(message)

def set_locale(locale: str) -> None:
    """Set the current locale for translations.
    
    Args:
        locale: The locale code to set as current
    """
    global _current_locale
    _current_locale = locale

def get_current_locale() -> Optional[str]:
    """Get the current locale."""
    return _current_locale

def clear_translation_cache() -> None:
    """Clear the translation cache (mainly for testing)."""
    global _translation_cache
    _translation_cache = {}

# Convenience function for marking translatable strings
def _(message: str) -> str:
    """Mark a string as translatable and translate it to current locale.
    
    This is the standard gettext convention for marking translatable strings.
    
    Args:
        message: The message to translate
        
    Returns:
        The translated message
    """
    return translate(message)