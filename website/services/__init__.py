"""
Services Package
================

This package contains business logic services for the application.

Services:
- GeminiService: Google Gemini AI integration for coaching interface
"""

from .gemini_service import GeminiService

__all__ = ['GeminiService']
