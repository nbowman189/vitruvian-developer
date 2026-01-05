"""
Quota Manager
=============

Tracks quota exhaustion state for Gemini AI models.

Provides in-memory tracking of model quota exhaustion with automatic
expiration based on retry_delay from API errors. Thread-safe for use
in Flask's multi-threaded environment.
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class QuotaManager:
    """
    Tracks quota exhaustion state for Gemini models.

    When a model quota is exhausted, stores the reset time based on
    retry_delay from API error. Automatically expires when time passes.

    Thread-safe for use in Flask (multi-threaded environment).

    Example:
        >>> manager = QuotaManager()
        >>> manager.mark_quota_exhausted('gemini-2.0-flash-exp', 3600)
        >>> manager.is_quota_available('gemini-2.0-flash-exp')
        False
        >>> manager.get_seconds_until_reset()
        3599
    """

    def __init__(self):
        """Initialize quota manager with empty state."""
        self._quota_state: Dict[str, datetime] = {}  # model_name -> reset_time
        self._lock = threading.Lock()
        logger.info("QuotaManager initialized")

    def mark_quota_exhausted(self, model_name: str, retry_delay_seconds: int):
        """
        Mark model quota as exhausted until reset_time.

        Args:
            model_name: Name of the Gemini model (e.g., 'gemini-2.0-flash-exp')
            retry_delay_seconds: Seconds until quota resets (from API error)
        """
        reset_time = datetime.utcnow() + timedelta(seconds=retry_delay_seconds)

        with self._lock:
            self._quota_state[model_name] = reset_time

        logger.warning(
            f"Model '{model_name}' quota exhausted. "
            f"Reset at {reset_time.isoformat()} (in {retry_delay_seconds}s)"
        )

    def is_quota_available(self, model_name: str) -> bool:
        """
        Check if model quota is available (not exhausted or past reset time).

        Args:
            model_name: Name of the Gemini model

        Returns:
            True if quota is available, False if exhausted
        """
        with self._lock:
            if model_name not in self._quota_state:
                return True

            reset_time = self._quota_state[model_name]

            # Check if quota has reset (past reset time)
            if datetime.utcnow() >= reset_time:
                # Quota has reset, remove from state
                del self._quota_state[model_name]
                logger.info(f"Model '{model_name}' quota has reset and is now available")
                return True

            return False

    def get_next_reset_time(self) -> Optional[datetime]:
        """
        Get earliest quota reset time across all models.

        Returns:
            Datetime of next reset, or None if no quotas exhausted
        """
        with self._lock:
            if not self._quota_state:
                return None
            return min(self._quota_state.values())

    def get_seconds_until_reset(self) -> Optional[int]:
        """
        Get seconds until next quota reset.

        Returns:
            Seconds until reset, or None if no quotas exhausted
        """
        reset_time = self.get_next_reset_time()
        if not reset_time:
            return None

        delta = reset_time - datetime.utcnow()
        seconds = int(delta.total_seconds())

        return max(0, seconds)  # Never return negative

    def get_status(self) -> Dict[str, Dict[str, any]]:
        """
        Get current quota status for all tracked models.

        Returns:
            Dictionary mapping model names to status info:
            {
                'gemini-2.0-flash-exp': {
                    'exhausted': True,
                    'reset_time': '2026-01-05T12:30:00Z',
                    'seconds_until_reset': 3599
                },
                ...
            }
        """
        with self._lock:
            status = {}

            for model_name, reset_time in self._quota_state.items():
                delta = reset_time - datetime.utcnow()
                seconds = max(0, int(delta.total_seconds()))

                status[model_name] = {
                    'exhausted': True,
                    'reset_time': reset_time.isoformat() + 'Z',
                    'seconds_until_reset': seconds
                }

            return status

    def clear_all(self):
        """Clear all quota state (useful for testing)."""
        with self._lock:
            self._quota_state.clear()
            logger.info("All quota state cleared")


# Global singleton instance
quota_manager = QuotaManager()
