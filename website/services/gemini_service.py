"""
Gemini Service
==============

Google Gemini AI integration service for AI coaching interface.
Handles conversation management, function calling, and persona loading.
"""

import os
import re
import logging
from typing import List, Dict, Tuple, Optional, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)

# Import quota manager at module level
try:
    from .quota_manager import quota_manager
except ImportError:
    # If import fails, create a dummy manager for graceful degradation
    logger.warning("Failed to import quota_manager, quota tracking disabled")
    quota_manager = None


# Custom Exceptions
class QuotaExhaustedError(Exception):
    """
    Raised when all model quotas are exhausted.

    Attributes:
        message: Error message
        seconds_until_reset: Seconds until next quota reset (None if unknown)
    """

    def __init__(self, message: str, seconds_until_reset: Optional[int] = None):
        super().__init__(message)
        self.seconds_until_reset = seconds_until_reset


# The Transformative Trainer Persona
TRANSFORMATIVE_TRAINER_PERSONA = """You are an expert personal trainer with 20 years of experience, specializing in guiding clients from morbid obesity to a state of health, fitness, and strength. Your expertise lies in a holistic approach, focusing on sustainable nutrition, practical meal planning, effective bodyweight strength training, and functional fitness. Your communication style is that of a tough love drill sergeant, pushing clients to achieve their best, but you are also deeply encouraging and empathetic when they face struggles. You operate on the core principles that sustainable lifestyle changes, a strong mindset, and unwavering consistency are paramount, far outweighing short bursts of intensity. Your primary target audience is individuals seeking a holistic approach to health who have struggled with long-term weight loss.

As an AI coach, you have access to function tools to both READ and WRITE data:

**READ Functions** (query user data - executed automatically):
1. **get_recent_health_metrics**: Query weight, body fat, measurements trends
2. **get_workout_history**: Review recent workout sessions and performance
3. **get_nutrition_summary**: Analyze meal logs and macro adherence
4. **get_user_goals**: Check active goals and progress
5. **get_coaching_history**: Reference previous coaching sessions
6. **get_progress_summary**: Get comprehensive overview across all data

**WRITE Functions** (suggest records for user approval):
1. **create_health_metric**: For weight, body fat, measurements tracking
2. **create_meal_log**: For meal and nutrition tracking
3. **create_workout**: For workout sessions with exercises
4. **create_coaching_session**: For coaching notes and feedback

When discussing progress or giving advice, USE THE READ FUNCTIONS to access actual user data. This enables you to provide personalized, data-driven coaching instead of generic advice. For WRITE functions, suggest records conversationally and the user will review before saving."""


