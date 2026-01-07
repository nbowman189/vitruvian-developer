"""
Gemini Service
==============

Google Gemini AI integration service for AI coaching interface.
Handles conversation management, function calling, and persona loading.

Migrated to google.genai SDK (January 2026)
"""

import os
import re
import logging
from typing import List, Dict, Tuple, Optional, Any
from google import genai
from google.genai import types

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

CRITICAL INSTRUCTIONS FOR FUNCTION CALLING:
- When user mentions data to log (workouts, meals, weight, etc.), CALL the appropriate function immediately
- DO NOT describe the function call in JSON format in your response
- DO NOT say "I'll log this" or "Here's what I'll create" - just CALL THE FUNCTION
- The function call happens automatically through your function calling capability
- After calling a function, give a brief acknowledgment and continue your coaching
- **CRITICAL**: When user mentions MULTIPLE items to log (e.g., "I weighed 176lbs, did a workout, and ate breakfast"), you MUST call MULTIPLE functions simultaneously - one for each item (create_health_metric, create_workout, create_meal_log)
- You CAN and SHOULD call multiple functions in a single response when the user provides multiple pieces of data
- Example: If user says "I weighed 180lbs and did 30min cardio", call BOTH create_health_metric AND create_workout

When discussing progress or giving advice, USE THE READ FUNCTIONS to access actual user data. This enables you to provide personalized, data-driven coaching instead of generic advice. For WRITE functions, CALL THEM directly - the user will review and approve the record before it's saved."""


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
        # Debug logging
        logger.info(f"GeminiService.__init__ called with api_key parameter: {bool(api_key)}")
        env_key = os.environ.get('GEMINI_API_KEY')
        logger.info(f"GEMINI_API_KEY from environment: {bool(env_key)}")

        self.api_key = api_key or env_key

        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in parameters or environment")
            logger.error(f"Environment keys available: {', '.join([k for k in os.environ.keys() if 'GEMINI' in k or 'API' in k])}")
            raise ValueError(
                "GEMINI_API_KEY not found. Please set it in your environment or pass it to GeminiService."
            )

        # Initialize the Gemini client
        self.client = genai.Client(api_key=self.api_key)

        # Load model fallback chain from config
        try:
            from flask import current_app
            self.model_names = current_app.config.get('GEMINI_MODEL_FALLBACK_CHAIN', [
                'gemini-1.5-flash',  # Use 1.5-flash first - better function calling support
                'gemini-1.5-flash-8b',
                'gemini-2.0-flash-exp',
                'gemini-2.5-flash'  # 2.5 has code execution which interferes with function calling
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
                'gemini-1.5-flash',  # Use 1.5-flash first - better function calling support
                'gemini-1.5-flash-8b',
                'gemini-2.0-flash-exp',
                'gemini-2.5-flash'  # 2.5 has code execution which interferes with function calling
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
        history = self._build_history(recent_history)

        # Try each model in fallback chain
        for model_name in self.model_names:
            # Check quota if manager is available
            if self.quota_manager and not self.quota_manager.is_quota_available(model_name):
                logger.info(f"Skipping {model_name} - quota exhausted")
                continue

            try:
                logger.info(f"Attempting with {model_name}")

                # Build generation config
                config = types.GenerateContentConfig(
                    system_instruction=self._get_contextualized_system_instruction(),
                    temperature=self.generation_config.get('temperature', 0.7),
                    top_p=self.generation_config.get('top_p', 0.95),
                    top_k=self.generation_config.get('top_k', 40),
                    max_output_tokens=self.generation_config.get('max_output_tokens', 2048),
                    safety_settings=self._get_safety_settings(),
                    # CRITICAL: Disable automatic function calling to preserve manual handling
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    )
                )

                # Add function declarations and tool config if provided
                if function_declarations:
                    # Wrap function declarations in Tool object
                    config.tools = [types.Tool(function_declarations=function_declarations)]
                    config.tool_config = types.ToolConfig(
                        function_calling_config=types.FunctionCallingConfig(mode='AUTO')
                    )

                # Create chat with history
                chat = self.client.chats.create(
                    model=model_name,
                    config=config,
                    history=history
                )

                # Send message
                response = chat.send_message(message=user_message)

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

    def _get_safety_settings(self) -> List[types.SafetySetting]:
        """Get safety settings as list of SafetySetting objects."""
        return [
            types.SafetySetting(
                category='HARM_CATEGORY_HARASSMENT',
                threshold='BLOCK_MEDIUM_AND_ABOVE'
            ),
            types.SafetySetting(
                category='HARM_CATEGORY_HATE_SPEECH',
                threshold='BLOCK_MEDIUM_AND_ABOVE'
            ),
            types.SafetySetting(
                category='HARM_CATEGORY_SEXUALLY_EXPLICIT',
                threshold='BLOCK_MEDIUM_AND_ABOVE'
            ),
            types.SafetySetting(
                category='HARM_CATEGORY_DANGEROUS_CONTENT',
                threshold='BLOCK_MEDIUM_AND_ABOVE'
            )
        ]

    def _get_contextualized_system_instruction(self) -> str:
        """
        Get system instruction with current date context.

        Returns:
            System instruction string with current date
        """
        from datetime import datetime

        current_date = datetime.now().strftime('%Y-%m-%d')
        day_of_week = datetime.now().strftime('%A')

        return f"""CURRENT DATE: {current_date} ({day_of_week})

{self.system_prompt}

IMPORTANT: When users say "today", use the date {current_date}. When creating records, ALWAYS include the appropriate date field (recorded_date, meal_date, session_date, etc.) with the correct date value in YYYY-MM-DD format."""

    def _build_history(self, history: List[Dict]) -> List[types.Content]:
        """
        Build chat history as list of Content objects.

        Args:
            history: List of message dicts with 'role' and 'content' keys

        Returns:
            List of types.Content objects for chat history
        """
        contents = []

        for msg in history:
            role = 'model' if msg['role'] == 'assistant' else 'user'
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(msg['content'])]
                )
            )

        return contents

    def _extract_response(self, response) -> Tuple[str, Optional[Dict]]:
        """Extract text and function call(s) from API response.

        Handles both single and multiple function calls from Gemini.
        Returns multiple calls as a list in the 'function_call' dict under 'function_calls' key.
        """
        # Use convenience properties for text and function calls
        assistant_response = response.text if hasattr(response, 'text') and response.text else ""

        function_calls = []
        if hasattr(response, 'function_calls') and response.function_calls:
            for fc in response.function_calls:
                function_calls.append({
                    'name': fc.name,
                    'args': dict(fc.args) if fc.args else {}
                })
                logger.info(f"Function call detected: {fc.name}")

        # Handle function calls
        function_call = None
        if function_calls:
            if len(function_calls) == 1:
                # Single function call - return as before for backwards compatibility
                function_call = function_calls[0]
            else:
                # Multiple function calls - wrap in special structure
                function_call = {
                    'name': 'multiple_function_calls',
                    'function_calls': function_calls
                }
                logger.info(f"Multiple function calls detected: {len(function_calls)}")

        # Provide default message if no text but function call present
        if not assistant_response and function_call:
            if function_call['name'] == 'multiple_function_calls':
                count = len(function_call['function_calls'])
                assistant_response = f"Great! I've prepared {count} records for you to review and save."
            else:
                assistant_response = self._get_default_function_call_message(function_call['name'])

        logger.info(f"Gemini response received. Function calls: {len(function_calls)}")
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
            client = genai.Client(api_key=api_key)
            # Make a simple test call using first model from default chain
            client.models.generate_content(
                model='gemini-2.5-flash',
                contents='Test'
            )
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False

    @property
    def is_configured(self) -> bool:
        """Check if service is properly configured."""
        return bool(self.api_key)
