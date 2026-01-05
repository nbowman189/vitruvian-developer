"""
Services Package
================

This package contains business logic services for the application.

Services:
- GeminiService: Google Gemini AI integration for coaching interface
- QuotaExhaustedError: Exception raised when all AI model quotas exhausted
- quota_manager: Singleton instance for tracking quota state
"""

from .gemini_service import GeminiService, QuotaExhaustedError
from .quota_manager import quota_manager

__all__ = ['GeminiService', 'QuotaExhaustedError', 'quota_manager']