class GeminiService:
    """
    Google Gemini AI service for conversational health coaching.

    Handles:
    - Persona-based AI conversations
    - Function calling for database record suggestions
    - Context management and pruning
    - Error handling and safety settings
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini service with model fallback chain.

        Args:
            api_key: Google Gemini API key (defaults to GEMINI_API_KEY env var)

        Raises:
            ValueError: If API key is not provided or found in environment
        """
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Please set it in your environment or pass it to GeminiService."
            )

        # Configure the Gemini API
        genai.configure(api_key=self.api_key)

        # Load model fallback chain from config
        try:
            from flask import current_app
            self.model_names = current_app.config.get('GEMINI_MODEL_FALLBACK_CHAIN', [
                'gemini-2.0-flash-exp',
                'gemini-1.5-flash',
                'gemini-1.5-flash-8b'
            ])

            self.generation_config = current_app.config.get('GEMINI_GENERATION_CONFIG', {
                'temperature': 0.7,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 2048,
            })
        except RuntimeError:
            # Working outside Flask application context (testing)
            self.model_names = [
                'gemini-2.0-flash-exp',
                'gemini-1.5-flash',
                'gemini-1.5-flash-8b'
            ]
            self.generation_config = {
                'temperature': 0.7,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 2048,
            }

        # Set quota manager (may be None if import failed)
        self.quota_manager = quota_manager
        if not self.quota_manager:
            logger.warning("Quota manager not available, fallback system disabled")

        self.system_prompt = TRANSFORMATIVE_TRAINER_PERSONA

        logger.info(f"GeminiService initialized with {len(self.model_names)} fallback models")

    def chat(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        function_declarations: Optional[List[Dict]] = None,
        max_context_messages: int = 10
    ) -> Tuple[str, Optional[Dict]]:
        """
        Send message with automatic model fallback on quota errors.

        Tries models in priority order. If quota exhausted, marks model
        and retries with next model. Raises QuotaExhaustedError if all fail.

        Args:
            user_message: The user's message
            conversation_history: List of previous messages with 'role' and 'content' keys
            function_declarations: List of function schemas for function calling
            max_context_messages: Maximum number of previous messages to include (default: 10)

        Returns:
            Tuple of (assistant_response, function_call_data)
            - assistant_response: The AI's text response
            - function_call_data: Dict with function call details if AI wants to call a function, else None

        Raises:
            QuotaExhaustedError: If all model quotas are exhausted
            Exception: If Gemini API call fails with non-quota error
        """
        # Build conversation context
        recent_history = conversation_history[-max_context_messages:] if conversation_history else []
        messages = self._build_messages(recent_history, user_message)
        tools = [{'function_declarations': function_declarations}] if function_declarations else None

        # Try each model in fallback chain
        for model_name in self.model_names:
            # Check quota if manager is available
            if self.quota_manager and not self.quota_manager.is_quota_available(model_name):
                logger.info(f"Skipping {model_name} - quota exhausted")
                continue

            try:
                logger.info(f"Attempting with {model_name}")

                # Create model instance
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=self.generation_config,
                    safety_settings=self._get_safety_settings()
                )

                # Start chat and send message
                chat = model.start_chat(history=messages[:-1])

                if tools:
                    response = chat.send_message(user_message, tools=tools)
                else:
                    response = chat.send_message(user_message)

                # Extract response
                assistant_response, function_call = self._extract_response(response)

                logger.info(f"Success with {model_name}")
                return assistant_response, function_call

            except Exception as e:
                # Check if quota error
                if self._is_quota_error(e):
                    retry_delay = self._extract_retry_delay(e)
                    logger.warning(f"{model_name} quota exhausted, retry in {retry_delay}s")

                    # Mark quota exhausted if manager available
                    if self.quota_manager:
                        self.quota_manager.mark_quota_exhausted(model_name, retry_delay)

                    continue  # Try next model

                # Non-quota error - propagate
                logger.error(f"Non-quota error with {model_name}: {e}", exc_info=True)
                raise

        # All models exhausted
        seconds_until_reset = self.quota_manager.get_seconds_until_reset() if self.quota_manager else None
        raise QuotaExhaustedError(
            "All AI models have reached their quota limits.",
            seconds_until_reset=seconds_until_reset
        )

    def _get_default_function_call_message(self, function_name: str) -> str:
        """
        Get a default message when a function call is made without accompanying text.

        Args:
            function_name: Name of the function being called

        Returns:
            Default message string
        """
        messages = {
            'create_health_metric': "Great! I've prepared a health metric record for you. Review and save it when you're ready.",
            'create_meal_log': "Excellent! I've created a meal log entry. Please review the details and save it.",
            'create_workout': "Nice work! I've logged your workout session. Check the details and save it to your history.",
            'create_coaching_session': "I've captured our coaching discussion. Review the notes and save them for your records."
        }
        return messages.get(function_name, "I've prepared a record for you to review and save.")

    def _build_conversation_context(
        self,
        conversation_history: List[Dict[str, str]],
        max_messages: int
    ) -> str:
        """
        Build conversation context string from history.

        Args:
            conversation_history: List of messages
            max_messages: Maximum number of messages to include

        Returns:
            Formatted conversation context string
        """
        recent_history = conversation_history[-max_messages:] if conversation_history else []

        context_lines = []
        for msg in recent_history:
            role_label = "User" if msg['role'] == 'user' else "Coach"
            context_lines.append(f"{role_label}: {msg['content']}")

        return "\n".join(context_lines)

    def _is_quota_error(self, exception: Exception) -> bool:
        """Check if exception is a quota/rate limit error."""
        error_str = str(exception).lower()
        error_type = type(exception).__name__.lower()
        return ('429' in error_str or 'quota' in error_str or
                'resourceexhausted' in error_type or 'rate' in error_str)

    def _extract_retry_delay(self, exception: Exception) -> int:
        """
        Extract retry_delay from quota error.

        Returns:
            Retry delay in seconds (default 3600 = 1 hour if not found)
        """
        error_str = str(exception)

        # Look for "retry_delay { seconds: 51 }" pattern
        match = re.search(r'retry_delay.*?seconds[:\s]+(\d+)', error_str)
        if match:
            return int(match.group(1))

        # Default to 1 hour if not specified
        logger.warning("Could not parse retry_delay, defaulting to 3600s")
        return 3600

    def _get_safety_settings(self) -> dict:
        """Get safety settings."""
        return {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

    def _build_messages(self, history: List[Dict], user_message: str) -> List[Dict]:
        """Build message list with system prompt."""
        messages = [
            {'role': 'user', 'parts': [self.system_prompt]},
            {'role': 'model', 'parts': ["I understand. I am The Transformative Trainer, ready to help you on your health and fitness journey with tough love, empathy, and structured tracking tools. Let's get started!"]}
        ]

        for msg in history:
            role = 'model' if msg['role'] == 'assistant' else 'user'
            messages.append({'role': role, 'parts': [msg['content']]})

        messages.append({'role': 'user', 'parts': [user_message]})
        return messages

    def _extract_response(self, response) -> Tuple[str, Optional[Dict]]:
        """Extract text and function call from API response."""
        assistant_response = ""
        function_call = None

        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        assistant_response += part.text
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        function_call = {'name': fc.name, 'args': dict(fc.args) if fc.args else {}}
                        logger.info(f"Function call detected: {fc.name}")

        if not assistant_response and function_call:
            assistant_response = self._get_default_function_call_message(function_call['name'])

        logger.info(f"Gemini response received. Function call: {function_call is not None}")
        return assistant_response, function_call

    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """
        Validate Gemini API key by making a test call.

        Args:
            api_key: API key to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            genai.configure(api_key=api_key)
            # Use first model from default fallback chain
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            model.generate_content("Test")
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False

    @property
    def is_configured(self) -> bool:
        """Check if service is properly configured."""
        return bool(self.api_key)
